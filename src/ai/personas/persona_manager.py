"""
Persona management module for handling AI personas and their attributes.
Manages the lifecycle and activation of role-based AI personas.
"""
from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass
from datetime import datetime
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PersonaProfile:
    """Represents an AI persona's profile and capabilities."""
    id: str
    name: str
    role: str
    domain: str
    expertise_level: str
    certifications: List[str]
    capabilities: Set[str]
    access_level: int
    metadata: Dict[str, str]
    created_at: datetime
    updated_at: datetime

class PersonaManager:
    """
    Manages AI personas, their profiles, and activation states.
    """
    
    def __init__(self, personas_dir: Path):
        self.personas_dir = personas_dir
        self.active_personas: Dict[str, PersonaProfile] = {}
        self.persona_cache: Dict[str, PersonaProfile] = {}
        
    async def initialize(self):
        """Initialize the persona manager and load persona profiles."""
        try:
            # Create personas directory if it doesn't exist
            self.personas_dir.mkdir(parents=True, exist_ok=True)
            
            # Load all persona profiles
            await self._load_persona_profiles()
            
        except Exception as e:
            logger.error(f"Error initializing persona manager: {str(e)}")
            raise
    
    async def get_available_personas(
        self,
        domain: str,
        user_role: str,
        expertise_level: Optional[str] = None
    ) -> List[str]:
        """
        Get available personas matching the specified criteria.
        
        Args:
            domain: The domain context
            user_role: The user's role
            expertise_level: Optional expertise level requirement
            
        Returns:
            List of persona IDs that match the criteria
        """
        matching_personas = []
        
        for persona_id, profile in self.persona_cache.items():
            if self._matches_criteria(profile, domain, user_role, expertise_level):
                matching_personas.append(persona_id)
        
        return matching_personas
    
    async def activate_persona(
        self,
        persona_id: str,
        context: Optional[Dict] = None
    ) -> PersonaProfile:
        """
        Activate a persona for use in processing.
        
        Args:
            persona_id: The ID of the persona to activate
            context: Optional context for persona activation
            
        Returns:
            Activated PersonaProfile
        """
        try:
            if persona_id not in self.persona_cache:
                raise ValueError(f"Persona {persona_id} not found")
            
            profile = self.persona_cache[persona_id]
            
            # Update activation state
            self.active_personas[persona_id] = profile
            
            # Log activation
            logger.info(f"Activated persona {persona_id} with context: {context}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Error activating persona {persona_id}: {str(e)}")
            raise
    
    async def deactivate_persona(self, persona_id: str):
        """Deactivate a previously activated persona."""
        try:
            if persona_id in self.active_personas:
                del self.active_personas[persona_id]
                logger.info(f"Deactivated persona {persona_id}")
                
        except Exception as e:
            logger.error(f"Error deactivating persona {persona_id}: {str(e)}")
            raise
    
    async def _load_persona_profiles(self):
        """Load all persona profiles from YAML files."""
        try:
            for profile_path in self.personas_dir.glob("*.yaml"):
                with open(profile_path) as f:
                    profile_data = yaml.safe_load(f)
                    
                profile = PersonaProfile(
                    id=profile_data["id"],
                    name=profile_data["name"],
                    role=profile_data["role"],
                    domain=profile_data["domain"],
                    expertise_level=profile_data["expertise_level"],
                    certifications=profile_data.get("certifications", []),
                    capabilities=set(profile_data.get("capabilities", [])),
                    access_level=profile_data.get("access_level", 1),
                    metadata=profile_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(profile_data["created_at"]),
                    updated_at=datetime.fromisoformat(profile_data["updated_at"])
                )
                
                self.persona_cache[profile.id] = profile
                
        except Exception as e:
            logger.error(f"Error loading persona profiles: {str(e)}")
            raise
    
    def _matches_criteria(
        self,
        profile: PersonaProfile,
        domain: str,
        user_role: str,
        expertise_level: Optional[str]
    ) -> bool:
        """Check if a persona profile matches the specified criteria."""
        # Check domain match
        if profile.domain != domain and profile.domain != "general":
            return False
            
        # Check role compatibility
        if not self._is_role_compatible(profile.role, user_role):
            return False
            
        # Check expertise level if specified
        if expertise_level and profile.expertise_level != expertise_level:
            return False
            
        return True
    
    def _is_role_compatible(self, persona_role: str, user_role: str) -> bool:
        """Check if persona role is compatible with user role."""
        
        if persona_role == user_role or persona_role == "general":
            return True
        
        # Define role hierarchies or compatibility rules here
        role_compatibility = {
            "legal_advisor": ["legal_analyst", "general"],
            "compliance_officer": ["compliance_analyst", "general"],
            "contract_manager": ["contract_specialist", "general"],
            "procurement_officer": ["procurement_specialist", "general"],
            "general": [] # General role is compatible with all
        }
        
        if user_role in role_compatibility and persona_role in role_compatibility[user_role]:
            return True
        
        return False