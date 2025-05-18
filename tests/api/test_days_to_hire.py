import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from home_task.app import app
from home_task.db import get_session
from home_task.models.db_schema.days_to_hire import DaysToHireStats
from home_task.models.api_schema.days_to_hire import DaysToHireResponse

client = TestClient(app)

def test_get_days_to_hire_success(mock_db_session, mock_days_to_hire_data):
    """Test successful retrieval of days to hire statistics."""
    # Create a mock query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_days_to_hire_data[0]
    mock_db_session.execute.return_value = mock_result
    
    # Configure the mock session to return the mock result
    mock_db_session.__enter__.return_value = mock_db_session
    
    with patch('home_task.api.days_to_hire.get_session', return_value=mock_db_session):
        response = client.get("/api/v1/days-to-hire?standard_job_id=job1&country_code=US")
        
        assert response.status_code == 200
        data = response.json()
        assert data["standard_job_id"] == "job1"
        assert data["country_code"] == "US"
        assert data["min_days"] == 10.0
        assert data["avg_days"] == 20.0
        assert data["max_days"] == 30.0
        assert data["job_postings_number"] == 100

def test_get_days_to_hire_global(mock_db_session, mock_days_to_hire_data):
    """Test successful retrieval of global days to hire statistics."""
    # Create a mock query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_days_to_hire_data[1]
    mock_db_session.execute.return_value = mock_result
    
    # Configure the mock session to return the mock result
    mock_db_session.__enter__.return_value = mock_db_session
    
    with patch('home_task.api.days_to_hire.get_session', return_value=mock_db_session):
        response = client.get("/api/v1/days-to-hire?standard_job_id=job2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["standard_job_id"] == "job2"
        assert data["country_code"] is None
        assert data["min_days"] == 15.0
        assert data["avg_days"] == 25.0
        assert data["max_days"] == 35.0
        assert data["job_postings_number"] == 200

def test_get_days_to_hire_not_found(mock_db_session):
    """Test 404 response when statistics are not found."""
    # Create a mock query result that returns None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    # Configure the mock session to return the mock result
    mock_db_session.__enter__.return_value = mock_db_session
    
    with patch('home_task.api.days_to_hire.get_session', return_value=mock_db_session):
        response = client.get("/api/v1/days-to-hire?standard_job_id=nonexistent")
        
        assert response.status_code == 404
        assert "No statistics found" in response.json()["detail"]

def test_get_days_to_hire_db_error(mock_db_session):
    """Test 500 response when database error occurs."""
    # Mock to raise SQLAlchemyError
    mock_db_session.execute.side_effect = SQLAlchemyError("Database error")
    
    # Configure the mock session to return the mock result
    mock_db_session.__enter__.return_value = mock_db_session
    
    with patch('home_task.api.days_to_hire.get_session', return_value=mock_db_session):
        response = client.get("/api/v1/days-to-hire?standard_job_id=job1")
        
        assert response.status_code == 500
        assert "An unexpected database error occurred" in response.json()["detail"] 