from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from ..ingestion.acquisition.federal_register_ingestor import FederalRegisterIngestor
from ..ingestion.acquisition.far_dfars_ingestor import FarDfarsIngestor
from ..utils.config_loader import AppConfig
from ..utils.error_handling import handle_exceptions, DataIngestionError
from ..utils.logging import get_logger

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = get_logger(__name__)


class IngestResponse(BaseModel):
    """Response model for ingestion endpoints."""
    task_id: str
    status: str
    message: str


async def get_ingestors(config: AppConfig = Depends()):
    """Get ingestor instances."""
    return {
        "federal_register": FederalRegisterIngestor(config),
        "far_dfars": FarDfarsIngestor(config)
    }


async def run_ingestion(
    ingestor_name: str,
    ingestors: dict,
    **kwargs
):
    """
    Run ingestion task in background.
    
    Args:
        ingestor_name: Name of the ingestor to use
        ingestors: Dictionary of ingestor instances
        **kwargs: Additional arguments for the ingestor
    """
    try:
        ingestor = ingestors[ingestor_name]
        await ingestor.ingest(**kwargs)
        logger.info(f"Completed {ingestor_name} ingestion")
    except Exception as e:
        logger.error(f"Failed {ingestor_name} ingestion: {str(e)}")
        raise


@router.post("/federal-register", response_model=IngestResponse)
@handle_exceptions(logger)
async def ingest_federal_register(
    background_tasks: BackgroundTasks,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    document_type: Optional[str] = None,
    ingestors: dict = Depends(get_ingestors)
):
    """
    Trigger Federal Register data ingestion.
    
    Args:
        background_tasks: FastAPI background tasks
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        document_type: Optional document type filter
        ingestors: Dictionary of ingestor instances
        
    Returns:
        IngestResponse: Task status
    """
    try:
        # Validate dates
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
            end_date = end_dt.strftime("%Y-%m-%d")
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = end_dt - timedelta(days=1)
            start_date = start_dt.strftime("%Y-%m-%d")
        
        if start_dt > end_dt:
            raise ValueError("Start date must be before end date")
        
        # Add ingestion task to background
        task_id = f"federal_register_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        background_tasks.add_task(
            run_ingestion,
            "federal_register",
            ingestors,
            start_date=start_date,
            end_date=end_date,
            document_type=document_type
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": f"Started Federal Register ingestion from {start_date} to {end_date}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")


@router.post("/far-dfars", response_model=IngestResponse)
@handle_exceptions(logger)
async def ingest_far_dfars(
    background_tasks: BackgroundTasks,
    regulation_type: Optional[str] = Query(None, regex="^(far|dfars|both)$"),
    part_number: Optional[str] = None,
    ingestors: dict = Depends(get_ingestors)
):
    """
    Trigger FAR/DFARS data ingestion.
    
    Args:
        background_tasks: FastAPI background tasks
        regulation_type: Optional regulation type filter ("far", "dfars", or "both")
        part_number: Optional part number to fetch
        ingestors: Dictionary of ingestor instances
        
    Returns:
        IngestResponse: Task status
    """
    # Add ingestion task to background
    task_id = f"far_dfars_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    background_tasks.add_task(
        run_ingestion,
        "far_dfars",
        ingestors,
        regulation_type=regulation_type,
        part_number=part_number
    )
    
    message = f"Started FAR/DFARS ingestion"
    if regulation_type:
        message += f" for {regulation_type.upper()}"
    if part_number:
        message += f" Part {part_number}"
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": message
    } 