import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from .config_loader import LoggingConfig


def setup_logging(config: LoggingConfig, logger_name: Optional[str] = None) -> logging.Logger:
    """
    Set up logging with rotation and structured format.
    
    Args:
        config: Logging configuration
        logger_name: Optional name for the logger. Defaults to root logger if None.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(config.level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create handlers
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(config.format))
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.format))
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Name of the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capability to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger 