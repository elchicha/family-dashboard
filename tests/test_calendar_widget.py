import pytest
from src.widgets.calendar_widget import CalendarWidget


class TestCalendarWidget:

    @pytest.fixture
    def mock_display(self, mocker):
        """Mock display for testing"""
        return mocker.Mock()

    @pytest.fixture
    def mock_calendar_service(self, mocker):
        """Mock calendar service for testing"""
        return mocker.Mock()

    def test_calendar_widget_renders_events_to_display(
        self, mock_display, mock_calendar_service
    ):
        """Widget should fetch events and render them on display"""
        mock_calendar_service.get_todays_events.return_value = [
            {"name": "Standup", "time": "09:00"},
            {"name": "Lunch", "time": "12:00"},
        ]

        widget = CalendarWidget(
            display=mock_display, calendar_service=mock_calendar_service
        )

        widget.render()

        assert mock_display.draw_text.called
        assert mock_display.draw_text.call_count >= 2

        all_draw_calls = str(mock_display.draw_text.call_args_list)
        assert "Standup" in all_draw_calls
        assert "09:00" in all_draw_calls
        assert "Lunch" in all_draw_calls
