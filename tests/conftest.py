import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from home_task.utils.logging_config import setup_logging
import logging

from home_task.db import get_session
from home_task.models.db_schema.days_to_hire import DaysToHireStats

# Set up logging for tests
setup_logging(log_level=logging.DEBUG)

@pytest.fixture
def mock_db_session():
    """Fixture providing a mock database session."""
    session = MagicMock()
    session.__enter__.return_value = session
    return session

@pytest.fixture
def mock_days_to_hire_data():
    """Fixture providing mock days to hire data."""
    return [
        DaysToHireStats(
            standard_job_id="job1",
            country_code="US",
            avg_days_to_hire=20.0,
            min_days_to_hire=10.0,
            max_days_to_hire=30.0,
            job_postings_count=100
        ),
        DaysToHireStats(
            standard_job_id="job2",
            country_code=None,  # Global statistics
            avg_days_to_hire=25.0,
            min_days_to_hire=15.0,
            max_days_to_hire=35.0,
            job_postings_count=200
        )
    ] 