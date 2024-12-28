"""Base ingestor class for all data ingestion."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from utils.logging import LoggerMixin
from utils.error_handling import DataIngestionError, retry


class BaseIngestor(ABC, LoggerMixin):
    """
    Abstract base class for all data ingestors.
    Defines the interface that all ingestors must implement.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ingestor with configuration.
        
        Args:
            config: Configuration dictionary for the ingestor
        """
        self.config = config
        self.logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    async def fetch_data(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Fetch data from the source.
        
        Args:
            **kwargs: Additional arguments for the fetch operation
            
        Returns:
            List[Dict[str, Any]]: List of fetched data items
            
        Raises:
            DataIngestionError: If data fetching fails
        """
        pass

    @abstractmethod
    async def transform_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform fetched data into the standard format.
        
        Args:
            data: Raw data from the source
            
        Returns:
            List[Dict[str, Any]]: Transformed data
            
        Raises:
            DataIngestionError: If transformation fails
        """
        pass

    @abstractmethod
    async def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate transformed data.
        
        Args:
            data: Transformed data to validate
            
        Returns:
            List[Dict[str, Any]]: Validated data
            
        Raises:
            DataIngestionError: If validation fails
        """
        pass

    @abstractmethod
    async def store_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Store validated data.
        
        Args:
            data: Validated data to store
            
        Raises:
            DataIngestionError: If storage operation fails
        """
        pass

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(DataIngestionError,))
    async def ingest(self, **kwargs: Any) -> None:
        """
        Execute the complete ingestion pipeline.
        
        Args:
            **kwargs: Additional arguments for the ingestion process
            
        Raises:
            DataIngestionError: If any step of the pipeline fails
        """
        try:
            self.logger.info(f"Starting ingestion process for {self.__class__.__name__}")
            
            # Fetch data
            raw_data = await self.fetch_data(**kwargs)
            self.logger.info(f"Fetched {len(raw_data)} items")
            
            # Transform data
            transformed_data = await self.transform_data(raw_data)
            self.logger.info(f"Transformed {len(transformed_data)} items")
            
            # Validate data
            validated_data = await self.validate_data(transformed_data)
            self.logger.info(f"Validated {len(validated_data)} items")
            
            # Store data
            await self.store_data(validated_data)
            self.logger.info("Data storage completed")
            
        except Exception as e:
            self.logger.error(f"Ingestion failed: {str(e)}")
            raise DataIngestionError(f"Ingestion pipeline failed: {str(e)}")

    async def cleanup(self) -> None:
        """
        Clean up resources after ingestion.
        Override this method if cleanup is needed.
        """
        pass 