"""PostgreSQL database connector."""

import asyncpg
from typing import Dict, Any, List, Optional
import os
from datetime import datetime

from utils.logging import LoggerMixin
from utils.error_handling import StorageError

class PostgreSQLConnector(LoggerMixin):
    """PostgreSQL database connector class."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize PostgreSQL connector with configuration."""
        super().__init__()
        self.config = config or {
            "host": os.getenv("POSTGRES_HOST"),
            "port": int(os.getenv("POSTGRES_PORT", "34605")),
            "database": os.getenv("POSTGRES_DATABASE"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "ssl": "require"
        }
        self.pool = None

    async def initialize(self):
        """Initialize the database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(**self.config)
            self.logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            raise StorageError(f"Failed to initialize PostgreSQL connection: {str(e)}")

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            self.logger.info("PostgreSQL connection pool closed") 