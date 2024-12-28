"""Main FastAPI application module."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import yaml
from pathlib import Path
from dotenv import load_dotenv

from ingestion.acquisition.federal_register_ingestor import FederalRegisterIngestor
from ingestion.acquisition.far_dfars_ingestor import FarDfarsIngestor
from ingestion.standards.standards_ingestor import StandardsIngestor
from routers import document_routes, ingestion_routes, federal_register_routes
from utils.config_loader import load_config
from utils.logging import setup_logging

# Load environment variables
load_dotenv()

# Load configuration
config = load_config()

# Setup logging
logger = setup_logging(config.logging)

# Initialize FastAPI app
app = FastAPI(
    title="Data Ingestion and Processing API",
    description="API for ingesting and processing documents from various sources",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_routes.router, prefix="/api/v1")
app.include_router(ingestion_routes.router, prefix="/api/v1")
app.include_router(federal_register_routes.router)

# Initialize ingestors
federal_register_ingestor = FederalRegisterIngestor(config)
far_dfars_ingestor = FarDfarsIngestor(config)
standards_ingestor = StandardsIngestor(config)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(datetime.UTC).isoformat()}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Data Ingestion and Processing API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.post("/ingest/federal-register")
async def ingest_federal_register(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Trigger ingestion from Federal Register."""
    try:
        success = await federal_register_ingestor.ingest(
            start_date=start_date,
            end_date=end_date
        )
        return {"success": success, "message": "Federal Register ingestion completed"}
    except Exception as e:
        logger.error(f"Federal Register ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/far-dfars")
async def ingest_far_dfars(
    regulation_type: Optional[str] = Query(None, description="Regulation type (far/dfars)"),
    part_number: Optional[str] = Query(None, description="Part number to ingest")
):
    """Trigger ingestion from FAR/DFARS."""
    try:
        success = await far_dfars_ingestor.ingest(
            regulation_type=regulation_type,
            part_number=part_number
        )
        return {"success": success, "message": "FAR/DFARS ingestion completed"}
    except Exception as e:
        logger.error(f"FAR/DFARS ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/standards")
async def ingest_standards(
    source: str = Query(..., description="Standards source (nist/iso)"),
    category: Optional[str] = Query(None, description="Category filter")
):
    """Trigger ingestion from standards sources."""
    try:
        success = await standards_ingestor.ingest(
            source=source,
            category=category
        )
        return {"success": success, "message": f"Standards ingestion from {source} completed"}
    except Exception as e:
        logger.error(f"Standards ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def get_documents(
    source: Optional[str] = Query(None, description="Filter by source"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Page size")
):
    """Retrieve documents with optional filtering."""
    # TODO: Implement document retrieval from PostgreSQL
    return {"documents": [], "total": 0, "page": page, "page_size": page_size}


@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Retrieve a specific document by ID."""
    # TODO: Implement document retrieval from PostgreSQL
    raise HTTPException(status_code=404, detail="Document not found")


@app.get("/documents/{document_id}/relationships")
async def get_document_relationships(document_id: str):
    """Retrieve relationships for a specific document."""
    # TODO: Implement relationship retrieval from Neo4j
    raise HTTPException(status_code=404, detail="Document not found")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug
    ) 