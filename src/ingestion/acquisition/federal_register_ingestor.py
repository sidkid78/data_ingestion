import aiohttp
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json

from ..base_ingestor import BaseIngestor
from ...utils.error_handling import DataIngestionError, retry


class FederalRegisterIngestor(BaseIngestor):
    """
    Ingestor for Federal Register data.
    Fetches documents from the Federal Register API and processes them.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config["data_sources"]["federal_register"]["api_url"]
        self.api_key = config.get("api_key")  # Optional API key

    @retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, DataIngestionError))
    async def fetch_data(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Fetch documents from the Federal Register API.
        
        Args:
            **kwargs: Additional arguments including:
                - start_date: Optional start date for fetching documents
                - end_date: Optional end date for fetching documents
                - document_type: Optional document type filter
                
        Returns:
            List[Dict[str, Any]]: List of fetched documents
        """
        try:
            # Parse date parameters
            end_date = kwargs.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            start_date = kwargs.get('start_date', 
                                  (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'))
            
            # Prepare query parameters
            params = {
                'fields[]': [
                    'title',
                    'document_number',
                    'publication_date',
                    'document_type',
                    'html_url',
                    'pdf_url',
                    'agencies',
                    'abstract',
                    'dates',
                    'regulation_id_numbers'
                ],
                'per_page': 100,
                'order': 'newest',
                'conditions[publication_date][gte]': start_date,
                'conditions[publication_date][lte]': end_date
            }
            
            if 'document_type' in kwargs:
                params['conditions[type]'] = kwargs['document_type']
            
            if self.api_key:
                params['api_key'] = self.api_key

            documents = []
            async with aiohttp.ClientSession() as session:
                while True:
                    async with session.get(f"{self.api_url}/documents", params=params) as response:
                        if response.status != 200:
                            raise DataIngestionError(f"API request failed with status {response.status}")
                        
                        data = await response.json()
                        documents.extend(data.get('results', []))
                        
                        # Check if there are more pages
                        next_page_url = data.get('next_page_url')
                        if not next_page_url:
                            break
                        
                        # Update params for next page
                        params['page'] = data.get('next_page')

            self.logger.info(f"Fetched {len(documents)} documents from Federal Register")
            return documents

        except aiohttp.ClientError as e:
            raise DataIngestionError(f"Failed to fetch data from Federal Register: {str(e)}")
        except Exception as e:
            raise DataIngestionError(f"Unexpected error during data fetch: {str(e)}")

    async def transform_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform Federal Register documents into standardized format.
        
        Args:
            data: Raw documents from Federal Register API
            
        Returns:
            List[Dict[str, Any]]: Transformed documents
        """
        transformed_documents = []
        
        for doc in data:
            try:
                transformed_doc = {
                    "source": "federal_register",
                    "document_id": doc.get("document_number"),
                    "title": doc.get("title"),
                    "document_type": doc.get("document_type", "").lower(),
                    "publication_date": doc.get("publication_date"),
                    "metadata": {
                        "html_url": doc.get("html_url"),
                        "pdf_url": doc.get("pdf_url"),
                        "abstract": doc.get("abstract"),
                        "agencies": [
                            {
                                "name": agency.get("name"),
                                "id": agency.get("id")
                            }
                            for agency in doc.get("agencies", [])
                        ],
                        "regulation_id_numbers": doc.get("regulation_id_numbers", []),
                        "dates": doc.get("dates", {})
                    },
                    "processed_at": datetime.utcnow().isoformat()
                }
                transformed_documents.append(transformed_doc)
                
            except Exception as e:
                self.logger.error(f"Error transforming document {doc.get('document_number')}: {str(e)}")
                continue

        return transformed_documents

    async def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate transformed Federal Register documents.
        
        Args:
            data: Transformed documents to validate
            
        Returns:
            List[Dict[str, Any]]: Validated documents
        """
        validated_documents = []
        
        for doc in data:
            try:
                # Required fields validation
                required_fields = ["document_id", "title", "document_type", "publication_date"]
                if not all(doc.get(field) for field in required_fields):
                    raise ValueError(f"Missing required fields: {[f for f in required_fields if not doc.get(f)]}")
                
                # Date format validation
                datetime.strptime(doc["publication_date"], "%Y-%m-%d")
                
                # Document type validation
                valid_types = ["rule", "proposed_rule", "notice", "presidential_document"]
                if doc["document_type"] not in valid_types:
                    self.logger.warning(f"Unknown document type: {doc['document_type']}")
                
                validated_documents.append(doc)
                
            except Exception as e:
                self.logger.error(f"Validation failed for document {doc.get('document_id')}: {str(e)}")
                continue

        return validated_documents

    async def store_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Store Federal Register documents in the database.
        
        Args:
            data: Validated documents to store
        """
        # TODO: Implement storage logic using PostgreSQL and Neo4j
        # This is a placeholder that just logs the documents
        for doc in data:
            self.logger.info(f"Storing document: {doc['document_id']}")
        
        self.logger.info(f"Stored {len(data)} documents") 