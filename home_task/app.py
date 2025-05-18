from fastapi import FastAPI
from home_task.api import health, days_to_hire
from home_task.utils.logging_config import setup_logging
from home_task.utils.db import check_database_connection

# Set up logging
logger = setup_logging()

app = FastAPI(
    title="HRF Universe API",
    description="API for HRF Universe",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Check database connection on startup."""
    if not check_database_connection():
        logger.error("Failed to connect to database. Exiting...")
        exit(1)
    logger.info("Successfully connected to database")

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(days_to_hire.router, prefix="/api/v1", tags=["days-to-hire"]) 