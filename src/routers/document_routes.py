from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..storage.postgresql_connector import PostgreSQLConnector
from ..storage.neo4j_connector import Neo4jConnector
from ..utils.config_loader import AppConfig
from ..utils.error_handling import handle_exceptions, StorageError
from ..utils.logging import get_logger

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)


class DocumentResponse(BaseModel):
    """Response model for document endpoints."""
    document_id: str
    source: str
    title: str
    document_type: str
    publication_date: str
    metadata: dict
    created_at: str
    updated_at: str


class DocumentRelationshipResponse(BaseModel):
    """Response model for document relationship endpoints."""
    document_id: str
    relationships: dict


async def get_db(config: AppConfig = Depends()):
    """Get database connections."""
    pg_connector = PostgreSQLConnector(config.storage.postgresql)
    neo4j_connector = Neo4jConnector(config.storage.neo4j)
    
    try:
        await pg_connector.initialize()
        await neo4j_connector.initialize()
        yield {"pg": pg_connector, "neo4j": neo4j_connector}
    finally:
        await pg_connector.close()
        await neo4j_connector.close()


@router.get("", response_model=List[DocumentResponse])
@handle_exceptions(logger)
async def list_documents(
    source: Optional[str] = None,
    document_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: dict = Depends(get_db)
):
    """
    List documents with optional filtering.
    
    Args:
        source: Filter by document source
        document_type: Filter by document type
        start_date: Filter by start date (YYYY-MM-DD)
        end_date: Filter by end date (YYYY-MM-DD)
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        db: Database connections
        
    Returns:
        List[DocumentResponse]: List of documents
    """
    try:
        # Convert date strings to datetime objects
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        
        documents = await db["pg"].search_documents(
            source=source,
            document_type=document_type,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset
        )
        
        return documents
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
@handle_exceptions(logger)
async def get_document(
    document_id: str,
    db: dict = Depends(get_db)
):
    """
    Get a single document by ID.
    
    Args:
        document_id: Document identifier
        db: Database connections
        
    Returns:
        DocumentResponse: Document details
    """
    document = await db["pg"].get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/relationships", response_model=DocumentRelationshipResponse)
@handle_exceptions(logger)
async def get_document_relationships(
    document_id: str,
    relationship_types: Optional[List[str]] = Query(None),
    db: dict = Depends(get_db)
):
    """
    Get relationships for a document.
    
    Args:
        document_id: Document identifier
        relationship_types: Optional list of relationship types to filter
        db: Database connections
        
    Returns:
        DocumentRelationshipResponse: Document relationships
    """
    # Verify document exists in PostgreSQL
    document = await db["pg"].get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get relationships from Neo4j
    relationships = await db["neo4j"].get_document_relationships(
        document_id,
        relationship_types=relationship_types
    )
    
    return {
        "document_id": document_id,
        "relationships": relationships
    }


@router.get("/{document_id}/related", response_model=List[DocumentResponse])
@handle_exceptions(logger)
async def get_related_documents(
    document_id: str,
    max_depth: int = Query(default=2, le=3),
    relationship_types: Optional[List[str]] = Query(None),
    db: dict = Depends(get_db)
):
    """
    Get documents related to the given document.
    
    Args:
        document_id: Document identifier
        max_depth: Maximum depth to traverse relationships
        relationship_types: Optional list of relationship types to filter
        db: Database connections
        
    Returns:
        List[DocumentResponse]: List of related documents
    """
    # Verify document exists
    document = await db["pg"].get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get related documents from Neo4j
    related = await db["neo4j"].find_related_documents(
        document_id,
        max_depth=max_depth,
        relationship_types=relationship_types
    )
    
    # Fetch full document details from PostgreSQL
    related_docs = []
    for rel in related:
        doc = await db["pg"].get_document(rel["document"]["document_id"])
        if doc:
            related_docs.append(doc)
    
    return related_docs


@router.delete("/{document_id}", status_code=204)
@handle_exceptions(logger)
async def delete_document(
    document_id: str,
    db: dict = Depends(get_db)
):
    """
    Delete a document and its relationships.
    
    Args:
        document_id: Document identifier
        db: Database connections
    """
    # Delete from PostgreSQL
    pg_deleted = await db["pg"].delete_document(document_id)
    if not pg_deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from Neo4j
    await db["neo4j"].delete_document_node(document_id)
    
    logger.info(f"Deleted document: {document_id}") 