import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup

from src.ingestion.acquisition.far_dfars_ingestor import FarDfarsIngestor
from src.utils.error_handling import DataIngestionError


@pytest.fixture
def config():
    return {
        "data_sources": {
            "far_dfars": {
                "base_url": "https://www.acquisition.gov"
            }
        }
    }


@pytest.fixture
def mock_far_index_html():
    return """
    <html>
        <body>
            <div class="parts-list">
                <a href="/far/part-1">Part 1 - Federal Acquisition Regulations System</a>
                <a href="/far/part-2">Part 2 - Definitions of Words and Terms</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_far_part_html():
    return """
    <html>
        <body>
            <h1>Part 1 - Federal Acquisition Regulations System</h1>
            <div class="regulation-content">
                <div class="subpart">
                    <h2>Subpart 1.1 - Purpose, Authority, Issuance</h2>
                </div>
                <div class="section">
                    <span class="section-number">1.101</span>
                    <span class="section-title">Purpose</span>
                    <div class="section-content">
                        The Federal Acquisition Regulations System is established...
                    </div>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.mark.asyncio
async def test_fetch_data_success(config, mock_far_index_html, mock_far_part_html):
    """Test successful data fetching from acquisition.gov."""
    ingestor = FarDfarsIngestor(config)
    
    # Mock aiohttp ClientSession
    mock_session = AsyncMock()
    
    # Mock index page response
    mock_index_response = AsyncMock()
    mock_index_response.status = 200
    mock_index_response.text = AsyncMock(return_value=mock_far_index_html)
    
    # Mock part page response
    mock_part_response = AsyncMock()
    mock_part_response.status = 200
    mock_part_response.text = AsyncMock(return_value=mock_far_part_html)
    
    # Set up session get responses
    async def mock_get(url):
        if "/far" in url and "part-" not in url:
            return mock_index_response
        return mock_part_response
    
    mock_session.get = AsyncMock(side_effect=mock_get)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        documents = await ingestor.fetch_data(regulation_type="far")
        
        assert len(documents) == 2
        assert documents[0]["document_number"] == "FAR-PART-1"
        assert documents[1]["document_number"] == "FAR-PART-2"


@pytest.mark.asyncio
async def test_fetch_data_with_part_filter(config, mock_far_index_html, mock_far_part_html):
    """Test fetching specific part number."""
    ingestor = FarDfarsIngestor(config)
    
    mock_session = AsyncMock()
    mock_index_response = AsyncMock()
    mock_index_response.status = 200
    mock_index_response.text = AsyncMock(return_value=mock_far_index_html)
    
    mock_part_response = AsyncMock()
    mock_part_response.status = 200
    mock_part_response.text = AsyncMock(return_value=mock_far_part_html)
    
    async def mock_get(url):
        if "/far" in url and "part-" not in url:
            return mock_index_response
        return mock_part_response
    
    mock_session.get = AsyncMock(side_effect=mock_get)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        documents = await ingestor.fetch_data(regulation_type="far", part_number="1")
        
        assert len(documents) == 1
        assert documents[0]["document_number"] == "FAR-PART-1"


@pytest.mark.asyncio
async def test_transform_data(config):
    """Test document transformation."""
    ingestor = FarDfarsIngestor(config)
    
    raw_docs = [
        {
            "document_number": "FAR-PART-1",
            "title": "Federal Acquisition Regulations System",
            "document_type": "far",
            "publication_date": "2023-12-01",
            "html_url": "https://www.acquisition.gov/far/part-1",
            "content": "The Federal Acquisition Regulations System is established...",
            "part_number": "1",
            "subparts": [
                {
                    "title": "Subpart 1.1 - Purpose, Authority, Issuance",
                    "sections": [
                        {
                            "number": "1.101",
                            "title": "Purpose",
                            "content": "The Federal Acquisition Regulations System..."
                        }
                    ]
                }
            ]
        }
    ]
    
    transformed_docs = await ingestor.transform_data(raw_docs)
    
    assert len(transformed_docs) == 1
    doc = transformed_docs[0]
    assert doc["source"] == "far_dfars"
    assert doc["document_id"] == "FAR-PART-1"
    assert doc["document_type"] == "far"
    assert "processed_at" in doc
    assert "subparts" in doc["metadata"]
    assert len(doc["metadata"]["subparts"]) == 1


@pytest.mark.asyncio
async def test_validate_data(config):
    """Test document validation."""
    ingestor = FarDfarsIngestor(config)
    
    valid_docs = [
        {
            "document_id": "FAR-PART-1",
            "source": "far_dfars",
            "title": "Federal Acquisition Regulations System",
            "document_type": "far",
            "publication_date": "2023-12-01",
            "metadata": {
                "html_url": "https://www.acquisition.gov/far/part-1",
                "part_number": "1",
                "subparts": [
                    {
                        "title": "Subpart 1.1",
                        "sections": []
                    }
                ]
            }
        }
    ]
    
    validated_docs = await ingestor.validate_data(valid_docs)
    assert len(validated_docs) == 1
    assert validated_docs[0]["document_id"] == "FAR-PART-1"


@pytest.mark.asyncio
async def test_validate_data_invalid_document(config):
    """Test validation of invalid documents."""
    ingestor = FarDfarsIngestor(config)
    
    invalid_docs = [
        {
            # Missing required fields
            "document_id": "FAR-PART-1",
            "title": "Test Document"
        }
    ]
    
    validated_docs = await ingestor.validate_data(invalid_docs)
    assert len(validated_docs) == 0


@pytest.mark.asyncio
async def test_extract_subparts():
    """Test subpart extraction from HTML."""
    ingestor = FarDfarsIngestor({"data_sources": {"far_dfars": {"base_url": ""}}})
    
    html = """
    <div>
        <div class="subpart">
            <h2>Subpart 1.1 - Purpose</h2>
        </div>
        <div class="section">
            <span class="section-number">1.101</span>
            <span class="section-title">Purpose</span>
            <div class="content">Section content</div>
        </div>
    </div>
    """
    
    soup = BeautifulSoup(html, "lxml")
    subparts = await ingestor._extract_subparts(soup)
    
    assert len(subparts) == 1
    assert subparts[0]["title"] == "Subpart 1.1 - Purpose"
    assert len(subparts[0]["sections"]) == 1
    assert subparts[0]["sections"][0]["number"] == "1.101" 