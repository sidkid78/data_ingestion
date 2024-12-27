import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.ingestion.acquisition.federal_register_ingestor import FederalRegisterIngestor
from src.ingestion.acquisition.far_dfars_ingestor import FarDfarsIngestor


@pytest.fixture
def mock_federal_register_ingestor():
    ingestor = AsyncMock(spec=FederalRegisterIngestor)
    ingestor.ingest = AsyncMock()
    return ingestor


@pytest.fixture
def mock_far_dfars_ingestor():
    ingestor = AsyncMock(spec=FarDfarsIngestor)
    ingestor.ingest = AsyncMock()
    return ingestor


@pytest.fixture
def client(mock_federal_register_ingestor, mock_far_dfars_ingestor):
    """Create test client with mocked dependencies."""
    
    async def mock_get_ingestors():
        return {
            "federal_register": mock_federal_register_ingestor,
            "far_dfars": mock_far_dfars_ingestor
        }
    
    app.dependency_overrides = {
        "src.routers.ingestion_routes.get_ingestors": mock_get_ingestors
    }
    
    return TestClient(app)


def test_ingest_federal_register_success(client, mock_federal_register_ingestor):
    """Test successful Federal Register ingestion."""
    response = client.post(
        "/api/v1/ingest/federal-register",
        params={
            "start_date": "2023-12-01",
            "end_date": "2023-12-31",
            "document_type": "rule"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    assert "federal_register" in response.json()["task_id"]
    assert "2023-12-01" in response.json()["message"]
    assert "2023-12-31" in response.json()["message"]


def test_ingest_federal_register_invalid_date(client):
    """Test Federal Register ingestion with invalid date."""
    response = client.post(
        "/api/v1/ingest/federal-register",
        params={
            "start_date": "invalid-date"
        }
    )
    
    assert response.status_code == 400
    assert "invalid date format" in response.json()["detail"].lower()


def test_ingest_federal_register_future_date(client):
    """Test Federal Register ingestion with future end date."""
    future_date = (datetime.now().date() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = client.post(
        "/api/v1/ingest/federal-register",
        params={
            "end_date": future_date
        }
    )
    
    assert response.status_code == 200  # Future dates are allowed but will be capped at today


def test_ingest_federal_register_invalid_date_range(client):
    """Test Federal Register ingestion with invalid date range."""
    response = client.post(
        "/api/v1/ingest/federal-register",
        params={
            "start_date": "2023-12-31",
            "end_date": "2023-12-01"
        }
    )
    
    assert response.status_code == 400
    assert "start date must be before end date" in response.json()["detail"].lower()


def test_ingest_far_dfars_success(client, mock_far_dfars_ingestor):
    """Test successful FAR/DFARS ingestion."""
    response = client.post(
        "/api/v1/ingest/far-dfars",
        params={
            "regulation_type": "far",
            "part_number": "1"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    assert "far_dfars" in response.json()["task_id"]
    assert "FAR" in response.json()["message"]
    assert "Part 1" in response.json()["message"]


def test_ingest_far_dfars_invalid_regulation_type(client):
    """Test FAR/DFARS ingestion with invalid regulation type."""
    response = client.post(
        "/api/v1/ingest/far-dfars",
        params={
            "regulation_type": "invalid"
        }
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_ingest_far_dfars_both_regulations(client, mock_far_dfars_ingestor):
    """Test FAR/DFARS ingestion for both regulations."""
    response = client.post(
        "/api/v1/ingest/far-dfars",
        params={
            "regulation_type": "both"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    assert "Started FAR/DFARS ingestion" in response.json()["message"]


@pytest.mark.asyncio
async def test_run_ingestion_success():
    """Test successful ingestion task execution."""
    from src.routers.ingestion_routes import run_ingestion
    
    mock_ingestor = AsyncMock()
    mock_ingestors = {"test_ingestor": mock_ingestor}
    
    await run_ingestion("test_ingestor", mock_ingestors, param1="value1")
    
    mock_ingestor.ingest.assert_called_once_with(param1="value1")


@pytest.mark.asyncio
async def test_run_ingestion_error():
    """Test ingestion task error handling."""
    from src.routers.ingestion_routes import run_ingestion
    
    mock_ingestor = AsyncMock()
    mock_ingestor.ingest.side_effect = Exception("Test error")
    mock_ingestors = {"test_ingestor": mock_ingestor}
    
    with pytest.raises(Exception) as exc_info:
        await run_ingestion("test_ingestor", mock_ingestors)
    
    assert "Test error" in str(exc_info.value) 