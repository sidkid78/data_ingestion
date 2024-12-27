"""Script to run database migrations using Alembic."""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys
import os
import alembic.config
import alembic.command

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import load_config
from src.utils.logging import setup_logging


def run_migrations(config_path: str):
    """Run database migrations using Alembic.
    
    Args:
        config_path: Path to the Alembic configuration file.
    """
    try:
        # Create Alembic configuration
        alembic_cfg = alembic.config.Config(config_path)
        
        # Run the migrations
        logging.info("Running database migrations...")
        alembic.command.upgrade(alembic_cfg, "head")
        
        logging.info("Database migrations completed successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to run database migrations: {str(e)}")
        raise


def create_migration(config_path: str, message: str):
    """Create a new migration revision.
    
    Args:
        config_path: Path to the Alembic configuration file.
        message: Migration message/description.
    """
    try:
        # Create Alembic configuration
        alembic_cfg = alembic.config.Config(config_path)
        
        # Create new revision
        logging.info(f"Creating new migration revision: {message}")
        alembic.command.revision(alembic_cfg, message=message, autogenerate=True)
        
        logging.info("Migration revision created successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to create migration revision: {str(e)}")
        raise


def main():
    """Main function to run database migrations."""
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    # Get Alembic config path
    alembic_cfg_path = str(Path(__file__).parent.parent / "alembic.ini")
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "revision":
            # Create new migration revision
            message = sys.argv[2] if len(sys.argv) > 2 else "migration"
            create_migration(alembic_cfg_path, message)
        else:
            # Run migrations
            run_migrations(alembic_cfg_path)
    except Exception as e:
        logging.error(f"Migration operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 