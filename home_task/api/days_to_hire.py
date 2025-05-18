from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from home_task.db import get_session
from home_task.models.db_schema.days_to_hire import DaysToHireStats
from home_task.models.api_schema.days_to_hire import DaysToHireResponse
from home_task.utils.logging_config import setup_logging

# Get logger
logger = setup_logging()

router = APIRouter()

@router.get("/days-to-hire", response_model=DaysToHireResponse, responses={
    200: {"description": "Successfully retrieved days to hire statistics"},
    404: {"description": "No statistics found for the given standard_job_id"},
    500: {"description": "Internal server error occurred"},
    503: {"description": "Database connection error"}
})
async def get_days_to_hire(
    standard_job_id: str,
    country_code: Optional[str] = None
):
    """
    Get days to hire statistics for a specific job and country.
    
    Args:
        standard_job_id: The standard job ID to get statistics for
        country_code: Optional country code. If not provided, returns global statistics
    
    Returns:
        DaysToHireResponse containing days to hire statistics
    
    Raises:
        HTTPException: If no statistics are found or database connection error occurs
    """
    try:
        with get_session() as session:
            query = select(DaysToHireStats).where(
                DaysToHireStats.standard_job_id == standard_job_id,
                DaysToHireStats.country_code == country_code if country_code is not None else DaysToHireStats.country_code.is_(None)
            )
            result = session.execute(query).scalar_one_or_none()
            
            if not result:
                logger.warning(f"No statistics found for standard_job_id: {standard_job_id} and country_code: {country_code}")
                raise HTTPException(
                    status_code=404,
                    detail=f"No statistics found for standard_job_id: {standard_job_id} and country_code: {country_code}"
                )
            
            # Convert the result to a dictionary and ensure proper types
            response_data = {
                "standard_job_id": str(result.standard_job_id),
                "country_code": str(result.country_code) if result.country_code is not None else None,
                "min_days": float(result.min_days_to_hire),
                "avg_days": float(result.avg_days_to_hire),
                "max_days": float(result.max_days_to_hire),
                "job_postings_number": int(result.job_postings_count)
            }
            
            logger.debug(f"Successfully retrieved statistics for standard_job_id: {standard_job_id} and country_code: {country_code}")
            return DaysToHireResponse(**response_data)
    except OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please try again later."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected database error occurred"
        )
