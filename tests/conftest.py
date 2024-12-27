import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock

from src.utils.config_loader import AppConfig, APIConfig, StorageConfig, ProcessingConfig, ValidationConfig, LoggingConfig


@pytest.fixture
def mock_config() -> AppConfig:
    """Create a mock configuration for testing."""
    return AppConfig(
        api=APIConfig(
            host="0.0.0.0",
            port=8000,
            debug=True,
            prefix="/api/v1"
        ),
        storage=StorageConfig(
            azure_blob={
                "container_name": "test-container",
                "connection_string_env": "TEST_STORAGE_CONNECTION_STRING"
            },
            postgresql={
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user_env": "TEST_PG_USER",
                "password_env": "TEST_PG_PASSWORD"
            },
            neo4j={
                "uri": "bolt://localhost:7687",
                "user_env": "TEST_NEO4J_USER",
                "password_env": "TEST_NEO4J_PASSWORD"
            }
        ),
        processing=ProcessingConfig(
            max_workers=2,
            batch_size=50,
            retry_attempts=2,
            retry_delay=1
        ),
        validation=ValidationConfig(
            yaml={
                "strict_mode": True,
                "allow_duplicates": False
            },
            metadata={
                "required_fields": ["title", "document_type", "publication_date", "source"],
                "controlled_vocabularies": {
                    "document_types": ["rule", "notice"],
                    "sources": ["federal_register", "far_dfars"]
                }
            }
        ),
        logging=LoggingConfig(
            level="INFO",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            file="logs/test.log"
        ),
        data_sources={
            "federal_register": {
                "api_url": "https://www.federalregister.gov/api/v1",
                "update_interval": 3600
            },
            "far_dfars": {
                "base_url": "https://www.acquisition.gov",
                "update_interval": 86400
            }
        }
    )


@pytest.fixture
def mock_document() -> Dict[str, Any]:
    """Create a mock document for testing."""
    return {
        "document_id": "TEST-DOC-001",
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
            ],
            "regulation_id_numbers": ["TEST-0001"],
            "dates": {}
        },
        "created_at": "2023-12-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z"
    }


@pytest.fixture
def mock_relationships() -> Dict[str, list]:
    """Create mock relationships for testing."""
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
        ],
        "REFERENCES": [
            {
                "type": "REFERENCES",
                "node": {
                    "regulation_id": "TEST-0001"
                },
                "created_at": "2023-12-01T00:00:00Z"
            }
        ]
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return AsyncMock(
        info=AsyncMock(),
        error=AsyncMock(),
        warning=AsyncMock(),
        debug=AsyncMock()
    ) 