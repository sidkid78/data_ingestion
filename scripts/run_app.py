"""Script to run the FastAPI application."""

import uvicorn
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys
import os

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import load_config
from src.utils.logging import setup_logging


def main():
    """Main function to run the FastAPI application."""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    try:
        # Run the application
        logging.info("Starting FastAPI application...")
        uvicorn.run(
            "src.main:app",
            host=config.api.host,
            port=config.api.port,
            reload=config.api.debug,
            log_level="info" if config.api.debug else "warning"
        )
    except Exception as e:
        logging.error(f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 