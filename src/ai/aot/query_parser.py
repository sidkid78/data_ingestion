"""
Query parsing module for the Algorithm of Thought (AoT) workflow.
Handles advanced NLP processing for query intent extraction and decomposition.
"""
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

from ..llm_integration import AzureLLMClient

logger = logging.getLogger(__name__)

@dataclass
class QueryIntent:
    """Structured representation of parsed query intent."""
    primary_intent: str
    sub_intents: List[str]
    entities: Dict[str, str]
    confidence_score: float
    timestamp: datetime

@dataclass
class SubQuery:
    """Represents a decomposed sub-query with metadata."""
    text: str
    intent: str
    priority: int
    dependencies: List[str]

class QueryParser:
    """
    Advanced query parsing using LLM for intent extraction and query decomposition.
    """
    
    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client
        
    async def parse_query(
        self,
        query: str,
        user_context: Optional[Dict] = None
    ) -> Tuple[QueryIntent, List[SubQuery]]:
        """
        Parse a complex query to extract intent and decompose into sub-queries.
        
        Args:
            query: The input query string
            user_context: Optional context about the user (role, expertise, etc.)
            
        Returns:
            Tuple containing QueryIntent and list of SubQuery objects
        """
        try:
            # Extract query intent using LLM
            intent = await self._extract_intent(query, user_context)
            
            # Decompose into sub-queries if complex
            sub_queries = await self._decompose_query(query, intent)
            
            return intent, sub_queries
            
        except Exception as e:
            logger.error(f"Error parsing query: {str(e)}")
            raise
    
    async def _extract_intent(
        self,
        query: str,
        user_context: Optional[Dict]
    ) -> QueryIntent:
        """Extract the primary intent and entities from the query."""
        context_str = self._format_user_context(user_context) if user_context else ""
        
        prompt = f"""
        Analyze the following query and extract its intent and entities:
        
        User Context:
        {context_str}
        
        Query:
        {query}
        
        Provide a structured response with:
        - Primary intent
        - Sub-intents (if any)
        - Named entities
        - Confidence score (0-1)
        """
        
        response = await self.llm_client.generate(prompt)
        # TODO: Parse LLM response into structured format
        
        return QueryIntent(
            primary_intent="",  # Extract from response
            sub_intents=[],
            entities={},
            confidence_score=0.0,
            timestamp=datetime.utcnow()
        )
    
    async def _decompose_query(
        self,
        query: str,
        intent: QueryIntent
    ) -> List[SubQuery]:
        """Decompose complex queries into simpler sub-queries."""
        if not self._needs_decomposition(query, intent):
            return [SubQuery(
                text=query,
                intent=intent.primary_intent,
                priority=1,
                dependencies=[]
            )]
            
        prompt = f"""
        Decompose the following query into simpler sub-queries:
        
        Query: {query}
        Primary Intent: {intent.primary_intent}
        
        For each sub-query provide:
        1. The sub-query text
        2. Its specific intent
        3. Priority (1-5, where 1 is highest)
        4. Dependencies (if any)
        """
        
        response = await self.llm_client.generate(prompt)
        # TODO: Parse LLM response into SubQuery objects
        
        return []
    
    def _needs_decomposition(self, query: str, intent: QueryIntent) -> bool:
        """Determine if a query needs to be decomposed based on complexity."""
        # TODO: Implement complexity analysis
        return len(query.split()) > 20 or len(intent.sub_intents) > 0
    
    def _format_user_context(self, context: Dict) -> str:
        """Format user context for LLM prompt."""
        if not context:
            return ""
            
        return "\n".join([
            f"{key}: {value}"
            for key, value in context.items()
        ]) 