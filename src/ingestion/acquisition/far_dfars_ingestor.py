"""FAR/DFARS data ingestion module."""

import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import re
import json

from ingestion.base_ingestor import BaseIngestor
from utils.error_handling import DataIngestionError, retry


class FarDfarsIngestor(BaseIngestor):
    """
    Ingestor for Federal Acquisition Regulation (FAR) and Defense Federal
    Acquisition Regulation Supplement (DFARS) documents.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config["data_sources"]["far_dfars"]["base_url"]
        self.far_index_url = f"{self.base_url}/far"
        self.dfars_index_url = f"{self.base_url}/dfars"

    @retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, DataIngestionError))
    async def fetch_data(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Fetch FAR/DFARS documents from acquisition.gov.
        
        Args:
            **kwargs: Additional arguments including:
                - regulation_type: Optional filter for "far" or "dfars"
                - part_number: Optional specific part number to fetch
                
        Returns:
            List[Dict[str, Any]]: List of fetched documents
        """
        try:
            documents = []
            regulation_type = kwargs.get("regulation_type", "both").lower()
            part_number = kwargs.get("part_number")

            async with aiohttp.ClientSession() as session:
                if regulation_type in ["both", "far"]:
                    far_docs = await self._fetch_regulation(
                        session, "far", self.far_index_url, part_number
                    )
                    documents.extend(far_docs)

                if regulation_type in ["both", "dfars"]:
                    dfars_docs = await self._fetch_regulation(
                        session, "dfars", self.dfars_index_url, part_number
                    )
                    documents.extend(dfars_docs)

            self.logger.info(f"Fetched {len(documents)} FAR/DFARS documents")
            return documents

        except aiohttp.ClientError as e:
            raise DataIngestionError(f"Failed to fetch FAR/DFARS data: {str(e)}")
        except Exception as e:
            raise DataIngestionError(f"Unexpected error during FAR/DFARS fetch: {str(e)}")

    async def _fetch_regulation(
        self,
        session: aiohttp.ClientSession,
        reg_type: str,
        index_url: str,
        part_number: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch documents for a specific regulation type.
        
        Args:
            session: aiohttp client session
            reg_type: Regulation type ("far" or "dfars")
            index_url: URL of the regulation index page
            part_number: Optional specific part number to fetch
            
        Returns:
            List[Dict[str, Any]]: List of fetched documents
        """
        documents = []
        
        try:
            # Fetch index page
            async with session.get(index_url) as response:
                if response.status != 200:
                    raise DataIngestionError(
                        f"Failed to fetch {reg_type.upper()} index: {response.status}"
                    )
                
                html = await response.text()
                soup = BeautifulSoup(html, "lxml")
                
                # Find all part links
                part_links = soup.find_all("a", href=re.compile(rf"/{reg_type}/part-\d+"))
                
                for link in part_links:
                    part_num = re.search(r"part-(\d+)", link["href"]).group(1)
                    
                    # Skip if not the requested part
                    if part_number and part_num != part_number:
                        continue
                    
                    # Fetch part content
                    part_url = f"{self.base_url}{link['href']}"
                    async with session.get(part_url) as part_response:
                        if part_response.status != 200:
                            self.logger.warning(f"Failed to fetch {part_url}")
                            continue
                        
                        part_html = await part_response.text()
                        part_soup = BeautifulSoup(part_html, "lxml")
                        
                        # Extract document information
                        title_elem = part_soup.find("h1")
                        content_elem = part_soup.find("div", class_="regulation-content")
                        
                        if title_elem and content_elem:
                            doc = {
                                "document_number": f"{reg_type.upper()}-PART-{part_num}",
                                "title": title_elem.text.strip(),
                                "document_type": reg_type.lower(),
                                "publication_date": datetime.now().strftime("%Y-%m-%d"),  # Use last updated date if available
                                "html_url": part_url,
                                "content": content_elem.text.strip(),
                                "part_number": part_num,
                                "subparts": await self._extract_subparts(part_soup)
                            }
                            documents.append(doc)
                            
                            self.logger.info(f"Fetched {reg_type.upper()} Part {part_num}")
                
        except Exception as e:
            self.logger.error(f"Error fetching {reg_type.upper()}: {str(e)}")
            raise

        return documents

    async def _extract_subparts(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract subpart information from a regulation part.
        
        Args:
            soup: BeautifulSoup object of the part page
            
        Returns:
            List[Dict[str, Any]]: List of subparts with their sections
        """
        subparts = []
        current_subpart = None
        
        for section in soup.find_all(["h2", "h3", "div"], class_=["subpart", "section"]):
            if "subpart" in section.get("class", []):
                if current_subpart:
                    subparts.append(current_subpart)
                
                current_subpart = {
                    "title": section.text.strip(),
                    "sections": []
                }
            
            elif "section" in section.get("class", []) and current_subpart:
                section_num = section.find("span", class_="section-number")
                section_title = section.find("span", class_="section-title")
                
                if section_num and section_title:
                    current_subpart["sections"].append({
                        "number": section_num.text.strip(),
                        "title": section_title.text.strip(),
                        "content": section.text.strip()
                    })
        
        if current_subpart:
            subparts.append(current_subpart)
        
        return subparts

    async def transform_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform FAR/DFARS documents into standardized format.
        
        Args:
            data: Raw documents from acquisition.gov
            
        Returns:
            List[Dict[str, Any]]: Transformed documents
        """
        transformed_documents = []
        
        for doc in data:
            try:
                transformed_doc = {
                    "source": "far_dfars",
                    "document_id": doc["document_number"],
                    "title": doc["title"],
                    "document_type": doc["document_type"],
                    "publication_date": doc["publication_date"],
                    "metadata": {
                        "html_url": doc["html_url"],
                        "part_number": doc["part_number"],
                        "subparts": doc["subparts"],
                        "regulation_type": doc["document_type"].upper(),
                        "content_summary": doc["content"][:500] + "..."  # First 500 chars
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
        Validate transformed FAR/DFARS documents.
        
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
                
                # Validate regulation type
                if doc["document_type"] not in ["far", "dfars"]:
                    raise ValueError(f"Invalid regulation type: {doc['document_type']}")
                
                # Validate part number format
                part_number = doc["metadata"].get("part_number")
                if not part_number or not part_number.isdigit():
                    raise ValueError(f"Invalid part number: {part_number}")
                
                # Validate subparts structure
                subparts = doc["metadata"].get("subparts", [])
                if not isinstance(subparts, list):
                    raise ValueError("Subparts must be a list")
                
                for subpart in subparts:
                    if not isinstance(subpart, dict) or "title" not in subpart or "sections" not in subpart:
                        raise ValueError("Invalid subpart structure")
                
                validated_documents.append(doc)
                
            except Exception as e:
                self.logger.error(f"Validation failed for document {doc.get('document_id')}: {str(e)}")
                continue

        return validated_documents

    async def store_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Store FAR/DFARS documents in the database.
        
        Args:
            data: Validated documents to store
        """
        # TODO: Implement storage logic using PostgreSQL and Neo4j
        # This is a placeholder that just logs the documents
        for doc in data:
            self.logger.info(f"Storing document: {doc['document_id']}")
        
        self.logger.info(f"Stored {len(data)} documents") 