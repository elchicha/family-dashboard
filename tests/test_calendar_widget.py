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
        mock_calendar_service.get_events.return_value = [
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

    def test_events_render_at_different_y_positions(
        self, mock_display, mock_calendar_service
    ):
        """Events should render at different Y coordinates so they don't overlap"""
        mock_calendar_service.get_events.return_value = [
            {"name": "First Event", "time": "09:00"},
            {"name": "Second Event", "time": "10:00"},
            {"name": "Third Event", "time": "11:00"},
        ]

        widget = CalendarWidget(mock_display, mock_calendar_service)
        widget.render()

        # Get all the draw_text calls
        calls = mock_display.draw_text.call_args_list

        # Extract Y positions (assuming draw_text is called with positional args x, y, text)
        # calls look like: call(x, y, text) or call(x=.., y=.., text=..)
        y_positions = []
        for call in calls:
            args, kwargs = call
            if len(args) >= 2:
                y_positions.append(args[1])  # Second positional arg is y
            else:
                y_positions.append(kwargs.get("y_pos"))  # Or get from kwargs

        # All Y positions should be different
        assert len(y_positions) == 3
        assert len(set(y_positions)) == 3  # 3 unique values

        # Y positions should increase (events stack downward)
        assert y_positions[0] < y_positions[1] < y_positions[2]
