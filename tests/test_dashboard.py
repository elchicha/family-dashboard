import pytest
from src.dashboard import Dashboard


class TestDashboard:

    @pytest.fixture
    def mock_display(self, mocker):
        """Mock display for testing"""
        return mocker.Mock()

    def test_dashboard_initializes_with_display(self, mock_display):
        """Dashboard should be creatable with a display"""
        dashboard = Dashboard(display=mock_display)

        assert dashboard.display == mock_display
