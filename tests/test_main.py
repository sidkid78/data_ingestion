"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to the Data Ingestion and Processing API"
    assert "docs_url" in data
    assert "redoc_url" in data


@patch("src.main.federal_register_ingestor")
def test_ingest_federal_register_success(mock_ingestor, client):
    """Test successful Federal Register ingestion."""
    mock_ingestor.ingest = AsyncMock(return_value=True)
    
    response = client.post("/ingest/federal-register", params={
        "start_date": "2023-12-01",
        "end_date": "2023-12-31"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Federal Register ingestion completed" in data["message"]


@patch("src.main.federal_register_ingestor")
def test_ingest_federal_register_failure(mock_ingestor, client):
    """Test failed Federal Register ingestion."""
    mock_ingestor.ingest = AsyncMock(side_effect=Exception("API Error"))
    
    response = client.post("/ingest/federal-register")
    
    assert response.status_code == 500
    assert "API Error" in response.json()["detail"]


@patch("src.main.far_dfars_ingestor")
def test_ingest_far_dfars_success(mock_ingestor, client):
    """Test successful FAR/DFARS ingestion."""
    mock_ingestor.ingest = AsyncMock(return_value=True)
    
    response = client.post("/ingest/far-dfars", params={
        "regulation_type": "far",
        "part_number": "52"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "FAR/DFARS ingestion completed" in data["message"]


@patch("src.main.far_dfars_ingestor")
def test_ingest_far_dfars_failure(mock_ingestor, client):
    """Test failed FAR/DFARS ingestion."""
    mock_ingestor.ingest = AsyncMock(side_effect=Exception("Scraping Error"))
    
    response = client.post("/ingest/far-dfars")
    
    assert response.status_code == 500
    assert "Scraping Error" in response.json()["detail"]


@patch("src.main.standards_ingestor")
def test_ingest_standards_success(mock_ingestor, client):
    """Test successful standards ingestion."""
    mock_ingestor.ingest = AsyncMock(return_value=True)
    
    response = client.post("/ingest/standards", params={
        "source": "nist",
        "category": "security"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Standards ingestion from nist completed" in data["message"]


@patch("src.main.standards_ingestor")
def test_ingest_standards_failure(mock_ingestor, client):
    """Test failed standards ingestion."""
    mock_ingestor.ingest = AsyncMock(side_effect=Exception("Invalid Source"))
    
    response = client.post("/ingest/standards", params={"source": "invalid"})
    
    assert response.status_code == 500
    assert "Invalid Source" in response.json()["detail"]


def test_get_documents(client):
    """Test retrieving documents."""
    response = client.get("/documents", params={
        "source": "federal_register",
        "document_type": "rule",
        "start_date": "2023-12-01",
        "end_date": "2023-12-31",
        "page": 1,
        "page_size": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


def test_get_document_not_found(client):
    """Test retrieving a non-existent document."""
    response = client.get("/documents/non-existent-id")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_get_document_relationships_not_found(client):
    """Test retrieving relationships for a non-existent document."""
    response = client.get("/documents/non-existent-id/relationships")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"] 