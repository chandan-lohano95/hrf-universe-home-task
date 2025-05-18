import pytest
from unittest.mock import MagicMock, patch
from home_task.scripts.calculate_days_to_hire_stats import DaysToHireStatsCalculator, DaysToHireStatistics

@pytest.fixture
def calculator():
    with patch("home_task.scripts.calculate_days_to_hire_stats.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        calc = DaysToHireStatsCalculator()
        calc.session = mock_session
        yield calc

def test_calculate_stats_for_group_success(calculator):
    mock_result = MagicMock()
    mock_result.min_days = 1
    mock_result.max_days = 10
    mock_result.avg_days = 5
    mock_result.filtered_count = 10
    mock_result.total_count = 12
    calculator.session.execute.return_value.first.return_value = mock_result

    result = calculator.calculate_stats_for_group("job1", "US")
    assert result.success
    assert isinstance(result.stats, DaysToHireStatistics)
    assert result.stats.min_days == 1
    assert result.stats.max_days == 10
    assert result.stats.avg_days == 5

def test_calculate_stats_for_group_not_enough_postings(calculator):
    mock_result = MagicMock()
    mock_result.filtered_count = 2
    calculator.session.execute.return_value.first.return_value = mock_result

    result = calculator.calculate_stats_for_group("job1", "US")
    assert not result.success
    assert "Not enough postings" in result.error_message

def test_calculate_stats_for_group_db_error(calculator):
    calculator.session.execute.side_effect = Exception("DB error")
    result = calculator.calculate_stats_for_group("job1", "US")
    assert not result.success
    assert "error" in result.error_message.lower() 