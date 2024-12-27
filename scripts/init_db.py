"""Script to initialize database schemas for PostgreSQL and Neo4j."""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys
import os

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import load_config
from src.utils.logging import setup_logging
from src.storage.postgresql_connector import PostgreSQLConnector
from src.storage.neo4j_connector import Neo4jConnector


async def init_postgresql(config):
    """Initialize PostgreSQL schema."""
    try:
        connector = PostgreSQLConnector(config)
        await connector.initialize()
        
        # Create tables
        async with connector.engine.begin() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(255) UNIQUE NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    title TEXT NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    publication_date DATE NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
                CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
                CREATE INDEX IF NOT EXISTS idx_documents_publication_date ON documents(publication_date);
                
                CREATE TABLE IF NOT EXISTS document_content (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(255) REFERENCES documents(document_id) ON DELETE CASCADE,
                    content_type VARCHAR(50) NOT NULL,
                    content TEXT,
                    blob_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_document_content_document_id ON document_content(document_id);
            """)
        
        logging.info("PostgreSQL schema initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize PostgreSQL schema: {str(e)}")
        raise
    finally:
        await connector.cleanup()


async def init_neo4j(config):
    """Initialize Neo4j schema."""
    try:
        connector = Neo4jConnector(config)
        await connector.initialize()
        
        # Create constraints and indexes
        async with connector.driver.session() as session:
            await session.run("""
                CREATE CONSTRAINT document_id IF NOT EXISTS
                FOR (d:Document) REQUIRE d.document_id IS UNIQUE
            """)
            
            await session.run("""
                CREATE CONSTRAINT agency_id IF NOT EXISTS
                FOR (a:Agency) REQUIRE a.id IS UNIQUE
            """)
            
            await session.run("""
                CREATE CONSTRAINT regulation_id IF NOT EXISTS
                FOR (r:Regulation) REQUIRE r.regulation_id IS UNIQUE
            """)
            
            await session.run("""
                CREATE INDEX document_source IF NOT EXISTS
                FOR (d:Document) ON (d.source)
            """)
            
            await session.run("""
                CREATE INDEX document_type IF NOT EXISTS
                FOR (d:Document) ON (d.document_type)
            """)
        
        logging.info("Neo4j schema initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize Neo4j schema: {str(e)}")
        raise
    finally:
        await connector.cleanup()


async def main():
    """Main function to initialize all database schemas."""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    try:
        # Initialize PostgreSQL schema
        logging.info("Initializing PostgreSQL schema...")
        await init_postgresql(config)
        
        # Initialize Neo4j schema
        logging.info("Initializing Neo4j schema...")
        await init_neo4j(config)
        
        logging.info("Database initialization completed successfully")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 