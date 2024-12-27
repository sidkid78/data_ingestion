"""Script to check code quality using various tools."""

import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys
import os

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import load_config
from src.utils.logging import setup_logging


def run_command(command: list, description: str) -> bool:
    """Run a shell command and log its output.
    
    Args:
        command: Command to run as a list of strings.
        description: Description of the command for logging.
    
    Returns:
        True if the command succeeded, False otherwise.
    """
    try:
        logging.info(f"Running {description}...")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            if result.stdout:
                logging.info(result.stdout)
            logging.info(f"{description} completed successfully")
            return True
        else:
            if result.stdout:
                logging.error(result.stdout)
            if result.stderr:
                logging.error(result.stderr)
            logging.error(f"{description} failed")
            return False
    except Exception as e:
        logging.error(f"Failed to run {description}: {str(e)}")
        return False


def main():
    """Main function to run code quality checks."""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    try:
        # Define source directories to check
        src_dirs = ["src", "tests", "scripts"]
        src_paths = " ".join(src_dirs)
        
        # Run black code formatter
        if not run_command(
            ["black", "--check"] + src_dirs,
            "black code formatting check"
        ):
            sys.exit(1)
        
        # Run isort import sorting
        if not run_command(
            ["isort", "--check-only"] + src_dirs,
            "isort import sorting check"
        ):
            sys.exit(1)
        
        # Run mypy type checking
        if not run_command(
            ["mypy", src_paths],
            "mypy type checking"
        ):
            sys.exit(1)
        
        # Run pylint code analysis
        if not run_command(
            ["pylint", src_paths],
            "pylint code analysis"
        ):
            sys.exit(1)
        
        # Run bandit security checks
        if not run_command(
            ["bandit", "-r"] + src_dirs,
            "bandit security check"
        ):
            sys.exit(1)
        
        logging.info("All code quality checks passed successfully")
    except Exception as e:
        logging.error(f"Code quality check failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 