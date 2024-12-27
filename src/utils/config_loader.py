from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    prefix: str = Field(default="/api/v1")


class StorageConfig(BaseModel):
    azure_blob: Dict[str, str]
    postgresql: Dict[str, Any]
    neo4j: Dict[str, str]


class ProcessingConfig(BaseModel):
    max_workers: int
    batch_size: int
    retry_attempts: int
    retry_delay: int


class ValidationConfig(BaseModel):
    yaml: Dict[str, bool]
    metadata: Dict[str, Any]


class LoggingConfig(BaseModel):
    level: str
    format: str
    file: str


class AppConfig(BaseModel):
    api: APIConfig
    storage: StorageConfig
    processing: ProcessingConfig
    validation: ValidationConfig
    logging: LoggingConfig
    data_sources: Dict[str, Any]


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load and validate application configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file. Defaults to config/app_config.yaml
        
    Returns:
        AppConfig: Validated configuration object
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValidationError: If configuration is invalid
    """
    if config_path is None:
        config_path = Path("config/app_config.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    return AppConfig(**config_dict) 