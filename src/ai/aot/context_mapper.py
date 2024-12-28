"""
Context mapping module for the Algorithm of Thought (AoT) workflow.
Maps queries to user context and activates relevant AI personas.
"""
from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass
from datetime import datetime

from ..personas.persona_manager import PersonaManager
from .query_parser import QueryIntent

logger = logging.getLogger(__name__)

@dataclass
class ContextualMapping:
    """Represents the contextual mapping of a query."""
    query_intent: QueryIntent
    user_role: str
    expertise_level: str
    domain_context: Dict[str, str]
    relevant_personas: Set[str]
    timestamp: datetime

class ContextMapper:
    """
    Maps queries to appropriate context and activates relevant AI personas.
    """
    
    def __init__(self, persona_manager: PersonaManager):
        self.persona_manager = persona_manager
        
    async def map_context(
        self,
        query_intent: QueryIntent,
        user_metadata: Dict
    ) -> ContextualMapping:
        """
        Map query intent to user context and identify relevant personas.
        
        Args:
            query_intent: Parsed query intent
            user_metadata: User information including role, expertise, etc.
            
        Returns:
            ContextualMapping object with relevant context and personas
        """
        try:
            # Extract user context
            user_role = user_metadata.get("role", "general")
            expertise_level = user_metadata.get("expertise_level", "intermediate")
            
            # Determine domain context
            domain_context = await self._extract_domain_context(
                query_intent,
                user_metadata
            )
            
            # Identify relevant personas
            relevant_personas = await self._identify_relevant_personas(
                query_intent,
                domain_context,
                user_role
            )
            
            return ContextualMapping(
                query_intent=query_intent,
                user_role=user_role,
                expertise_level=expertise_level,
                domain_context=domain_context,
                relevant_personas=relevant_personas,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error mapping context: {str(e)}")
            raise
    
    async def _extract_domain_context(
        self,
        query_intent: QueryIntent,
        user_metadata: Dict
    ) -> Dict[str, str]:
        """Extract domain-specific context based on query intent and user metadata."""
        domain_context = {
            "primary_domain": self._determine_primary_domain(query_intent),
            "related_domains": self._identify_related_domains(query_intent),
            "temporal_context": datetime.utcnow().isoformat(),
            "spatial_context": user_metadata.get("location", "global"),
            "regulatory_context": user_metadata.get("regulatory_framework", "general")
        }
        
        # Enrich with any domain-specific attributes
        if domain_specific_attrs := self._get_domain_specific_attributes(
            domain_context["primary_domain"]
        ):
            domain_context.update(domain_specific_attrs)
        
        return domain_context
    
    async def _identify_relevant_personas(
        self,
        query_intent: QueryIntent,
        domain_context: Dict[str, str],
        user_role: str
    ) -> Set[str]:
        """Identify and activate relevant AI personas based on context."""
        try:
            # Get available personas that match the domain and user role
            available_personas = await self.persona_manager.get_available_personas(
                domain=domain_context["primary_domain"],
                user_role=user_role
            )
            
            # Filter based on query intent and expertise requirements
            relevant_personas = set()
            for persona in available_personas:
                if self._is_persona_relevant(persona, query_intent):
                    relevant_personas.add(persona)
            
            return relevant_personas
            
        except Exception as e:
            logger.error(f"Error identifying relevant personas: {str(e)}")
            return set()  # Return empty set as fallback
    
    def _determine_primary_domain(self, query_intent: QueryIntent) -> str:
        """Determine the primary domain based on query intent and entities."""
        # TODO: Implement domain determination logic
        return "general"
    
    def _identify_related_domains(self, query_intent: QueryIntent) -> List[str]:
        """Identify related domains based on query intent."""
        # TODO: Implement related domain identification
        return []
    
    def _get_domain_specific_attributes(self, domain: str) -> Optional[Dict[str, str]]:
        """Get domain-specific attributes for context enrichment."""
        # TODO: Implement domain-specific attribute lookup
        return None
    
    def _is_persona_relevant(self, persona: str, query_intent: QueryIntent) -> bool:
        """Determine if a persona is relevant for the given query intent."""
        # TODO: Implement persona relevance checking
        return True 