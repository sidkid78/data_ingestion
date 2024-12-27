"""
Standards document ingestor implementation.
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import re
import logging

from ..base_ingestor import BaseIngestor
from ...utils.error_handling import DataIngestionError, retry
from ...utils.logging import LoggerMixin


class StandardsIngestor(BaseIngestor, LoggerMixin):
    """Ingestor for standards documents from various sources."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the standards ingestor.
        
        Args:
            config: Configuration dictionary containing API endpoints and settings.
        """
        super().__init__()
        self.config = config
        self.session = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    @retry(max_attempts=3, delay=1)
    async def fetch_data(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch standards documents from the specified source.
        
        Args:
            source: The source to fetch standards from (e.g., 'nist', 'iso').
            **kwargs: Additional parameters for filtering and pagination.
        
        Returns:
            List of fetched documents.
        
        Raises:
            DataIngestionError: If there's an error fetching the documents.
        """
        await self.initialize()
        
        try:
            if source == "nist":
                return await self._fetch_nist_standards(**kwargs)
            elif source == "iso":
                return await self._fetch_iso_standards(**kwargs)
            else:
                raise DataIngestionError(f"Unsupported standards source: {source}")
        except Exception as e:
            raise DataIngestionError(f"Error fetching standards from {source}: {str(e)}")

    async def _fetch_nist_standards(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch standards from NIST.
        
        Returns:
            List of NIST standards documents.
        """
        base_url = self.config["standards"]["nist"]["base_url"]
        standards = []

        try:
            async with self.session.get(f"{base_url}/search") as response:
                if response.status != 200:
                    raise DataIngestionError(f"NIST API returned status {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                for item in soup.select(".standard-item"):
                    standard = {
                        "document_id": item.get("data-standard-id", ""),
                        "title": item.select_one(".title").text.strip(),
                        "publication_date": item.select_one(".date").text.strip(),
                        "source": "nist",
                        "document_type": "standard",
                        "metadata": {
                            "status": item.select_one(".status").text.strip(),
                            "category": item.select_one(".category").text.strip(),
                            "url": f"{base_url}{item.select_one('a')['href']}",
                            "abstract": item.select_one(".abstract").text.strip()
                        }
                    }
                    standards.append(standard)

        except Exception as e:
            self.logger.error(f"Error fetching NIST standards: {str(e)}")
            raise DataIngestionError(f"Failed to fetch NIST standards: {str(e)}")

        return standards

    async def _fetch_iso_standards(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch standards from ISO.
        
        Returns:
            List of ISO standards documents.
        """
        base_url = self.config["standards"]["iso"]["base_url"]
        standards = []

        try:
            async with self.session.get(f"{base_url}/search") as response:
                if response.status != 200:
                    raise DataIngestionError(f"ISO API returned status {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                for item in soup.select(".standard-item"):
                    standard = {
                        "document_id": item.get("data-standard-id", ""),
                        "title": item.select_one(".title").text.strip(),
                        "publication_date": item.select_one(".date").text.strip(),
                        "source": "iso",
                        "document_type": "standard",
                        "metadata": {
                            "status": item.select_one(".status").text.strip(),
                            "technical_committee": item.select_one(".committee").text.strip(),
                            "url": f"{base_url}{item.select_one('a')['href']}",
                            "abstract": item.select_one(".abstract").text.strip()
                        }
                    }
                    standards.append(standard)

        except Exception as e:
            self.logger.error(f"Error fetching ISO standards: {str(e)}")
            raise DataIngestionError(f"Failed to fetch ISO standards: {str(e)}")

        return standards

    async def transform_data(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform the fetched standards documents.
        
        Args:
            documents: List of documents to transform.
        
        Returns:
            List of transformed documents.
        """
        transformed = []
        
        for doc in documents:
            try:
                # Standardize dates
                if "publication_date" in doc:
                    doc["publication_date"] = datetime.strptime(
                        doc["publication_date"], "%Y-%m-%d"
                    ).strftime("%Y-%m-%d")

                # Add timestamps
                doc["created_at"] = datetime.utcnow().isoformat()
                doc["updated_at"] = doc["created_at"]

                transformed.append(doc)
            except Exception as e:
                self.logger.error(f"Error transforming document {doc.get('document_id')}: {str(e)}")
                continue

        return transformed

    async def validate_data(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate the transformed standards documents.
        
        Args:
            documents: List of documents to validate.
        
        Returns:
            List of validated documents.
        
        Raises:
            DataIngestionError: If validation fails.
        """
        validated = []
        required_fields = ["document_id", "title", "publication_date", "source", "document_type"]
        
        for doc in documents:
            try:
                # Check required fields
                missing_fields = [field for field in required_fields if not doc.get(field)]
                if missing_fields:
                    raise DataIngestionError(
                        f"Document {doc.get('document_id')} missing required fields: {missing_fields}"
                    )

                # Validate source
                if doc["source"] not in ["nist", "iso"]:
                    raise DataIngestionError(
                        f"Invalid source '{doc['source']}' for document {doc['document_id']}"
                    )

                validated.append(doc)
            except Exception as e:
                self.logger.error(f"Validation error for document {doc.get('document_id')}: {str(e)}")
                continue

        return validated

    async def store_data(self, documents: List[Dict[str, Any]]) -> bool:
        """Store the validated standards documents.
        
        Args:
            documents: List of documents to store.
        
        Returns:
            True if storage was successful.
        
        Raises:
            DataIngestionError: If storage fails.
        """
        try:
            # Store in PostgreSQL
            # TODO: Implement PostgreSQL storage
            
            # Store in Neo4j
            # TODO: Implement Neo4j storage
            
            return True
        except Exception as e:
            raise DataIngestionError(f"Failed to store documents: {str(e)}")

    async def ingest(self, source: str, **kwargs) -> bool:
        """Run the complete ingestion pipeline for standards documents.
        
        Args:
            source: The source to ingest standards from.
            **kwargs: Additional parameters for the ingestion process.
        
        Returns:
            True if ingestion was successful.
        """
        try:
            self.logger.info(f"Starting standards ingestion from {source}")
            
            # Fetch data
            documents = await self.fetch_data(source, **kwargs)
            self.logger.info(f"Fetched {len(documents)} documents from {source}")
            
            # Transform data
            transformed = await self.transform_data(documents)
            self.logger.info(f"Transformed {len(transformed)} documents")
            
            # Validate data
            validated = await self.validate_data(transformed)
            self.logger.info(f"Validated {len(validated)} documents")
            
            # Store data
            success = await self.store_data(validated)
            if success:
                self.logger.info(f"Successfully stored {len(validated)} documents")
            
            return success
        except Exception as e:
            self.logger.error(f"Error during standards ingestion: {str(e)}")
            raise
        finally:
            await self.cleanup() 