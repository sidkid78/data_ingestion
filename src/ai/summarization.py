"""
Synthesize and summarize retrieved documents into coherent responses.
"""
from typing import Dict, List
import logging
import json

from .llm_integration import AzureLLMClient

logger = logging.getLogger(__name__)

class ResultSynthesizer:
    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    async def synthesize(
        self,
        query: str,
        documents: List[Dict],
        max_length: int = 1000
    ) -> Dict:
        """
        Synthesize retrieved documents into a coherent response.
        """
        try:
            # Extract relevant content from documents
            doc_contents = self._prepare_documents(documents)
            
            # Generate synthesis prompt
            prompt = self._generate_synthesis_prompt(query, doc_contents)
            
            # Generate synthesis using LLM
            synthesis = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=max_length
            )
            
            # Parse and structure the response
            try:
                response = json.loads(synthesis)
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                response = {
                    "summary": synthesis,
                    "key_points": [],
                    "references": []
                }
            
            return {
                "synthesis": response.get("summary", ""),
                "key_points": response.get("key_points", []),
                "references": response.get("references", []),
                "source_documents": [doc["id"] for doc in documents]
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing results: {str(e)}")
            raise

    def _prepare_documents(self, documents: List[Dict]) -> List[str]:
        """
        Extract and prepare document contents for synthesis.
        """
        contents = []
        for doc in documents:
            content = f"""
            Document ID: {doc.get('id')}
            Title: {doc.get('title', 'Untitled')}
            Content: {doc.get('content', '')}
            Relevance Score: {doc.get('score', 0)}
            Source: {doc.get('source', 'unknown')}
            """
            contents.append(content.strip())
        
        return contents

    def _generate_synthesis_prompt(
        self,
        query: str,
        doc_contents: List[str]
    ) -> str:
        """
        Generate a prompt for synthesizing document contents.
        """
        return f"""
        Based on the following query and retrieved documents, provide a comprehensive synthesis.
        Format the response as JSON with the following structure:
        {{
            "summary": "A coherent summary addressing the query",
            "key_points": ["List of key points extracted from documents"],
            "references": ["List of relevant document references"]
        }}

        Query: {query}

        Retrieved Documents:
        {'-' * 80}
        {'\n'.join(doc_contents)}
        {'-' * 80}

        Synthesize the information focusing on:
        1. Direct answers to the query
        2. Supporting evidence from documents
        3. Relationships between different sources
        4. Any conflicting information
        5. Key insights and implications

        Ensure the synthesis is:
        - Comprehensive yet concise
        - Well-structured and coherent
        - Supported by document references
        - Relevant to the original query
        """

    async def extract_key_points(
        self,
        text: str,
        max_points: int = 5
    ) -> List[str]:
        """
        Extract key points from a text using LLM.
        """
        try:
            prompt = f"""
            Extract the {max_points} most important points from the following text.
            Return the points as a JSON array of strings.

            Text:
            {text}
            """
            
            response = await self.llm_client.generate(prompt)
            points = json.loads(response)
            
            return points[:max_points]
            
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return []

    async def generate_summary(
        self,
        text: str,
        max_length: int = 200
    ) -> str:
        """
        Generate a concise summary of a text using LLM.
        """
        try:
            prompt = f"""
            Generate a concise summary (maximum {max_length} characters) of the following text:

            {text}
            """
            
            summary = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=max_length
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "" 