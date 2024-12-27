from typing import Any, Dict, List, Optional, Set
import spacy
from datetime import datetime
import re

from ...utils.logging import LoggerMixin
from ...utils.error_handling import ProcessingError


class MetadataEnricher(LoggerMixin):
    """
    Enriches document metadata using NLP techniques.
    Extracts entities, keywords, and relationships from document content.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the metadata enricher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.nlp = None
        self.initialized = False

    async def initialize(self) -> None:
        """
        Initialize spaCy model and other resources.
        
        Raises:
            ProcessingError: If initialization fails
        """
        try:
            # Load English language model
            self.nlp = spacy.load("en_core_web_sm")
            self.initialized = True
            self.logger.info("Metadata enricher initialized successfully")
            
        except Exception as e:
            raise ProcessingError(f"Failed to initialize metadata enricher: {str(e)}")

    async def enrich_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich document with additional metadata.
        
        Args:
            document: Document to enrich
            
        Returns:
            Dict[str, Any]: Enriched document
            
        Raises:
            ProcessingError: If enrichment fails
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Create enriched metadata
            enriched_metadata = {
                **document.get("metadata", {}),
                "nlp_enrichment": {
                    "entities": await self._extract_entities(document),
                    "keywords": await self._extract_keywords(document),
                    "dates": await self._extract_dates(document),
                    "citations": await self._extract_citations(document),
                    "processed_at": datetime.now(datetime.UTC).isoformat()
                }
            }

            # Return enriched document
            return {
                **document,
                "metadata": enriched_metadata
            }

        except Exception as e:
            raise ProcessingError(f"Failed to enrich document: {str(e)}")

    async def _extract_entities(self, document: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract named entities from document content.
        
        Args:
            document: Document to process
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Extracted entities by type
        """
        entities = {
            "organizations": [],
            "persons": [],
            "locations": [],
            "dates": [],
            "laws": []
        }

        # Process title and abstract
        text = f"{document.get('title', '')} {document.get('metadata', {}).get('abstract', '')}"
        doc = self.nlp(text)

        for ent in doc.ents:
            entity = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            }

            if ent.label_ == "ORG":
                entities["organizations"].append(entity)
            elif ent.label_ == "PERSON":
                entities["persons"].append(entity)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(entity)
            elif ent.label_ == "DATE":
                entities["dates"].append(entity)
            elif ent.label_ == "LAW":
                entities["laws"].append(entity)

        return entities

    async def _extract_keywords(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract important keywords from document content.
        
        Args:
            document: Document to process
            
        Returns:
            List[Dict[str, Any]]: Extracted keywords with relevance scores
        """
        # Process title and abstract
        text = f"{document.get('title', '')} {document.get('metadata', {}).get('abstract', '')}"
        doc = self.nlp(text)

        # Extract noun phrases and calculate relevance
        keywords = []
        seen = set()

        for chunk in doc.noun_chunks:
            # Clean and normalize the phrase
            phrase = " ".join(token.text.lower() for token in chunk if not token.is_stop)
            if phrase and phrase not in seen and len(phrase.split()) <= 3:
                # Calculate simple relevance score based on phrase length and frequency
                relevance = len(phrase.split()) / 3.0  # Normalize by max phrase length
                
                keywords.append({
                    "text": phrase,
                    "relevance": round(relevance, 2),
                    "pos_tags": [token.pos_ for token in chunk]
                })
                seen.add(phrase)

        # Sort by relevance
        return sorted(keywords, key=lambda x: x["relevance"], reverse=True)[:10]

    async def _extract_dates(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize dates from document content.
        
        Args:
            document: Document to process
            
        Returns:
            List[Dict[str, Any]]: Extracted and normalized dates
        """
        text = f"{document.get('title', '')} {document.get('metadata', {}).get('abstract', '')}"
        doc = self.nlp(text)

        dates = []
        seen = set()

        for ent in doc.ents:
            if ent.label_ == "DATE" and ent.text not in seen:
                try:
                    dates.append({
                        "text": ent.text,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
                    seen.add(ent.text)
                except Exception as e:
                    self.logger.warning(f"Failed to parse date '{ent.text}': {str(e)}")

        return dates

    async def _extract_citations(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract legal citations from document content.
        
        Args:
            document: Document to process
            
        Returns:
            List[Dict[str, Any]]: Extracted citations
        """
        text = f"{document.get('title', '')} {document.get('metadata', {}).get('abstract', '')}"
        
        citations = []
        
        # Common citation patterns
        patterns = [
            # Code of Federal Regulations
            r"(\d+)\s+CFR\s+(\d+(?:\.\d+)?)",
            # United States Code
            r"(\d+)\s+U\.?S\.?C\.?\s+(\d+)",
            # Public Law
            r"Pub(?:lic)?\.?\s*L(?:aw)?\.?\s*(\d+)-(\d+)",
            # Federal Register
            r"(\d+)\s+Fed\.?\s*Reg\.?\s+(\d+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citations.append({
                    "text": match.group(0),
                    "type": self._get_citation_type(pattern),
                    "start": match.start(),
                    "end": match.end()
                })

        return citations

    def _get_citation_type(self, pattern: str) -> str:
        """
        Determine citation type from regex pattern.
        
        Args:
            pattern: Regex pattern used to match citation
            
        Returns:
            str: Citation type
        """
        if "CFR" in pattern:
            return "cfr"
        elif "U.?S.?C" in pattern:
            return "usc"
        elif "Pub" in pattern:
            return "public_law"
        elif "Fed.?Reg" in pattern:
            return "federal_register"
        return "unknown" 