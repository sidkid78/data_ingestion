"""Script to run the test suite."""

import pytest
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
    """Main function to run the test suite."""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    try:
        # Run the tests
        logging.info("Running test suite...")
        args = [
            "tests",
            "-v",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-p", "no:warnings"
        ]
        
        # Add additional arguments from command line
        if len(sys.argv) > 1:
            args.extend(sys.argv[1:])
        
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            logging.info("Test suite completed successfully")
        else:
            logging.error("Test suite failed")
            sys.exit(exit_code)
    except Exception as e:
        logging.error(f"Failed to run test suite: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 