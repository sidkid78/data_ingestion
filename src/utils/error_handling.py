import asyncio
import time
from functools import wraps
from typing import Any, Callable, Type, Union
import logging
from fastapi import HTTPException

# Custom Exceptions
class DataIngestionError(Exception):
    """Base exception for data ingestion errors."""
    pass

class ValidationError(DataIngestionError):
    """Raised when data validation fails."""
    pass

class StorageError(DataIngestionError):
    """Raised when storage operations fail."""
    pass

class ProcessingError(DataIngestionError):
    """Raised when data processing fails."""
    pass

class ConfigurationError(DataIngestionError):
    """Raised when configuration is invalid or missing."""
    pass

# Error Handler Decorator
def handle_exceptions(
    logger: logging.Logger,
    error_map: dict[Type[Exception], Union[Type[Exception], Callable[[Exception], Exception]]] = None
) -> Callable:
    """
    Decorator for handling exceptions in async and sync functions.
    
    Args:
        logger: Logger instance for error logging
        error_map: Mapping of caught exceptions to raised exceptions
        
    Returns:
        Callable: Decorated function
    """
    if error_map is None:
        error_map = {
            ValidationError: lambda e: HTTPException(status_code=400, detail=str(e)),
            StorageError: lambda e: HTTPException(status_code=500, detail=str(e)),
            ProcessingError: lambda e: HTTPException(status_code=500, detail=str(e)),
            ConfigurationError: lambda e: HTTPException(status_code=500, detail=str(e)),
        }

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {str(e)}")
                for exc_type, handler in error_map.items():
                    if isinstance(e, exc_type):
                        if callable(handler):
                            raise handler(e)
                        raise handler(detail=str(e))
                raise HTTPException(status_code=500, detail="Internal server error")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {str(e)}")
                for exc_type, handler in error_map.items():
                    if isinstance(e, exc_type):
                        if callable(handler):
                            raise handler(e)
                        raise handler(detail=str(e))
                raise HTTPException(status_code=500, detail="Internal server error")

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Retry Decorator
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for retrying operations that may fail.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    continue
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    continue
            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 