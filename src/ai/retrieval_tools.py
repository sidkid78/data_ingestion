"""
Tools for retrieving documents from Neo4j and Azure Cognitive Search.
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

class DocumentRetriever:
    def __init__(
        self,
        search_endpoint: str,
        search_key: str,
        search_index: str,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str
    ):
        # Initialize Azure Cognitive Search client
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index,
            credential=AzureKeyCredential(search_key)
        )
        
        # Initialize Neo4j client
        self.neo4j_client = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

    async def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search for documents using both Azure Cognitive Search and Neo4j.
        """
        try:
            # Search in Azure Cognitive Search
            semantic_results = await self._search_cognitive(query, filters, limit)
            
            # Search in Neo4j for related documents
            graph_results = await self._search_neo4j(query, filters, limit)
            
            # Merge and deduplicate results
            all_results = self._merge_results(semantic_results, graph_results)
            
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    async def _search_cognitive(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search documents using Azure Cognitive Search.
        """
        try:
            # Build filter string if filters provided
            filter_str = self._build_filter_string(filters) if filters else None
            
            # Execute search
            results = self.search_client.search(
                search_text=query,
                filter=filter_str,
                top=limit,
                include_total_count=True
            )
            
            # Convert results to list of dictionaries
            documents = []
            async for doc in results:
                documents.append({
                    "id": doc["id"],
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": doc["@search.score"],
                    "source": "cognitive_search"
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching in Cognitive Search: {str(e)}")
            raise

    async def _search_neo4j(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search documents using Neo4j graph relationships.
        """
        try:
            async with self.neo4j_client.session() as session:
                # Build Cypher query with filters
                cypher_query = """
                CALL db.index.fulltext.queryNodes("documentIndex", $query) YIELD node, score
                WHERE node:Document
                """
                
                if filters:
                    for key, value in filters.items():
                        cypher_query += f"\nAND node.{key} = ${key}"
                
                cypher_query += """
                RETURN node, score
                ORDER BY score DESC
                LIMIT $limit
                """
                
                # Execute query
                result = await session.run(
                    cypher_query,
                    query=query,
                    limit=limit,
                    **filters if filters else {}
                )
                
                # Convert results to list of dictionaries
                documents = []
                async for record in result:
                    node = record["node"]
                    documents.append({
                        "id": node["id"],
                        "title": node.get("title", ""),
                        "content": node.get("content", ""),
                        "metadata": {
                            k: v for k, v in node.items()
                            if k not in ["id", "title", "content"]
                        },
                        "score": record["score"],
                        "source": "neo4j"
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Error searching in Neo4j: {str(e)}")
            raise

    def _merge_results(
        self,
        semantic_results: List[Dict],
        graph_results: List[Dict]
    ) -> List[Dict]:
        """
        Merge and deduplicate results from different sources.
        """
        # Create a dictionary to track unique documents by ID
        unique_docs = {}
        
        # Process semantic search results
        for doc in semantic_results:
            doc_id = doc["id"]
            if doc_id not in unique_docs:
                unique_docs[doc_id] = doc
            else:
                # Update score if new score is higher
                if doc["score"] > unique_docs[doc_id]["score"]:
                    unique_docs[doc_id] = doc
        
        # Process graph search results
        for doc in graph_results:
            doc_id = doc["id"]
            if doc_id not in unique_docs:
                unique_docs[doc_id] = doc
            else:
                # Update score if new score is higher
                if doc["score"] > unique_docs[doc_id]["score"]:
                    unique_docs[doc_id] = doc
        
        # Convert back to list and sort by score
        results = list(unique_docs.values())
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results

    def _build_filter_string(self, filters: Dict) -> str:
        """
        Build OData filter string for Azure Cognitive Search.
        """
        filter_parts = []
        for key, value in filters.items():
            if isinstance(value, str):
                filter_parts.append(f"{key} eq '{value}'")
            else:
                filter_parts.append(f"{key} eq {value}")
        
        return " and ".join(filter_parts) 