import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.storage.postgresql_connector import PostgreSQLConnector
from src.storage.neo4j_connector import Neo4jConnector


@pytest.fixture
def mock_pg_connector():
    connector = AsyncMock(spec=PostgreSQLConnector)
    connector.initialize = AsyncMock()
    connector.close = AsyncMock()
    return connector


@pytest.fixture
def mock_neo4j_connector():
    connector = AsyncMock(spec=Neo4jConnector)
    connector.initialize = AsyncMock()
    connector.close = AsyncMock()
    return connector


@pytest.fixture
def mock_document():
    return {
        "document_id": "TEST-DOC-001",
        "source": "federal_register",
        "title": "Test Document",
        "document_type": "rule",
        "publication_date": "2023-12-01",
        "metadata": {
            "html_url": "https://example.com/doc1",
            "abstract": "Test abstract"
        },
        "created_at": "2023-12-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z"
    }


@pytest.fixture
def mock_relationships():
    return {
        "ISSUED_BY": [
            {
                "type": "ISSUED_BY",
                "node": {
                    "name": "Test Agency",
                    "id": "TA1"
                },
                "created_at": "2023-12-01T00:00:00Z"
            }
        ]
    }


@pytest.fixture
def client(mock_pg_connector, mock_neo4j_connector):
    """Create test client with mocked dependencies."""
    
    async def mock_get_db():
        return {
            "pg": mock_pg_connector,
            "neo4j": mock_neo4j_connector
        }
    
    app.dependency_overrides = {
        "src.routers.document_routes.get_db": mock_get_db
    }
    
    return TestClient(app)


def test_list_documents_success(client, mock_pg_connector, mock_document):
    """Test successful document listing."""
    mock_pg_connector.search_documents = AsyncMock(return_value=[mock_document])
    
    response = client.get("/api/v1/documents")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["document_id"] == mock_document["document_id"]


def test_list_documents_with_filters(client, mock_pg_connector, mock_document):
    """Test document listing with filters."""
    mock_pg_connector.search_documents = AsyncMock(return_value=[mock_document])
    
    response = client.get(
        "/api/v1/documents",
        params={
            "source": "federal_register",
            "document_type": "rule",
            "start_date": "2023-12-01",
            "end_date": "2023-12-31"
        }
    )
    
    assert response.status_code == 200
    mock_pg_connector.search_documents.assert_called_once()
    call_kwargs = mock_pg_connector.search_documents.call_args.kwargs
    assert call_kwargs["source"] == "federal_register"
    assert call_kwargs["document_type"] == "rule"


def test_get_document_success(client, mock_pg_connector, mock_document):
    """Test successful single document retrieval."""
    mock_pg_connector.get_document = AsyncMock(return_value=mock_document)
    
    response = client.get(f"/api/v1/documents/{mock_document['document_id']}")
    
    assert response.status_code == 200
    assert response.json()["document_id"] == mock_document["document_id"]


def test_get_document_not_found(client, mock_pg_connector):
    """Test document not found error."""
    mock_pg_connector.get_document = AsyncMock(return_value=None)
    
    response = client.get("/api/v1/documents/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_document_relationships(
    client,
    mock_pg_connector,
    mock_neo4j_connector,
    mock_document,
    mock_relationships
):
    """Test document relationships retrieval."""
    mock_pg_connector.get_document = AsyncMock(return_value=mock_document)
    mock_neo4j_connector.get_document_relationships = AsyncMock(return_value=mock_relationships)
    
    response = client.get(f"/api/v1/documents/{mock_document['document_id']}/relationships")
    
    assert response.status_code == 200
    assert response.json()["document_id"] == mock_document["document_id"]
    assert "ISSUED_BY" in response.json()["relationships"]


def test_get_related_documents(
    client,
    mock_pg_connector,
    mock_neo4j_connector,
    mock_document
):
    """Test related documents retrieval."""
    mock_pg_connector.get_document = AsyncMock(return_value=mock_document)
    mock_neo4j_connector.find_related_documents = AsyncMock(return_value=[
        {
            "document": {"document_id": "TEST-DOC-002"},
            "relationships": []
        }
    ])
    
    response = client.get(
        f"/api/v1/documents/{mock_document['document_id']}/related",
        params={"max_depth": 2}
    )
    
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_document_success(
    client,
    mock_pg_connector,
    mock_neo4j_connector
):
    """Test successful document deletion."""
    mock_pg_connector.delete_document = AsyncMock(return_value=True)
    mock_neo4j_connector.delete_document_node = AsyncMock()
    
    response = client.delete("/api/v1/documents/TEST-DOC-001")
    
    assert response.status_code == 204
    mock_pg_connector.delete_document.assert_called_once()
    mock_neo4j_connector.delete_document_node.assert_called_once()


def test_delete_document_not_found(
    client,
    mock_pg_connector,
    mock_neo4j_connector
):
    """Test document not found during deletion."""
    mock_pg_connector.delete_document = AsyncMock(return_value=False)
    
    response = client.delete("/api/v1/documents/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_neo4j_connector.delete_document_node.assert_not_called() 