from datetime import datetime, timedelta

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
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_calendar_service.get_events.return_value = [
            {"summary": "Standup", "time": "09:00", "date": today, "uid": "1"},
            {"summary": "Lunch", "time": "12:00", "date": today, "uid": "2"},
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)

        widget.render(display=mock_display, x_offset=0, y_offset=0)

        assert mock_display.draw_text.called
        assert mock_display.draw_text.call_count >= 2

        all_draw_calls = str(mock_display.draw_text.call_args_list)
        assert "Standup" in all_draw_calls
        assert "9:00AM" in all_draw_calls or "9:00 AM" in all_draw_calls
        assert "Lunch" in all_draw_calls

    def test_events_render_at_different_y_positions(
        self, mock_display, mock_calendar_service
    ):
        """Events should render at different Y coordinates so they don't overlap"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_calendar_service.get_events.return_value = [
            {"summary": "First Event", "time": "09:00", "date": today, "uid": "1"},
            {"summary": "Second Event", "time": "10:00", "date": today, "uid": "2"},
            {"summary": "Third Event", "time": "11:00", "date": today, "uid": "3"},
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

        # Get unique Y positions (header elements may share same Y)
        unique_y = set(y_positions)
        assert (
            len(unique_y) >= 3
        ), f"Expected at least 3 unique Y positions, got {len(unique_y)}: {unique_y}"

        # Filter out header Y positions (anything before y=50)
        # Events should start after header + spacing
        event_y_positions = [y for y in y_positions if y >= 50]

        assert (
            len(event_y_positions) >= 3
        ), f"Expected at least 3 events rendered below header, got {len(event_y_positions)}"

        # Y positions of EVENTS should increase (no overlap among events)
        first_three_events = event_y_positions[:3]
        assert (
            first_three_events[0] < first_three_events[1] < first_three_events[2]
        ), f"Event Y positions should increase: {first_three_events}"


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
        """Should display event location below title if available when show_locations=True."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_calendar_service.get_events.return_value = [
            {
                "summary": "Dentist",
                "time": "14:30",
                "location": "123 Main St",
                "date": today,
                "uid": "1",
            }
        ]

        widget = CalendarWidget(
            calendar_service=mock_calendar_service,
            show_locations=True,  # Enable location display
        )
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Dentist" in calls_str
        assert "123 Main St" in calls_str

    def test_location_is_indented(self, mock_display, mock_calendar_service):
        """Location should be indented relative to event title."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_calendar_service.get_events.return_value = [
            {
                "summary": "Meeting",
                "time": "10:00",
                "location": "Room 5",
                "date": today,
                "uid": "1",
            }
        ]

        widget = CalendarWidget(
            calendar_service=mock_calendar_service,
            show_locations=True,  # Enable location display
        )
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

    def test_adaptive_mode_handles_many_events(
        self, mock_display, mock_calendar_service
    ):
        """Adaptive mode should handle many events by adjusting layout."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Create 20 events to trigger adaptive behavior
        events = [
            {
                "summary": f"Event {i + 1}",
                "time": f"{9 + i}:00",
                "date": today,
                "uid": str(i),
            }
            for i in range(20)
        ]
        mock_calendar_service.get_events.return_value = events

        widget = CalendarWidget(
            calendar_service=mock_calendar_service, view_mode="adaptive"
        )
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)

        # Should show first event
        assert "Event 1" in calls_str

        # Widget should adapt to show events (not crash)
        assert mock_display.draw_text.called

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
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_calendar_service.get_events.return_value = [
            {
                "summary": "Meeting",
                "time": "10:00",
                "location": "Office",
                "date": today,
                "uid": "1",
            }
        ]

        widget = CalendarWidget(
            calendar_service=mock_calendar_service, show_locations=True
        )
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
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_calendar_service.get_events.return_value = [
            {"summary": "Lunch", "time": "14:30", "date": today, "uid": "1"}
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        # Should convert 14:30 to 2:30 PM (with or without space)
        assert "2:30PM" in calls_str or "2:30 PM" in calls_str

    def test_widget_height_is_appropriate(self):
        """Widget height should fit in layout (default is 350)."""
        widget = CalendarWidget(calendar_service=None)
        assert 250 <= widget.height <= 400

    def test_events_sorted_by_time(self, mock_display, mock_calendar_service):
        """Events should be sorted by time regardless of order returned."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Return events in random order
        mock_calendar_service.get_events.return_value = [
            {"summary": "Lunch", "time": "12:00", "date": today, "uid": "2"},
            {"summary": "Dinner", "time": "18:00", "date": today, "uid": "3"},
            {"summary": "Breakfast", "time": "08:00", "date": today, "uid": "1"},
        ]

        widget = CalendarWidget(calendar_service=mock_calendar_service)
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        # Extract text content from draw calls
        text_calls = [
            call.kwargs.get("text", "")
            for call in mock_display.draw_text.call_args_list
        ]

        # Find indices of each event in the rendered order
        breakfast_idx = next(
            (i for i, text in enumerate(text_calls) if "Breakfast" in text), None
        )
        lunch_idx = next(
            (i for i, text in enumerate(text_calls) if "Lunch" in text), None
        )
        dinner_idx = next(
            (i for i, text in enumerate(text_calls) if "Dinner" in text), None
        )

        # All events should be rendered
        assert breakfast_idx is not None, "Breakfast should be rendered"
        assert lunch_idx is not None, "Lunch should be rendered"
        assert dinner_idx is not None, "Dinner should be rendered"

        # They should appear in time order
        assert (
            breakfast_idx < lunch_idx < dinner_idx
        ), f"Events should be in time order: Breakfast({breakfast_idx}) < Lunch({lunch_idx}) < Dinner({dinner_idx})"


class TestCalendarWidgetThreeDayView:
    """Tests for three-day compact calendar view."""

    @pytest.fixture
    def mock_display(self, mocker):
        """Mock display for testing"""
        display = mocker.Mock()
        display.width = 800
        display.height = 480
        return display

    @pytest.fixture
    def mock_calendar_service_multi_day(self, mocker):
        """Mock calendar service with events across multiple days for testing"""
        service = mocker.Mock()

        # Today's events
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        service.get_events.return_value = [
            # Today
            {"summary": "Today Event 1", "time": "09:00", "date": today, "uid": "1"},
            {"summary": "Today Event 2", "time": "14:00", "date": today, "uid": "2"},
            # Tomorrow
            {
                "summary": "Tomorrow Event",
                "time": "10:00",
                "date": today + timedelta(days=1),
                "uid": "3",
            },
            # Day after tomorrow
            {
                "summary": "Future Event",
                "time": "15:00",
                "date": today + timedelta(days=2),
                "uid": "4",
            },
        ]
        return service

    def test_three_day_mode_enabled(
        self, mock_display, mock_calendar_service_multi_day
    ):
        """Should support three_day view mode."""
        widget = CalendarWidget(
            calendar_service=mock_calendar_service_multi_day, view_mode="three_day"
        )

        assert widget.view_mode == "three_day"

    def test_renders_three_date_headers(
        self, mock_display, mock_calendar_service_multi_day
    ):
        """Should display header for each day in three-day view."""
        widget = CalendarWidget(
            calendar_service=mock_calendar_service_multi_day,
            view_mode="three_day",
            available_height=480,
        )

        widget.render(display=mock_display, x_offset=0, y_offset=0)
        calls_str = str(mock_display.draw_text.call_args_list)

        assert (
            "TODAY" in calls_str or datetime.now().strftime("%A").upper() in calls_str
        )

        tomorrow = datetime.now() + timedelta(days=1)
        assert "TOMORROW" in calls_str or tomorrow.strftime("%A").upper() in calls_str

    def test_adaptive_mode_chooses_appropriate_layout(
        self, mock_display, mock_calendar_service_multi_day
    ):
        """Adaptive mode should choose layout based on event count."""
        widget = CalendarWidget(
            calendar_service=mock_calendar_service_multi_day,
            view_mode="adaptive",
            available_height=480,
        )

        widget.render(display=mock_display, x_offset=0, y_offset=0)

        # Should render without errors
        assert mock_display.draw_text.called

        calls_str = str(mock_display.draw_text.call_args_list)
        # With 4 events total, should show multi-day view
        assert "Today Event 1" in calls_str or "TODAY" in calls_str

    def test_events_sorted_within_each_day(self, mock_display, mocker):
        """Events within each day should be sorted by time."""
        service = mocker.Mock()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Events in wrong order
        service.get_events.return_value = [
            {"summary": "Lunch", "time": "12:00", "date": today, "uid": "2"},
            {"summary": "Breakfast", "time": "08:00", "date": today, "uid": "1"},
            {"summary": "Dinner", "time": "18:00", "date": today, "uid": "3"},
        ]

        widget = CalendarWidget(
            calendar_service=service, view_mode="three_day", available_height=480
        )

        widget.render(display=mock_display, x_offset=0, y_offset=0)

        # Extract text content from draw calls
        text_calls = [
            call.kwargs.get("text", "")
            for call in mock_display.draw_text.call_args_list
        ]

        # Find indices of each event
        breakfast_idx = next(
            (i for i, text in enumerate(text_calls) if "Breakfast" in text), None
        )
        lunch_idx = next(
            (i for i, text in enumerate(text_calls) if "Lunch" in text), None
        )
        dinner_idx = next(
            (i for i, text in enumerate(text_calls) if "Dinner" in text), None
        )

        # All events should be rendered
        assert breakfast_idx is not None
        assert lunch_idx is not None
        assert dinner_idx is not None

        # They should appear in time order
        assert (
            breakfast_idx < lunch_idx < dinner_idx
        ), "Events should be sorted by time within the day"
