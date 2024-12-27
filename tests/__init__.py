"""
Test suite for the data ingestion and processing service.
"""

import pytest
import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure pytest
pytest_plugins = [
    "pytest_asyncio",
] 