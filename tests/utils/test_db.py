import pytest
from unittest.mock import patch, MagicMock
from home_task.utils import db
from sqlalchemy.exc import SQLAlchemyError, OperationalError

def test_check_database_connection_success():
    with patch("home_task.utils.db.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value = None  # SELECT 1 returns no error
        assert db.check_database_connection() is True

def test_check_database_connection_operational_error():
    with patch("home_task.utils.db.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.side_effect = OperationalError("Connection refused", None, None)
        assert db.check_database_connection() is False

def test_check_database_connection_sqlalchemy_error():
    with patch("home_task.utils.db.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.side_effect = SQLAlchemyError("Some DB error")
        assert db.check_database_connection() is False 