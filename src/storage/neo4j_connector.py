"""Neo4j database connector."""

from neo4j import AsyncGraphDatabase
from typing import Dict, Any, List, Optional
import os
from datetime import datetime

from utils.logging import LoggerMixin
from utils.error_handling import StorageError
from neo4j.exceptions import ServiceUnavailable, AuthError
from utils.error_handling import retry

class Neo4jConnector(LoggerMixin):
    """Neo4j database connector class."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Neo4j connector with configuration."""
        super().__init__()
        self.config = config or {
            "uri": os.getenv("NEO4J_URI"),
            "user": os.getenv("NEO4J_USER"),
            "password": os.getenv("NEO4J_PASSWORD")
        }
        self.driver = None

    async def initialize(self) -> None:
        """
        Initialize Neo4j connection.
        
        Raises:
            StorageError: If connection fails
        """
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.config['uri'],
                auth=(self.config['user'], self.config['password'])
            )
            # Verify connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            self.logger.info("Neo4j connection initialized successfully")
            
        except (ServiceUnavailable, AuthError) as e:
            raise StorageError(f"Failed to initialize Neo4j connection: {str(e)}")

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self.logger.info("Neo4j connection closed")

    @retry(max_attempts=3, delay=1.0, exceptions=(StorageError,))
    async def store_document_node(self, document: Dict[str, Any]) -> None:
        """
        Store a document as a node in Neo4j.
        
        Args:
            document: Document data to store
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self.driver:
            raise StorageError("Neo4j connection not initialized")

        # Create document node query
        query = """
        MERGE (d:Document {document_id: $document_id})
        SET d += $properties
        """
        
        properties = {
            "document_id": document["document_id"],
            "title": document["title"],
            "source": document["source"],
            "document_type": document["document_type"],
            "publication_date": document["publication_date"],
            "updated_at": datetime.utcnow().isoformat()
        }

        try:
            async with self.driver.session() as session:
                await session.run(query, document_id=document["document_id"], properties=properties)
                
                # Create agency relationships
                for agency in document.get("metadata", {}).get("agencies", []):
                    await self.create_agency_relationship(
                        document["document_id"],
                        agency["name"],
                        agency.get("id")
                    )
                
                # Create regulation relationships
                for rin in document.get("metadata", {}).get("regulation_id_numbers", []):
                    await self.create_regulation_relationship(
                        document["document_id"],
                        rin
                    )
                
            self.logger.info(f"Stored document node: {document['document_id']}")
            
        except Exception as e:
            raise StorageError(f"Failed to store document node: {str(e)}")

    async def create_agency_relationship(
        self,
        document_id: str,
        agency_name: str,
        agency_id: Optional[str] = None
    ) -> None:
        """
        Create relationship between document and agency.
        
        Args:
            document_id: Document identifier
            agency_name: Name of the agency
            agency_id: Optional agency identifier
        """
        if not self.driver:
            raise StorageError("Neo4j connection not initialized")

        query = """
        MATCH (d:Document {document_id: $document_id})
        MERGE (a:Agency {name: $agency_name})
        SET a.agency_id = $agency_id
        MERGE (d)-[r:ISSUED_BY]->(a)
        SET r.created_at = $timestamp
        """

        try:
            async with self.driver.session() as session:
                await session.run(
                    query,
                    document_id=document_id,
                    agency_name=agency_name,
                    agency_id=agency_id,
                    timestamp=datetime.utcnow().isoformat()
                )
        except Exception as e:
            self.logger.error(f"Failed to create agency relationship: {str(e)}")

    async def create_regulation_relationship(
        self,
        document_id: str,
        regulation_id: str
    ) -> None:
        """
        Create relationship between document and regulation.
        
        Args:
            document_id: Document identifier
            regulation_id: Regulation identifier
        """
        if not self.driver:
            raise StorageError("Neo4j connection not initialized")

        query = """
        MATCH (d:Document {document_id: $document_id})
        MERGE (r:Regulation {regulation_id: $regulation_id})
        MERGE (d)-[rel:REFERENCES]->(r)
        SET rel.created_at = $timestamp
        """

        try:
            async with self.driver.session() as session:
                await session.run(
                    query,
                    document_id=document_id,
                    regulation_id=regulation_id,
                    timestamp=datetime.utcnow().isoformat()
                )
        except Exception as e:
            self.logger.error(f"Failed to create regulation relationship: {str(e)}")

    async def get_document_relationships(
        self,
        document_id: str,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all relationships for a document.
        
        Args:
            document_id: Document identifier
            relationship_types: Optional list of relationship types to filter
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary of relationships by type
        """
        if not self.driver:
            raise StorageError("Neo4j connection not initialized")

        # Default relationship types if none specified
        if not relationship_types:
            relationship_types = ["ISSUED_BY", "REFERENCES"]

        relationships: Dict[str, List[Dict[str, Any]]] = {}
        
        try:
            async with self.driver.session() as session:
                for rel_type in relationship_types:
                    query = f"""
                    MATCH (d:Document {{document_id: $document_id}})-[r:{rel_type}]->(n)
                    RETURN type(r) as type, n, r.created_at as created_at
                    """
                    
                    result = await session.run(query, document_id=document_id)
                    records = await result.data()
                    
                    relationships[rel_type] = [
                        {
                            "type": record["type"],
                            "node": dict(record["n"]),
                            "created_at": record["created_at"]
                        }
                        for record in records
                    ]
                    
            return relationships
            
        except Exception as e:
            raise StorageError(f"Failed to get document relationships: {str(e)}")

    async def find_related_documents(
        self,
        document_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents related to the given document through relationships.
        
        Args:
            document_id: Starting document identifier
            max_depth: Maximum depth to traverse relationships
            relationship_types: Optional list of relationship types to consider
            
        Returns:
            List[Dict[str, Any]]: List of related documents with relationship info
        """
        if not self.driver:
            raise StorageError("Neo4j connection not initialized")

        # Default relationship types if none specified
        if not relationship_types:
            relationship_types = ["ISSUED_BY", "REFERENCES"]

        rel_pattern = "|".join(f":{rel_type}" for rel_type in relationship_types)
        
        query = f"""
        MATCH path = (d:Document {{document_id: $document_id}})-[{rel_pattern}*1..{max_depth}]-(related:Document)
        RETURN related, relationships(path) as rels
        LIMIT 100
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query, document_id=document_id)
                records = await result.data()
                
                related_docs = []
                for record in records:
                    doc = dict(record["related"])
                    relationships = [
                        {
                            "type": rel.type,
                            "created_at": rel.get("created_at")
                        }
                        for rel in record["rels"]
                    ]
                    
                    related_docs.append({
                        "document": doc,
                        "relationships": relationships
                    })
                    
                return related_docs
                
        except Exception as e:
            raise StorageError(f"Failed to find related documents: {str(e)}")

    async def delete_document_node(self, document_id: str) -> bool:
        """
        Delete a document node and its relationships.
        
        Args:
            document_id: Document identifier to delete
            
        Returns:
            bool: True if document was deleted, False if not found
        """
        if not self.driver:
            raise StorageError("Neo4j connection not initialized")

        query = """
        MATCH (d:Document {document_id: $document_id})
        OPTIONAL MATCH (d)-[r]-()
        DELETE r, d
        RETURN count(d) as deleted
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query, document_id=document_id)
                data = await result.data()
                return data[0]["deleted"] > 0
                
        except Exception as e:
            raise StorageError(f"Failed to delete document node: {str(e)}") 