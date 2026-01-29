from datetime import datetime, timedelta

import pytest
from unittest.mock import Mock
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

        # Extract Y positions and texts to identify unique events
        event_y_positions = {}  # summary -> y_position
        for call in calls:
            args, kwargs = call
            text = str(kwargs.get("text", ""))
            y_pos = (
                kwargs.get("y_pos")
                if "y_pos" in kwargs
                else (args[1] if len(args) >= 2 else None)
            )

            # Track Y position for each event summary
            if "First Event" in text:
                event_y_positions["First Event"] = y_pos
            elif "Second Event" in text:
                event_y_positions["Second Event"] = y_pos
            elif "Third Event" in text:
                event_y_positions["Third Event"] = y_pos

        # Should have all 3 events
        assert (
            len(event_y_positions) == 3
        ), f"Expected 3 events, got {len(event_y_positions)}"

        # Events should be at different Y positions (each event on its own line)
        y_values = list(event_y_positions.values())
        assert (
            y_values[0] < y_values[1] < y_values[2]
        ), f"Event Y positions should increase: First={y_values[0]}, Second={y_values[1]}, Third={y_values[2]}"


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

    def test_renders_date_header(self, mock_display, mock_calendar_service):
        """Should display header with day and date."""
        mock_calendar_service.get_events.return_value = []

        widget = CalendarWidget(
            calendar_service=mock_calendar_service,
            show_header=True,
            view_mode="single_day",  # Force single-day view to ensure header renders
        )
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        # Should show day name or TODAY
        today = datetime.now()
        day_name = today.strftime("%A").upper()
        assert day_name in calls_str or "TODAY" in calls_str

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
            text = str(call.kwargs.get("text", ""))
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

        widget = CalendarWidget(
            calendar_service=mock_calendar_service,
            show_header=True,
            view_mode="single_day",  # Force single-day view to ensure message renders
        )
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls_str = str(mock_display.draw_text.call_args_list)
        # Should show some indication of no events
        assert (
            "No events" in calls_str
            or "Nothing scheduled" in calls_str
            or "No events today" in calls_str
        )

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
            str(call.kwargs.get("text", ""))
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
            str(call.kwargs.get("text", ""))
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


class TestCalendarWidgetWidth:
    """Test that CalendarWidget properly uses assigned width."""

    def test_calendar_widget_has_width_attribute(self):
        """CalendarWidget should have a width attribute."""
        mock_service = Mock()
        widget = CalendarWidget(mock_service)

        assert hasattr(widget, "width")
        assert widget.width == 480  # default width

    def test_calendar_widget_has_set_width_method(self):
        """CalendarWidget should have a set_width method."""
        mock_service = Mock()
        widget = CalendarWidget(mock_service)

        assert hasattr(widget, "set_width")
        assert callable(widget.set_width)

    def test_set_width_updates_width_attribute(self):
        """Calling set_width should update the widget's width."""
        mock_service = Mock()
        widget = CalendarWidget(mock_service)

        new_width = 560
        widget.set_width(new_width)

        assert widget.width == new_width

    def test_render_uses_full_width_for_headers(self):
        """Headers should span the full widget width."""
        mock_service = Mock()
        mock_service.get_events.return_value = []

        widget = CalendarWidget(
            mock_service,
            show_header=True,
            view_mode="single_day",  # Force single-day view to ensure header renders
        )
        widget.set_width(560)

        mock_display = Mock()
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Find the draw_rectangle call for the header
        rectangle_calls = [call for call in mock_display.draw_rectangle.call_args_list]

        # At least one rectangle should be drawn (the header)
        assert (
            len(rectangle_calls) > 0
        ), "Should draw header rectangle when show_header=True"

        # Check that header rectangle uses full width
        header_call = rectangle_calls[0]
        rect_width = header_call[1]["width"]  # keyword argument

        # Header should span close to full width (accounting for padding)
        expected_width = 560 - 2 * widget.padding + 10  # from your code
        assert rect_width == expected_width

    def test_content_respects_padding_with_custom_width(self):
        """Content should be positioned with proper padding regardless of width."""
        mock_service = Mock()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mock_service.get_events.return_value = [
            {
                "summary": "Test Event",
                "time": "9:00AM",
                "date": today,
            }
        ]

        widget = CalendarWidget(mock_service)
        widget.set_width(560)

        mock_display = Mock()
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Check text rendering positions
        text_calls = mock_display.draw_text.call_args_list

        # All text should be within the widget bounds
        for call in text_calls:
            x_pos = call[1]["x_pos"]
            # Text should start at or after padding
            assert x_pos >= widget.padding
            # And shouldn't exceed width (roughly)
            assert x_pos < widget.width


class TestCalendarWidgetFiveDayView:
    """Test five-day calendar view."""

    def test_five_day_mode_enabled(self):
        """CalendarWidget should support five_day view mode."""
        mock_service = Mock()
        mock_service.get_events.return_value = []

        widget = CalendarWidget(mock_service, view_mode="five_day")
        mock_display = Mock()

        widget.render(mock_display)

        # Should fetch 5 days of events (or 4 days if starting from tomorrow)
        call_args = mock_service.get_events.call_args
        start_date = call_args[1]["start_date"]
        end_date = call_args[1]["end_date"]

        assert (end_date - start_date).days >= 3  # At least 4 days

    def test_renders_five_date_headers(self):
        """Five-day view should render up to 5 day headers for days with events."""
        mock_service = Mock()
        today = datetime.now().date()

        # Create events for 5 days
        mock_service.get_events.return_value = [
            {
                "summary": f"Event Day {i}",
                "time": "9:00AM",
                "date": today + timedelta(days=i),
            }
            for i in range(5)
        ]

        widget = CalendarWidget(
            mock_service, view_mode="five_day", available_height=480
        )
        mock_display = Mock()

        widget.render(mock_display)

        # Count header rectangles (black backgrounds)
        rectangle_calls = [
            call
            for call in mock_display.draw_rectangle.call_args_list
            if call[1].get("fill") == "#000000"
        ]

        # Should render headers for days with events (won't skip empty days in this test)
        assert (
            len(rectangle_calls) >= 3
        ), f"Should render at least 3 day headers, got {len(rectangle_calls)}"

    def test_adaptive_mode_uses_five_days_when_sparse(self):
        """Adaptive mode should use 5 days when events are sparse."""
        mock_service = Mock()
        today = datetime.now().date()

        # Very few events across multiple days (3 events total)
        mock_service.get_events.return_value = [
            {"summary": "Event 1", "time": "9:00AM", "date": today},
            {"summary": "Event 2", "time": "2:00PM", "date": today + timedelta(days=2)},
            {"summary": "Event 3", "time": "3:00PM", "date": today + timedelta(days=4)},
        ]

        widget = CalendarWidget(
            mock_service, view_mode="adaptive", available_height=480
        )
        mock_display = Mock()

        widget.render(mock_display)

        # Should fetch 5 days when checking event density
        call_args = mock_service.get_events.call_args
        end_date = call_args[1]["end_date"]
        start_date = call_args[1]["start_date"]

        # Should check at least 4 days ahead
        assert (end_date - start_date).days >= 3

    def test_adaptive_mode_scales_down_with_many_events(self):
        """Adaptive mode should use fewer days or single-day view when there are many events."""
        mock_service = Mock()
        today = datetime.now().date()

        # Many events today (20 events)
        mock_service.get_events.return_value = [
            {"summary": f"Event {i}", "time": f"{8+i}:00AM", "date": today}
            for i in range(20)
        ]

        widget = CalendarWidget(
            mock_service, view_mode="adaptive", available_height=480
        )
        mock_display = Mock()

        widget.render(mock_display)

        # With many events, should adapt layout
        # Just verify it renders without errors
        assert mock_display.draw_text.called


class TestCalendarWidgetAllDayGrouping:
    """Test all-day event grouping with visual background."""

    def test_groups_multiple_all_day_events(self):
        """Multiple all-day events should be grouped together."""
        mock_service = Mock()
        today = datetime.now().date()

        mock_service.get_events.return_value = [
            {"summary": "Event 1", "time": "All Day", "date": today},
            {"summary": "Event 2", "time": "All Day", "date": today},
            {"summary": "Event 3", "time": "All Day", "date": today},
            {"summary": "Timed Event", "time": "9:00AM", "date": today},
        ]

        widget = CalendarWidget(mock_service, view_mode="single_day")
        mock_display = Mock()

        widget.render(mock_display)

        # Should draw a rectangle background for all-day section
        rectangle_calls = [
            call
            for call in mock_display.draw_rectangle.call_args_list
            if call[1].get("fill") == "#F5F5F5"  # Light grey background
        ]

        assert len(rectangle_calls) >= 1, "Should draw background for all-day group"

    def test_all_day_events_shown_on_single_line(self):
        """All-day events should be combined on one line."""
        mock_service = Mock()
        today = datetime.now().date()

        mock_service.get_events.return_value = [
            {"summary": "SCEF Read-a-thon", "time": "All Day", "date": today},
            {"summary": "Book Fair", "time": "All Day", "date": today},
            {"summary": "Catholic Schools Week", "time": "All Day", "date": today},
        ]

        widget = CalendarWidget(mock_service, view_mode="single_day")
        mock_display = Mock()

        widget.render(mock_display)

        # Find texts containing all-day event summaries
        text_calls = [call for call in mock_display.draw_text.call_args_list]
        all_day_combined = [
            call[1]["text"]
            for call in text_calls
            if "SCEF Read-a-thon" in call[1]["text"] or "Book Fair" in call[1]["text"]
        ]

        # Should combine into one line (or wrap if very long)
        assert len(all_day_combined) <= 2, "All-day events should be on 1-2 lines max"

    def test_separates_all_day_from_timed_events(self):
        """All-day section should visually separate from timed events."""
        mock_service = Mock()
        today = datetime.now().date()

        mock_service.get_events.return_value = [
            {"summary": "All Day Event", "time": "All Day", "date": today},
            {"summary": "Morning Event", "time": "9:00AM", "date": today},
        ]

        widget = CalendarWidget(mock_service, view_mode="single_day")
        mock_display = Mock()

        widget.render(mock_display)

        # Should have grey background for all-day section
        grey_rectangles = [
            call
            for call in mock_display.draw_rectangle.call_args_list
            if call[1].get("fill") == "#F5F5F5"
        ]

        assert (
            len(grey_rectangles) >= 1
        ), "Should have grey background for all-day events"

        text_calls = [call for call in mock_display.draw_text.call_args_list]
        texts = [call[1]["text"] for call in text_calls]

        # Should render both types of events
        assert any("All Day Event" in text for text in texts)
        assert any("9:00AM" in text for text in texts)
