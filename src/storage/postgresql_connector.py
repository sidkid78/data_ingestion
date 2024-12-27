from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import select, update, delete

from ..utils.logging import LoggerMixin
from ..utils.error_handling import StorageError, retry

Base = declarative_base()

class Document(Base):
    """SQLAlchemy model for documents."""
    __tablename__ = 'documents'

    document_id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    document_type = Column(String, nullable=False)
    publication_date = Column(DateTime, nullable=False)
    metadata = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_documents_source', 'source'),
        Index('idx_documents_type', 'document_type'),
        Index('idx_documents_date', 'publication_date'),
        Index('idx_documents_metadata', 'metadata', postgresql_using='gin'),
    )


class PostgreSQLConnector(LoggerMixin):
    """
    Connector for PostgreSQL database operations.
    Handles document storage and retrieval.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PostgreSQL connector.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.engine = None
        self.SessionLocal = None

    async def initialize(self) -> None:
        """
        Initialize database connection and create tables.
        """
        try:
            # Construct database URL
            db_url = f"postgresql+asyncpg://{self.config['user']}:{self.config['password']}@" \
                    f"{self.config['host']}:{self.config['port']}/{self.config['database']}"

            # Create async engine
            self.engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=5,
                max_overflow=10
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.logger.info("PostgreSQL connection initialized successfully")

        except Exception as e:
            raise StorageError(f"Failed to initialize PostgreSQL connection: {str(e)}")

    async def close(self) -> None:
        """
        Close database connection.
        """
        if self.engine:
            await self.engine.dispose()
            self.logger.info("PostgreSQL connection closed")

    @retry(max_attempts=3, delay=1.0, exceptions=(StorageError,))
    async def store_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Store multiple documents in the database.
        
        Args:
            documents: List of documents to store
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self.SessionLocal:
            raise StorageError("Database connection not initialized")

        async with self.SessionLocal() as session:
            try:
                for doc in documents:
                    # Convert publication_date string to datetime
                    pub_date = datetime.strptime(doc['publication_date'], '%Y-%m-%d')
                    
                    # Create document instance
                    db_doc = Document(
                        document_id=doc['document_id'],
                        source=doc['source'],
                        title=doc['title'],
                        document_type=doc['document_type'],
                        publication_date=pub_date,
                        metadata=doc['metadata']
                    )
                    
                    # Merge to handle both insert and update
                    session.merge(db_doc)
                
                await session.commit()
                self.logger.info(f"Stored {len(documents)} documents in PostgreSQL")
                
            except Exception as e:
                await session.rollback()
                raise StorageError(f"Failed to store documents: {str(e)}")

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Document data if found, None otherwise
        """
        if not self.SessionLocal:
            raise StorageError("Database connection not initialized")

        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Document).where(Document.document_id == document_id)
                )
                doc = result.scalar_one_or_none()
                
                if doc:
                    return {
                        "document_id": doc.document_id,
                        "source": doc.source,
                        "title": doc.title,
                        "document_type": doc.document_type,
                        "publication_date": doc.publication_date.strftime('%Y-%m-%d'),
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat(),
                        "updated_at": doc.updated_at.isoformat()
                    }
                return None
                
            except Exception as e:
                raise StorageError(f"Failed to retrieve document: {str(e)}")

    async def search_documents(
        self,
        source: Optional[str] = None,
        document_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search documents with filters.
        
        Args:
            source: Optional source filter
            document_type: Optional document type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Dict[str, Any]]: List of matching documents
        """
        if not self.SessionLocal:
            raise StorageError("Database connection not initialized")

        async with self.SessionLocal() as session:
            try:
                query = select(Document)
                
                # Apply filters
                if source:
                    query = query.where(Document.source == source)
                if document_type:
                    query = query.where(Document.document_type == document_type)
                if start_date:
                    query = query.where(Document.publication_date >= start_date)
                if end_date:
                    query = query.where(Document.publication_date <= end_date)
                
                # Apply pagination
                query = query.order_by(Document.publication_date.desc())
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                docs = result.scalars().all()
                
                return [
                    {
                        "document_id": doc.document_id,
                        "source": doc.source,
                        "title": doc.title,
                        "document_type": doc.document_type,
                        "publication_date": doc.publication_date.strftime('%Y-%m-%d'),
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat(),
                        "updated_at": doc.updated_at.isoformat()
                    }
                    for doc in docs
                ]
                
            except Exception as e:
                raise StorageError(f"Failed to search documents: {str(e)}")

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            bool: True if document was deleted, False if not found
        """
        if not self.SessionLocal:
            raise StorageError("Database connection not initialized")

        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    delete(Document).where(Document.document_id == document_id)
                )
                await session.commit()
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise StorageError(f"Failed to delete document: {str(e)}") 