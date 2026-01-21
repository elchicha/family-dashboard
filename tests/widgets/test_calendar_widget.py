from datetime import datetime

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
        assert "9:00 AM" in all_draw_calls
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


class TestCalendarWidgetEnhanced:
    """Tests for enhanced single-day calendar view."""

    @pytest.fixture
    def mock_display(self, mocker):
        """Mock display for testing"""
        display = mocker.Mock()
        display.width = 800
        display.height = 480
        return display

    @pytest.fixture
    def mock_calendar_service(self, mocker):
        """Mock calendar service for testing"""
        return mocker.Mock()

    def test_renders_date_header(self, mock_display, mock_calendar_service, mocker):
        """Should display header with day and date."""
        mock_calendar_service.get_events.return_value = []

        # Mock datetime to control "today"
        mock_datetime = mocker.patch("src.widgets.calendar_widget.datetime")
        mock_datetime.now.return_value = datetime(2025, 1, 20, 12, 0)

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        # Should show day name and date
        assert "MONDAY" in calls_str or "TODAY" in calls_str
        assert "JAN 20" in calls_str or "20" in calls_str

    def test_renders_event_location_if_present(
            self, mock_display, mock_calendar_service
    ):
        """Should display event location below title if available."""
        mock_calendar_service.get_events.return_value = [
            {
                "summary": "Dentist",
                "time": "14:30",
                "location": "123 Main St",
                "uid": "1",
            }
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Dentist" in calls_str
        assert "123 Main St" in calls_str

    def test_location_is_indented(self, mock_display, mock_calendar_service):
        """Location should be indented relative to event title."""
        mock_calendar_service.get_events.return_value = [
            {
                "summary": "Meeting",
                "time": "10:00",
                "location": "Room 5",
                "uid": "1",
            }
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls = mock_display.draw_text.call_args_list

        title_x = None
        location_x = None

        for call in calls:
            text = call.kwargs.get("text", "")
            x_pos = call.kwargs.get("x_pos", 0)

            if "Meeting" in text:
                title_x = x_pos
            if "Room 5" in text:
                location_x = x_pos

        assert title_x is not None, "Should render event title"
        assert location_x is not None, "Should render location"
        assert location_x > title_x, "Location should be indented"

    def test_truncates_after_max_events(self, mock_display, mock_calendar_service):
        """Should truncate and show indicator if more than max events."""
        # Create 6 events
        events = [
            {"summary": f"Event {i + 1}", "time": f"{9 + i}:00", "uid": str(i)}
            for i in range(6)
        ]
        mock_calendar_service.get_events.return_value = events

        widget = CalendarWidget(
            calendar_service=mock_calendar_service,
            max_events=3
        )
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)

        # Should show first 3 events
        assert "Event 1" in calls_str
        assert "Event 2" in calls_str
        assert "Event 3" in calls_str

        # Should NOT show events 4-6
        assert "Event 4" not in calls_str

        # Should show truncation indicator
        assert "+3 more" in calls_str or "3 more" in calls_str

    def test_handles_no_events_gracefully(self, mock_display, mock_calendar_service):
        """Should show message when no events scheduled."""
        mock_calendar_service.get_events.return_value = []

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        # Should show some indication of no events
        assert "No events" in calls_str or "Nothing scheduled" in calls_str

    def test_uses_grayscale_hierarchy(self, mock_display, mock_calendar_service):
        """Should use different colors for different text elements."""
        mock_calendar_service.get_events.return_value = [
            {
                "summary": "Meeting",
                "time": "10:00",
                "location": "Office",
                "uid": "1",
            }
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        colors = [
            call.kwargs.get("color")
            for call in mock_display.draw_text.call_args_list
            if call.kwargs.get("color")
        ]

        unique_colors = set(colors)
        # Should have at least 2 different colors for hierarchy
        assert len(unique_colors) >= 2

    def test_formats_time_in_12_hour_format(self, mock_display, mock_calendar_service):
        """Should display times in 12-hour AM/PM format."""
        mock_calendar_service.get_events.return_value = [
            {"summary": "Lunch", "time": "14:30", "uid": "1"}
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        # Should convert 14:30 to 2:30 PM
        assert "2:30 PM" in calls_str or "2:30PM" in calls_str

    def test_widget_height_is_appropriate(self):
        """Widget height should fit in layout."""
        widget = CalendarWidget(calendar_service=None)
        assert 250 <= widget.height <= 400