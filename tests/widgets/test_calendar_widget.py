import pytest
from src.widgets.calendar_widget import CalendarWidget


class TestCalendarWidget:

    @pytest.fixture
    def mock_display(self, mocker):
        """Mock display for testing"""
        display = mocker.Mock()
        display.width = 1872
        display.height = 1404
        return display

    @pytest.fixture
    def mock_calendar_service(self, mocker):
        """Mock calendar service for testing"""
        return mocker.Mock()

    def test_calendar_widget_renders_events_to_display(
        self, mock_display, mock_calendar_service
    ):
        """Widget should fetch events and render them on display"""
        mock_calendar_service.get_events.return_value = [
            {"summary": "Standup", "time": "09:00", "uid": "1"},
            {"summary": "Lunch", "time": "12:00", "uid": "2"},
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)

        widget.render(display=mock_display, x_offset=0, y_offset=0)

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
            {"summary": "First Event", "time": "09:00", "uid": "1"},
            {"summary": "Second Event", "time": "10:00", "uid": "2"},
            {"summary": "Third Event", "time": "11:00", "uid": "3"},
        ]

        widget = CalendarWidget(mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        # Get all the draw_text calls
        calls = mock_display.draw_text.call_args_list

        # Extract Y positions IN ORDER
        y_positions = []
        for call in calls:
            args, kwargs = call
            if "y_pos" in kwargs:
                y_positions.append(kwargs["y_pos"])
            elif len(args) >= 2:
                y_positions.append(args[1])

        # Should have at least 3 Y positions
        assert (
            len(y_positions) >= 3
        ), f"Expected at least 3 Y positions, got {len(y_positions)}"

        # All Y positions should be unique (no overlap)
        unique_y = set(y_positions)
        assert (
            len(unique_y) >= 3
        ), f"Expected at least 3 unique Y positions, got {len(unique_y)}"

        # Y positions should increase (events stack downward)
        # Take first 3 Y positions in render order
        first_three_y = y_positions[:3]
        assert (
            first_three_y[0] < first_three_y[1] < first_three_y[2]
        ), f"Y positions should increase: {first_three_y}"
