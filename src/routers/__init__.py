"""
API routers for the data ingestion and processing service.
"""

from . import document_routes
from . import ingestion_routes

__all__ = ["document_routes", "ingestion_routes"] 