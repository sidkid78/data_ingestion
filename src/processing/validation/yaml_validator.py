from typing import Any, Dict, List, Optional, Union
import yaml
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaError
import re

from ...utils.logging import LoggerMixin
from ...utils.error_handling import ValidationError


class YAMLValidator(LoggerMixin):
    """
    Validates YAML document structure and content.
    Ensures documents conform to the required schema.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YAML validator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.schema = self._load_document_schema()

    def _load_document_schema(self) -> Dict[str, Any]:
        """
        Load and return the document validation schema.
        
        Returns:
            Dict[str, Any]: JSON Schema for document validation
        """
        return {
            "type": "object",
            "required": [
                "document_id",
                "source",
                "title",
                "document_type",
                "publication_date",
                "metadata"
            ],
            "properties": {
                "document_id": {
                    "type": "string",
                    "minLength": 1
                },
                "source": {
                    "type": "string",
                    "enum": [
                        "federal_register",
                        "far_dfars",
                        "iso",
                        "ansi",
                        "nist"
                    ]
                },
                "title": {
                    "type": "string",
                    "minLength": 1
                },
                "document_type": {
                    "type": "string",
                    "enum": [
                        "rule",
                        "proposed_rule",
                        "notice",
                        "presidential_document",
                        "standard",
                        "guidance",
                        "policy"
                    ]
                },
                "publication_date": {
                    "type": "string",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                },
                "metadata": {
                    "type": "object",
                    "required": ["html_url"],
                    "properties": {
                        "html_url": {
                            "type": "string",
                            "format": "uri"
                        },
                        "pdf_url": {
                            "type": "string",
                            "format": "uri"
                        },
                        "abstract": {
                            "type": "string"
                        },
                        "agencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    },
                                    "id": {
                                        "type": "string"
                                    }
                                }
                            }
                        },
                        "regulation_id_numbers": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "dates": {
                            "type": "object"
                        },
                        "nlp_enrichment": {
                            "type": "object",
                            "properties": {
                                "entities": {
                                    "type": "object"
                                },
                                "keywords": {
                                    "type": "array"
                                },
                                "dates": {
                                    "type": "array"
                                },
                                "citations": {
                                    "type": "array"
                                },
                                "processed_at": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
            }
        }

    async def validate_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a document against the schema.
        
        Args:
            document: Document to validate
            
        Returns:
            Dict[str, Any]: Validated document
            
        Raises:
            ValidationError: If document fails validation
        """
        try:
            # Validate against JSON Schema
            validate(instance=document, schema=self.schema)
            
            # Additional custom validations
            await self._validate_dates(document)
            await self._validate_urls(document)
            await self._validate_relationships(document)
            
            return document
            
        except JsonSchemaError as e:
            raise ValidationError(f"Schema validation failed: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Document validation failed: {str(e)}")

    async def validate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate multiple documents.
        
        Args:
            documents: List of documents to validate
            
        Returns:
            List[Dict[str, Any]]: List of validated documents
            
        Raises:
            ValidationError: If any document fails validation
        """
        validated_documents = []
        errors = []

        for doc in documents:
            try:
                validated_doc = await self.validate_document(doc)
                validated_documents.append(validated_doc)
            except ValidationError as e:
                errors.append({
                    "document_id": doc.get("document_id", "unknown"),
                    "error": str(e)
                })
                self.logger.error(f"Validation failed for document {doc.get('document_id', 'unknown')}: {str(e)}")

        if errors:
            self.logger.warning(f"Validation completed with {len(errors)} errors")
        
        return validated_documents

    async def _validate_dates(self, document: Dict[str, Any]) -> None:
        """
        Validate date formats and ranges.
        
        Args:
            document: Document to validate
            
        Raises:
            ValidationError: If date validation fails
        """
        try:
            # Validate publication date
            pub_date = datetime.strptime(document["publication_date"], "%Y-%m-%d")
            
            # Ensure date is not in the future
            if pub_date > datetime.now():
                raise ValidationError("Publication date cannot be in the future")
            
            # Validate other dates in metadata
            if "dates" in document.get("metadata", {}):
                for date_type, date_str in document["metadata"]["dates"].items():
                    if isinstance(date_str, str):
                        try:
                            datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            raise ValidationError(f"Invalid date format for {date_type}: {date_str}")
                            
        except ValueError as e:
            raise ValidationError(f"Date validation failed: {str(e)}")

    async def _validate_urls(self, document: Dict[str, Any]) -> None:
        """
        Validate URL formats and accessibility.
        
        Args:
            document: Document to validate
            
        Raises:
            ValidationError: If URL validation fails
        """
        metadata = document.get("metadata", {})
        
        # Validate required HTML URL
        if not metadata.get("html_url"):
            raise ValidationError("HTML URL is required")
        
        # Validate URL format
        for url_field in ["html_url", "pdf_url"]:
            if url := metadata.get(url_field):
                if not url.startswith(("http://", "https://")):
                    raise ValidationError(f"Invalid URL format for {url_field}: {url}")

    async def _validate_relationships(self, document: Dict[str, Any]) -> None:
        """
        Validate document relationships and references.
        
        Args:
            document: Document to validate
            
        Raises:
            ValidationError: If relationship validation fails
        """
        metadata = document.get("metadata", {})
        
        # Validate agency relationships
        agencies = metadata.get("agencies", [])
        if agencies:
            for agency in agencies:
                if not agency.get("name"):
                    raise ValidationError("Agency name is required")
                
        # Validate regulation ID numbers
        rin_pattern = r"^[A-Z]{4}-[A-Z0-9]{4}$"
        for rin in metadata.get("regulation_id_numbers", []):
            if not re.match(rin_pattern, rin):
                raise ValidationError(f"Invalid regulation ID number format: {rin}")

    def to_yaml(self, document: Dict[str, Any]) -> str:
        """
        Convert document to YAML format.
        
        Args:
            document: Document to convert
            
        Returns:
            str: YAML representation of the document
        """
        try:
            return yaml.dump(
                document,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        except Exception as e:
            raise ValidationError(f"Failed to convert document to YAML: {str(e)}")

    def from_yaml(self, yaml_str: str) -> Dict[str, Any]:
        """
        Parse document from YAML format.
        
        Args:
            yaml_str: YAML string to parse
            
        Returns:
            Dict[str, Any]: Parsed document
            
        Raises:
            ValidationError: If YAML parsing fails
        """
        try:
            return yaml.safe_load(yaml_str)
        except Exception as e:
            raise ValidationError(f"Failed to parse YAML document: {str(e)}") 