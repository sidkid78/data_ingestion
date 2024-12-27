"""
RAG (Retrieval-Augmented Generation) agent for intelligent document querying and synthesis.
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .llm_integration import AzureLLMClient
from .retrieval_tools import DocumentRetriever
from .summarization import ResultSynthesizer

logger = logging.getLogger(__name__)

class RAGAgent:
    def __init__(
        self,
        llm_client: AzureLLMClient,
        retriever: DocumentRetriever,
        synthesizer: ResultSynthesizer
    ):
        self.llm_client = llm_client
        self.retriever = retriever
        self.synthesizer = synthesizer

    async def process_query(
        self,
        query: str,
        metadata_filters: Optional[Dict] = None,
        max_results: int = 10
    ) -> Dict:
        """
        Process a user query through the RAG pipeline.
        """
        try:
            # Decompose query into sub-queries
            sub_queries = await self.decompose_query(query)
            
            # Retrieve relevant documents for each sub-query
            retrieval_results = []
            for sub_query in sub_queries:
                docs = await self.retriever.search(
                    query=sub_query,
                    filters=metadata_filters,
                    limit=max_results
                )
                retrieval_results.extend(docs)
            
            # Synthesize results into a coherent response
            synthesis = await self.synthesizer.synthesize(
                query=query,
                documents=retrieval_results
            )
            
            return {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "synthesis": synthesis,
                "sources": retrieval_results
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    async def decompose_query(self, query: str) -> List[str]:
        """
        Decompose a complex query into simpler sub-queries using LLM.
        """
        try:
            # Use LLM to analyze and break down the query
            decomposition_prompt = f"""
            Analyze the following query and break it down into simpler sub-queries:
            Query: {query}
            
            Return only the sub-queries, one per line.
            """
            
            response = await self.llm_client.generate(decomposition_prompt)
            sub_queries = [q.strip() for q in response.split('\n') if q.strip()]
            
            return sub_queries if sub_queries else [query]
            
        except Exception as e:
            logger.error(f"Error decomposing query: {str(e)}")
            return [query]  # Fallback to original query

    async def validate_compliance(
        self,
        document: Dict,
        policies: List[Dict]
    ) -> Dict:
        """
        Validate document compliance against existing policies.
        """
        try:
            validation_results = await self.llm_client.analyze_compliance(
                document=document,
                policies=policies
            )
            
            return {
                "document_id": document.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
                "validation_results": validation_results,
                "status": "compliant" if validation_results.get("is_compliant") else "non_compliant"
            }
            
        except Exception as e:
            logger.error(f"Error validating compliance: {str(e)}")
            raise 