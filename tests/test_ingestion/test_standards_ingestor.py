"""Tests for the standards ingestor implementation."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup

from src.ingestion.standards.standards_ingestor import StandardsIngestor
from src.utils.error_handling import DataIngestionError


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return {
        "standards": {
            "nist": {
                "base_url": "https://csrc.nist.gov/publications",
                "update_interval": 86400
            },
            "iso": {
                "base_url": "https://www.iso.org/standards",
                "update_interval": 86400
            }
        }
    }


@pytest.fixture
def mock_nist_html():
    """Create mock HTML content for NIST standards."""
    return """
    <div class="standard-item" data-standard-id="SP800-53">
        <h2 class="title">Security and Privacy Controls for Information Systems and Organizations</h2>
        <div class="date">2023-12-01</div>
        <div class="status">Final</div>
        <div class="category">Security</div>
        <div class="abstract">This publication provides a catalog of security and privacy controls.</div>
        <a href="/publication/800-53">View Details</a>
    </div>
    """


@pytest.fixture
def mock_iso_html():
    """Create mock HTML content for ISO standards."""
    return """
    <div class="standard-item" data-standard-id="ISO/IEC 27001">
        <h2 class="title">Information Security Management Systems</h2>
        <div class="date">2023-12-01</div>
        <div class="status">Published</div>
        <div class="committee">JTC 1/SC 27</div>
        <div class="abstract">This standard specifies requirements for information security management systems.</div>
        <a href="/standard/27001">View Details</a>
    </div>
    """


@pytest.fixture
async def standards_ingestor(mock_config):
    """Create a standards ingestor instance for testing."""
    ingestor = StandardsIngestor(mock_config)
    await ingestor.initialize()
    yield ingestor
    await ingestor.cleanup()


@pytest.mark.asyncio
async def test_initialize(standards_ingestor):
    """Test initialization of the standards ingestor."""
    assert standards_ingestor.session is not None
    assert standards_ingestor.config == mock_config


@pytest.mark.asyncio
async def test_fetch_nist_standards(standards_ingestor, mock_nist_html):
    """Test fetching NIST standards."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = mock_nist_html
        mock_get.return_value.__aenter__.return_value = mock_response

        documents = await standards_ingestor._fetch_nist_standards()
        
        assert len(documents) == 1
        doc = documents[0]
        assert doc["document_id"] == "SP800-53"
        assert doc["title"] == "Security and Privacy Controls for Information Systems and Organizations"
        assert doc["source"] == "nist"
        assert doc["document_type"] == "standard"
        assert "status" in doc["metadata"]
        assert "category" in doc["metadata"]
        assert "abstract" in doc["metadata"]


@pytest.mark.asyncio
async def test_fetch_iso_standards(standards_ingestor, mock_iso_html):
    """Test fetching ISO standards."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = mock_iso_html
        mock_get.return_value.__aenter__.return_value = mock_response

        documents = await standards_ingestor._fetch_iso_standards()
        
        assert len(documents) == 1
        doc = documents[0]
        assert doc["document_id"] == "ISO/IEC 27001"
        assert doc["title"] == "Information Security Management Systems"
        assert doc["source"] == "iso"
        assert doc["document_type"] == "standard"
        assert "status" in doc["metadata"]
        assert "technical_committee" in doc["metadata"]
        assert "abstract" in doc["metadata"]


@pytest.mark.asyncio
async def test_fetch_data_invalid_source(standards_ingestor):
    """Test fetching data from an invalid source."""
    with pytest.raises(DataIngestionError) as exc_info:
        await standards_ingestor.fetch_data("invalid_source")
    assert "Unsupported standards source" in str(exc_info.value)


@pytest.mark.asyncio
async def test_transform_data(standards_ingestor):
    """Test transforming standards documents."""
    documents = [
        {
            "document_id": "TEST-001",
            "title": "Test Standard",
            "publication_date": "2023-12-01",
            "source": "nist",
            "document_type": "standard"
        }
    ]

    transformed = await standards_ingestor.transform_data(documents)
    
    assert len(transformed) == 1
    doc = transformed[0]
    assert doc["publication_date"] == "2023-12-01"
    assert "created_at" in doc
    assert "updated_at" in doc


@pytest.mark.asyncio
async def test_validate_data_valid(standards_ingestor):
    """Test validating valid standards documents."""
    documents = [
        {
            "document_id": "TEST-001",
            "title": "Test Standard",
            "publication_date": "2023-12-01",
            "source": "nist",
            "document_type": "standard"
        }
    ]

    validated = await standards_ingestor.validate_data(documents)
    
    assert len(validated) == 1
    assert validated[0] == documents[0]


@pytest.mark.asyncio
async def test_validate_data_invalid(standards_ingestor):
    """Test validating invalid standards documents."""
    documents = [
        {
            "document_id": "TEST-001",
            # Missing required fields
            "source": "invalid_source"
        }
    ]

    validated = await standards_ingestor.validate_data(documents)
    
    assert len(validated) == 0


@pytest.mark.asyncio
async def test_ingest_pipeline(standards_ingestor, mock_nist_html):
    """Test the complete ingestion pipeline."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = mock_nist_html
        mock_get.return_value.__aenter__.return_value = mock_response

        success = await standards_ingestor.ingest("nist")
        
        assert success is True 