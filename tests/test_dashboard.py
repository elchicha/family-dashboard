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

    def test_dashboard_renders_all_widget(self, mock_display, mocker):
        """Dashboard should render all widgets and refresh the display"""
        dashboard = Dashboard(display=mock_display)

        mock_widget1 = mocker.Mock()
        mock_widget2 = mocker.Mock()

        dashboard.add_widget(mock_widget1, x_pos=0, y_pos=0)
        dashboard.add_widget(mock_widget2, x_pos=400, y_pos=0)

        dashboard.render()

        mock_display.clear.assert_called_once()

        mock_widget1.render.assert_called_once()
        mock_widget2.render.assert_called_once()

        mock_display.refresh.assert_called_once()

    def test_dashboard_passes_position_offsets_to_widgets(self, mock_display, mocker):
        """Dashboard should tell widgets where to render"""
        dashboard = Dashboard(display=mock_display)

        mock_widget = mocker.Mock()

        dashboard.add_widget(mock_widget, x_pos=100, y_pos=50)
        dashboard.render()

        mock_widget.render.assert_called_once()
        call_kwargs = mock_widget.render.call_args.kwargs
        assert call_kwargs.get("x_offset") == 100
        assert call_kwargs.get("y_offset") == 50
