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

    def test_dashboard_can_add_widgets(self, mock_display, mocker):
        """Dashboard should allow adding widgets with positions"""
        dashboard = Dashboard(display=mock_display)

        mock_widget = mocker.Mock()

        dashboard.add_widget(mock_widget, x_pos=100, y_pos=50)
        assert len(dashboard.widgets) == 1
        assert dashboard.widgets[0] == (mock_widget, 100, 50)
