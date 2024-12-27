"""
Integration with Azure OpenAI services for LLM-based operations.
"""
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime

from azure.core.credentials import TokenCredential
from azure.ai.textanalytics import TextAnalyticsClient
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class AzureLLMClient:
    def __init__(
        self,
        endpoint: str,
        deployment_name: str,
        api_version: str,
        api_key: str,
        cognitive_endpoint: str = None,
        cognitive_key: str = None
    ):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.deployment_name = deployment_name
        
        # Initialize Text Analytics client if credentials provided
        self.text_analytics = None
        if cognitive_endpoint and cognitive_key:
            self.text_analytics = TextAnalyticsClient(
                endpoint=cognitive_endpoint,
                credential=cognitive_key
            )

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Azure OpenAI.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    async def analyze_compliance(
        self,
        document: Dict,
        policies: List[Dict]
    ) -> Dict:
        """
        Analyze document compliance against policies using LLM.
        """
        try:
            # Format document and policies for analysis
            context = self._format_compliance_context(document, policies)
            
            prompt = f"""
            Analyze the following document for compliance with the provided policies:
            
            Document:
            {json.dumps(document, indent=2)}
            
            Policies:
            {json.dumps(policies, indent=2)}
            
            Provide a detailed compliance analysis including:
            1. Compliance status
            2. Identified conflicts or issues
            3. Recommendations for resolution
            
            Format the response as JSON.
            """
            
            response = await self.generate(prompt)
            analysis = json.loads(response)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "is_compliant": analysis.get("compliance_status") == "compliant",
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing compliance: {str(e)}")
            raise

    async def extract_metadata(
        self,
        text: str,
        metadata_types: List[str]
    ) -> Dict:
        """
        Extract metadata from text using Azure Text Analytics.
        """
        try:
            if not self.text_analytics:
                raise ValueError("Text Analytics client not initialized")
            
            result = {}
            
            # Extract entities
            if "entities" in metadata_types:
                response = self.text_analytics.recognize_entities([text])[0]
                result["entities"] = [
                    {
                        "text": entity.text,
                        "category": entity.category,
                        "confidence_score": entity.confidence_score
                    }
                    for entity in response.entities
                ]
            
            # Extract key phrases
            if "key_phrases" in metadata_types:
                response = self.text_analytics.extract_key_phrases([text])[0]
                result["key_phrases"] = response.key_phrases
            
            # Extract sentiment
            if "sentiment" in metadata_types:
                response = self.text_analytics.analyze_sentiment([text])[0]
                result["sentiment"] = {
                    "sentiment": response.sentiment,
                    "confidence_scores": response.confidence_scores._asdict()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise

    def _format_compliance_context(
        self,
        document: Dict,
        policies: List[Dict]
    ) -> str:
        """
        Format document and policies for compliance analysis.
        """
        return f"""
        Document ID: {document.get('id')}
        Title: {document.get('title')}
        Content: {document.get('content')}
        
        Relevant Policies:
        {json.dumps(policies, indent=2)}
        """ 