import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.ingestion.acquisition.federal_register_ingestor import FederalRegisterIngestor
from src.utils.error_handling import DataIngestionError


@pytest.fixture
def config():
    return {
        "data_sources": {
            "federal_register": {
                "api_url": "https://www.federalregister.gov/api/v1"
            }
        }
    }


@pytest.fixture
def mock_response():
    return {
        "count": 2,
        "results": [
            {
                "document_number": "2023-001",
                "title": "Test Document 1",
                "document_type": "rule",
                "publication_date": "2023-12-01",
                "html_url": "https://example.com/doc1",
                "pdf_url": "https://example.com/doc1.pdf",
                "abstract": "Test abstract 1",
                "agencies": [
                    {
                        "name": "Test Agency 1",
                        "id": "TA1"
                    }
                ],
                "regulation_id_numbers": ["TEST-0001"]
            },
            {
                "document_number": "2023-002",
                "title": "Test Document 2",
                "document_type": "notice",
                "publication_date": "2023-12-02",
                "html_url": "https://example.com/doc2",
                "pdf_url": "https://example.com/doc2.pdf",
                "abstract": "Test abstract 2",
                "agencies": [
                    {
                        "name": "Test Agency 2",
                        "id": "TA2"
                    }
                ],
                "regulation_id_numbers": ["TEST-0002"]
            }
        ],
        "next_page_url": None
    }


@pytest.mark.asyncio
async def test_fetch_data_success(config, mock_response):
    """Test successful data fetching from Federal Register API."""
    ingestor = FederalRegisterIngestor(config)
    
    # Mock aiohttp ClientSession
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.status = 200
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        documents = await ingestor.fetch_data()
        
        assert len(documents) == 2
        assert documents[0]["document_number"] == "2023-001"
        assert documents[1]["document_number"] == "2023-002"


@pytest.mark.asyncio
async def test_fetch_data_api_error(config):
    """Test handling of API errors during data fetching."""
    ingestor = FederalRegisterIngestor(config)
    
    # Mock aiohttp ClientSession with error response
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.status = 500
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(DataIngestionError):
            await ingestor.fetch_data()


@pytest.mark.asyncio
async def test_transform_data(config, mock_response):
    """Test document transformation."""
    ingestor = FederalRegisterIngestor(config)
    
    transformed_docs = await ingestor.transform_data(mock_response["results"])
    
    assert len(transformed_docs) == 2
    
    doc = transformed_docs[0]
    assert doc["source"] == "federal_register"
    assert doc["document_id"] == "2023-001"
    assert doc["title"] == "Test Document 1"
    assert doc["document_type"] == "rule"
    assert doc["publication_date"] == "2023-12-01"
    assert "processed_at" in doc
    
    metadata = doc["metadata"]
    assert metadata["html_url"] == "https://example.com/doc1"
    assert metadata["pdf_url"] == "https://example.com/doc1.pdf"
    assert metadata["abstract"] == "Test abstract 1"
    assert len(metadata["agencies"]) == 1
    assert metadata["agencies"][0]["name"] == "Test Agency 1"


@pytest.mark.asyncio
async def test_validate_data(config):
    """Test document validation."""
    ingestor = FederalRegisterIngestor(config)
    
    valid_docs = [
        {
            "document_id": "2023-001",
            "source": "federal_register",
            "title": "Test Document",
            "document_type": "rule",
            "publication_date": "2023-12-01",
            "metadata": {
                "html_url": "https://example.com/doc1",
                "pdf_url": "https://example.com/doc1.pdf",
                "abstract": "Test abstract",
                "agencies": [
                    {
                        "name": "Test Agency",
                        "id": "TA1"
                    }
                ]
            }
        }
    ]
    
    validated_docs = await ingestor.validate_data(valid_docs)
    assert len(validated_docs) == 1
    assert validated_docs[0]["document_id"] == "2023-001"


@pytest.mark.asyncio
async def test_validate_data_invalid_document(config):
    """Test validation of invalid documents."""
    ingestor = FederalRegisterIngestor(config)
    
    invalid_docs = [
        {
            # Missing required fields
            "document_id": "2023-001",
            "title": "Test Document"
        }
    ]
    
    validated_docs = await ingestor.validate_data(invalid_docs)
    assert len(validated_docs) == 0


@pytest.mark.asyncio
async def test_ingest_pipeline(config, mock_response):
    """Test the complete ingestion pipeline."""
    ingestor = FederalRegisterIngestor(config)
    
    # Mock fetch_data
    ingestor.fetch_data = AsyncMock(return_value=mock_response["results"])
    
    # Mock store_data
    ingestor.store_data = AsyncMock()
    
    await ingestor.ingest()
    
    # Verify the pipeline steps were called
    ingestor.fetch_data.assert_called_once()
    assert ingestor.store_data.call_count == 1 