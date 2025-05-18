from fastapi import APIRouter, HTTPException
from typing import Dict

from home_task.utils.db import check_database_connection
from home_task.utils.logging_config import setup_logging

# Get logger
logger = setup_logging()

router = APIRouter()

@router.get("/health", responses={
    200: {"description": "All services are healthy"},
    503: {"description": "One or more services are down"}
})
async def health_check():
    """
    Health check endpoint that verifies all required services.
    Returns 200 if all services are healthy, 503 if any service is down.
    """
    try:
        services: Dict[str, bool] = {
            "database": check_database_connection()
        }
        
        if not all(services.values()):
            logger.error("One or more services are unavailable")
            raise HTTPException(
                status_code=503,
                detail="One or more services are unavailable"
            )
        
        logger.info("Health check passed")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="One or more services are unavailable"
        ) 