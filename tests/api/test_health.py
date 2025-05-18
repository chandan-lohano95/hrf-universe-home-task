import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from home_task.app import app
from home_task.utils.db import check_database_connection

client = TestClient(app)

def test_health_check_success():
    """Test successful health check when all services are healthy."""
    with patch('home_task.api.health.check_database_connection', return_value=True):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

def test_health_check_db_down():
    """Test health check when database is down."""
    with patch('home_task.api.health.check_database_connection', return_value=False):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 503
        assert "One or more services are unavailable" in response.json()["detail"]

def test_health_check_db_error():
    """Test health check when database check raises an error."""
    with patch('home_task.api.health.check_database_connection', side_effect=Exception("Connection error")):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 503
        assert "One or more services are unavailable" in response.json()["detail"] 