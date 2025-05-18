from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from home_task.utils.logging_config import setup_logging

from home_task.db import get_session

# Get logger
logger = setup_logging()

def check_database_connection() -> bool:
    """
    Check database connection and return a user-friendly error message if it fails.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except OperationalError as e:
        error_msg = str(e)
        if "Connection refused" in error_msg:
            logger.error("\n❌ Database Connection Error:")
            logger.error("The application could not connect to the PostgreSQL database.")
            logger.error("\nPossible solutions:")
            logger.error("\n1. Check if Docker container is running (if using Docker):")
            logger.error("   docker-compose up -d")
            logger.error("\n2. Verify database credentials in home_task/db.py")
        else:
            logger.error(f"\n❌ Database Error: {error_msg}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"\n❌ Database Error: {str(e)}")
        return False