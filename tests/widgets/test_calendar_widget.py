from datetime import datetime, timedelta, time

import pytest
from unittest.mock import Mock, patch
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

    def test_multi_day_headers_show_correct_day_labels(
        self, mock_display, mock_calendar_service_multi_day
    ):
        """Headers should say TODAY, TOMORROW, and weekday name — not always TODAY."""
        widget = CalendarWidget(
            calendar_service=mock_calendar_service_multi_day,
            view_mode="three_day",
            available_height=480,
        )

        widget.render(display=mock_display, x_offset=0, y_offset=0)
        calls_str = str(mock_display.draw_text.call_args_list)

        # Should have TODAY for the first day
        assert "TODAY" in calls_str

        # Should have TOMORROW for the second day — NOT another TODAY
        assert "TOMORROW" in calls_str

        # Count how many times TODAY appears — should be exactly once (in the header)
        today_count = calls_str.count("TODAY")
        assert today_count == 1, f"TODAY should appear once, but appeared {today_count} times"

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


class TestCategorizeEventsByTime:
    """Tests for _categorize_events_by_time method."""

    @pytest.fixture
    def widget(self):
        return CalendarWidget(Mock(), horizon_mode=True)

    def test_all_day_events_categorized_separately(self, widget):
        """All-day events should be placed in the all_day list."""
        today = datetime.now().date()
        events = [
            {"summary": "Holiday", "time": "All Day", "date": today},
        ]

        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(10, 0), events
        )

        assert len(all_day) == 1
        assert all_day[0]["summary"] == "Holiday"
        assert len(now_events) == 0
        assert len(past) == 0
        assert len(upcoming) == 0

    def test_past_events_categorized(self, widget):
        """Events whose end time is before current_time should be past."""
        today = datetime.now().date()
        events = [
            {"summary": "Early Meeting", "time": "08:00", "date": today},
        ]
        # Event is 08:00-09:00, current time is 10:00 -> past
        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(10, 0), events
        )

        assert len(past) == 1
        assert past[0]["summary"] == "Early Meeting"

    def test_happening_now_events_categorized(self, widget):
        """Events where start <= current < end should be happening now."""
        today = datetime.now().date()
        events = [
            {"summary": "Current Meeting", "time": "10:00", "date": today},
        ]
        # Event is 10:00-11:00, current time is 10:30 -> happening now
        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(10, 30), events
        )

        assert len(now_events) == 1
        assert now_events[0]["summary"] == "Current Meeting"

    def test_upcoming_events_categorized(self, widget):
        """Events starting after current_time should be upcoming."""
        today = datetime.now().date()
        events = [
            {"summary": "Afternoon Event", "time": "14:00", "date": today},
        ]

        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(10, 0), events
        )

        assert len(upcoming) == 1
        assert upcoming[0]["summary"] == "Afternoon Event"

    def test_mixed_event_categorization(self, widget):
        """Should correctly categorize a mix of all event types."""
        today = datetime.now().date()
        events = [
            {"summary": "All Day Fest", "time": "All Day", "date": today},
            {"summary": "Morning Done", "time": "07:00", "date": today},
            {"summary": "In Progress", "time": "10:00", "date": today},
            {"summary": "Later Today", "time": "15:00", "date": today},
        ]
        # 07:00-08:00 past, 10:00-11:00 now, 15:00 upcoming at 10:30
        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(10, 30), events
        )

        assert len(all_day) == 1
        assert len(past) == 1
        assert len(now_events) == 1
        assert len(upcoming) == 1
        assert past[0]["summary"] == "Morning Done"
        assert now_events[0]["summary"] == "In Progress"
        assert upcoming[0]["summary"] == "Later Today"

    def test_unparseable_time_excluded(self, widget):
        """Events with invalid time strings should be excluded from all categories."""
        today = datetime.now().date()
        events = [
            {"summary": "Bad Time", "time": "not-a-time", "date": today},
            {"summary": "Good Event", "time": "14:00", "date": today},
        ]

        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(10, 0), events
        )

        total = len(all_day) + len(now_events) + len(past) + len(upcoming)
        assert total == 1
        assert upcoming[0]["summary"] == "Good Event"

    def test_event_with_custom_duration(self, widget):
        """Event with duration_minutes should use that for categorization."""
        today = datetime.now().date()
        events = [
            {
                "summary": "Long Meeting",
                "time": "09:00",
                "date": today,
                "duration_minutes": 180,
            },
        ]
        # 09:00 with 180min = ends at 12:00. At 11:00 still happening now.
        all_day, now_events, past, upcoming = widget._categorize_events_by_time(
            time(11, 0), events
        )

        assert len(now_events) == 1
        assert now_events[0]["summary"] == "Long Meeting"


class TestFetchHorizonEvents:
    """Tests for _fetch_horizon_events method."""

    def test_separates_today_and_tomorrow_events(self):
        """Events should be correctly split by date."""
        mock_service = Mock()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        mock_service.get_events.return_value = [
            {"summary": "Today Event", "time": "09:00", "date": today},
            {"summary": "Tomorrow Event", "time": "10:00", "date": tomorrow},
        ]

        widget = CalendarWidget(mock_service, horizon_mode=True)
        current_time, now, today_events, tomorrow_events = (
            widget._fetch_horizon_events()
        )

        assert len(today_events) == 1
        assert today_events[0]["summary"] == "Today Event"
        assert len(tomorrow_events) == 1
        assert tomorrow_events[0]["summary"] == "Tomorrow Event"

    def test_calls_service_with_correct_date_range(self):
        """Service should be called with today to end of tomorrow."""
        mock_service = Mock()
        mock_service.get_events.return_value = []

        widget = CalendarWidget(mock_service, horizon_mode=True)
        widget._fetch_horizon_events()

        call_args = mock_service.get_events.call_args
        start_date = call_args[1]["start_date"]
        end_date = call_args[1]["end_date"]

        today = datetime.now().date()
        assert start_date == today
        assert end_date == today + timedelta(days=2)

    def test_handles_datetime_dates(self):
        """Should handle event dates that are datetime objects."""
        mock_service = Mock()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        mock_service.get_events.return_value = [
            {"summary": "DateTime Event", "time": "09:00", "date": today},
        ]

        widget = CalendarWidget(mock_service, horizon_mode=True)
        _, _, today_events, _ = widget._fetch_horizon_events()

        assert len(today_events) == 1
        assert today_events[0]["summary"] == "DateTime Event"

    def test_handles_string_dates(self):
        """Should handle event dates that are date strings."""
        mock_service = Mock()
        today_str = datetime.now().strftime("%Y-%m-%d")

        mock_service.get_events.return_value = [
            {"summary": "String Date Event", "time": "09:00", "date": today_str},
        ]

        widget = CalendarWidget(mock_service, horizon_mode=True)
        _, _, today_events, _ = widget._fetch_horizon_events()

        assert len(today_events) == 1
        assert today_events[0]["summary"] == "String Date Event"

    def test_returns_time_types(self):
        """Should return current_time as time and now as datetime."""
        mock_service = Mock()
        mock_service.get_events.return_value = []

        widget = CalendarWidget(mock_service, horizon_mode=True)
        current_time, now, _, _ = widget._fetch_horizon_events()

        assert isinstance(current_time, time)
        assert isinstance(now, datetime)

    def test_ignores_events_outside_range(self):
        """Events not matching today or tomorrow should be excluded."""
        mock_service = Mock()
        today = datetime.now().date()
        far_future = today + timedelta(days=5)

        mock_service.get_events.return_value = [
            {"summary": "Today Event", "time": "09:00", "date": today},
            {"summary": "Far Future", "time": "09:00", "date": far_future},
        ]

        widget = CalendarWidget(mock_service, horizon_mode=True)
        _, _, today_events, tomorrow_events = widget._fetch_horizon_events()

        assert len(today_events) == 1
        assert len(tomorrow_events) == 0


class TestRenderHorizonView:
    """Tests for _render_horizon_view integration."""

    @pytest.fixture
    def mock_display(self):
        return Mock()

    @pytest.fixture
    def widget(self):
        mock_service = Mock()
        return CalendarWidget(
            mock_service, horizon_mode=True, available_height=480
        )

    def test_horizon_mode_activates_horizon_view(self, mock_display):
        """Setting horizon_mode=True should use horizon view renderer."""
        mock_service = Mock()
        mock_service.get_events.return_value = []

        widget = CalendarWidget(mock_service, horizon_mode=True, available_height=480)
        widget.render(mock_display)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Rest of day is clear" in calls_str

    def test_renders_all_day_banner(self, mock_display, widget):
        """Should render all-day events as a banner."""
        today = datetime.now().date()
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [{"summary": "Holiday", "time": "All Day", "date": today}],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "[ALL DAY]" in calls_str
        assert "Holiday" in calls_str

    def test_renders_happening_now_event(self, mock_display, widget):
        """Should show NOW badge for events currently in progress."""
        today = datetime.now().date()
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [{"summary": "Standup", "time": "10:00", "date": today}],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "NOW" in calls_str
        assert "Standup" in calls_str

    def test_renders_up_next_for_first_upcoming(self, mock_display, widget):
        """Should show UP NEXT for the first upcoming event."""
        today = datetime.now().date()
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [{"summary": "Lunch", "time": "12:00", "date": today}],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "UP NEXT" in calls_str
        assert "Lunch" in calls_str

    def test_renders_coming_up_today_section(self, mock_display, widget):
        """Should show COMING UP TODAY when multiple upcoming events exist."""
        today = datetime.now().date()
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [
                {"summary": "Lunch", "time": "12:00", "date": today},
                {"summary": "Meeting", "time": "14:00", "date": today},
                {"summary": "Review", "time": "16:00", "date": today},
            ],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "COMING UP TODAY" in calls_str
        assert "Meeting" in calls_str
        assert "Review" in calls_str

    def test_renders_rest_of_day_clear(self, mock_display, widget):
        """Should show clear message when no upcoming or happening events."""
        today = datetime.now().date()
        fetch_data = (
            time(20, 0),
            datetime.now().replace(hour=20, minute=0),
            [{"summary": "Past Event", "time": "09:00", "date": today}],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Rest of day is clear" in calls_str

    def test_renders_tomorrow_section(self, mock_display, widget):
        """Should show TOMORROW section when tomorrow has events."""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [{"summary": "Today Event", "time": "12:00", "date": today}],
            [{"summary": "Tomorrow Event", "time": "09:00", "date": tomorrow}],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "TOMORROW" in calls_str
        assert "Tomorrow Event" in calls_str

    def test_renders_past_events_section(self, mock_display, widget):
        """Should show Earlier section for past events when space allows."""
        today = datetime.now().date()
        fetch_data = (
            time(15, 0),
            datetime.now().replace(hour=15, minute=0),
            [
                {"summary": "Done Meeting", "time": "09:00", "date": today},
                {"summary": "Later Event", "time": "16:00", "date": today},
            ],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Earlier" in calls_str

    def test_renders_more_tomorrow_overflow(self, mock_display, widget):
        """Should show '+ N more tomorrow' when too many tomorrow events."""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        tomorrow_events = [
            {"summary": f"Tomorrow Event {i}", "time": f"{8+i}:00", "date": tomorrow}
            for i in range(20)
        ]
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [{"summary": "Today Event", "time": "12:00", "date": today}],
            tomorrow_events,
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "more tomorrow" in calls_str

    def test_all_day_and_upcoming_together(self, mock_display, widget):
        """Should render both all-day banner and upcoming events."""
        today = datetime.now().date()
        fetch_data = (
            time(10, 30),
            datetime.now().replace(hour=10, minute=30),
            [
                {"summary": "Spirit Day", "time": "All Day", "date": today},
                {"summary": "Meeting", "time": "14:00", "date": today},
            ],
            [],
        )

        with patch.object(widget, "_fetch_horizon_events", return_value=fetch_data):
            widget._render_horizon_view(mock_display, 0, 0)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "[ALL DAY]" in calls_str
        assert "Spirit Day" in calls_str
        assert "UP NEXT" in calls_str
        assert "Meeting" in calls_str


class TestHorizonViewHelperRenderers:
    """Tests for individual horizon view rendering helpers."""

    @pytest.fixture
    def mock_display(self):
        return Mock()

    @pytest.fixture
    def widget(self):
        return CalendarWidget(Mock(), horizon_mode=True, available_height=480)

    # _render_now_event tests

    def test_render_now_event_draws_background(self, mock_display, widget):
        """Should draw a highlighted background rectangle."""
        today = datetime.now().date()
        event = {"summary": "Meeting", "time": "10:00", "date": today}
        now = datetime.now().replace(hour=10, minute=30)

        widget._render_now_event(mock_display, 0, 0, event, now)

        rect_calls = mock_display.draw_rectangle.call_args_list
        assert len(rect_calls) == 1
        assert rect_calls[0][1]["fill"] == "#F5F5F5"

    def test_render_now_event_shows_now_badge(self, mock_display, widget):
        """Should display the NOW badge text."""
        today = datetime.now().date()
        event = {"summary": "Meeting", "time": "10:00", "date": today}
        now = datetime.now().replace(hour=10, minute=30)

        widget._render_now_event(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "NOW" in calls_str

    def test_render_now_event_shows_summary(self, mock_display, widget):
        """Should display the event summary."""
        today = datetime.now().date()
        event = {"summary": "Team Sync", "time": "10:00", "date": today}
        now = datetime.now().replace(hour=10, minute=30)

        widget._render_now_event(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Team Sync" in calls_str

    def test_render_now_event_shows_location_when_enabled(self, mock_display):
        """Should display location when show_locations is True."""
        widget = CalendarWidget(Mock(), horizon_mode=True, show_locations=True)
        today = datetime.now().date()
        event = {
            "summary": "Meeting",
            "time": "10:00",
            "date": today,
            "location": "Room A",
        }
        now = datetime.now().replace(hour=10, minute=30)

        widget._render_now_event(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Room A" in calls_str

    def test_render_now_event_hides_location_by_default(self, mock_display, widget):
        """Should not display location when show_locations is False."""
        today = datetime.now().date()
        event = {
            "summary": "Meeting",
            "time": "10:00",
            "date": today,
            "location": "Room A",
        }
        now = datetime.now().replace(hour=10, minute=30)

        widget._render_now_event(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Room A" not in calls_str

    def test_render_now_event_returns_advanced_y(self, mock_display, widget):
        """Should return y_offset + 55."""
        today = datetime.now().date()
        event = {"summary": "Meeting", "time": "10:00", "date": today}
        now = datetime.now().replace(hour=10, minute=30)

        result_y = widget._render_now_event(mock_display, 0, 100, event, now)

        assert result_y == 155

    # _render_next_event_with_countdown tests

    def test_render_next_event_shows_up_next(self, mock_display, widget):
        """Should display UP NEXT label."""
        today = datetime.now().date()
        event = {"summary": "Lunch", "time": "12:00", "date": today}
        now = datetime.combine(today, time(10, 30))

        widget._render_next_event_with_countdown(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "UP NEXT" in calls_str

    def test_render_next_event_countdown_in_minutes(self, mock_display, widget):
        """Should show countdown in minutes when less than 60 min away."""
        today = datetime.now().date()
        event = {"summary": "Quick Chat", "time": "10:45", "date": today}
        now = datetime.combine(today, time(10, 30))

        widget._render_next_event_with_countdown(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "15 min" in calls_str

    def test_render_next_event_countdown_in_hours(self, mock_display, widget):
        """Should show countdown in hours and minutes when 60+ min away."""
        today = datetime.now().date()
        event = {"summary": "Afternoon Meeting", "time": "14:00", "date": today}
        now = datetime.combine(today, time(10, 30))

        widget._render_next_event_with_countdown(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "3h 30m" in calls_str

    def test_render_next_event_urgent_color(self, mock_display, widget):
        """Should use orange color when event is less than 15 minutes away."""
        today = datetime.now().date()
        event = {"summary": "Soon", "time": "10:40", "date": today}
        now = datetime.combine(today, time(10, 30))

        widget._render_next_event_with_countdown(mock_display, 0, 0, event, now)

        colors = [
            call[1].get("color")
            for call in mock_display.draw_text.call_args_list
        ]
        assert "#FF6600" in colors

    def test_render_next_event_normal_color(self, mock_display, widget):
        """Should use grey color when event is 15+ minutes away."""
        today = datetime.now().date()
        event = {"summary": "Later", "time": "12:00", "date": today}
        now = datetime.combine(today, time(10, 30))

        widget._render_next_event_with_countdown(mock_display, 0, 0, event, now)

        # The countdown text should use grey, not orange
        countdown_calls = [
            call
            for call in mock_display.draw_text.call_args_list
            if "in " in call[1].get("text", "") and "min" in call[1].get("text", "")
        ]
        for call in countdown_calls:
            assert call[1]["color"] != "#FF6600"

    def test_render_next_event_returns_advanced_y(self, mock_display, widget):
        """Should return y_offset + 50."""
        today = datetime.now().date()
        event = {"summary": "Event", "time": "12:00", "date": today}
        now = datetime.combine(today, time(10, 30))

        result_y = widget._render_next_event_with_countdown(
            mock_display, 0, 50, event, now
        )

        assert result_y == 100

    # _render_event_line_with_time_until tests

    def test_render_event_line_with_time_until_shows_summary(
        self, mock_display, widget
    ):
        """Should display event summary."""
        today = datetime.now().date()
        event = {"summary": "Meeting", "time": "14:00", "date": today}
        now = datetime.combine(today, time(13, 30))

        widget._render_event_line_with_time_until(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Meeting" in calls_str

    def test_render_event_line_with_time_until_shows_minutes(
        self, mock_display, widget
    ):
        """Should show 'in Xm' for events less than 60 minutes away."""
        today = datetime.now().date()
        event = {"summary": "Meeting", "time": "14:00", "date": today}
        now = datetime.combine(today, time(13, 30))

        widget._render_event_line_with_time_until(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "30m" in calls_str

    def test_render_event_line_with_time_until_urgent_color(
        self, mock_display, widget
    ):
        """Should use orange color when less than 15 minutes away."""
        today = datetime.now().date()
        event = {"summary": "Urgent", "time": "13:40", "date": today}
        now = datetime.combine(today, time(13, 30))

        widget._render_event_line_with_time_until(mock_display, 0, 0, event, now)

        time_until_calls = [
            call
            for call in mock_display.draw_text.call_args_list
            if "10m" in call[1].get("text", "")
        ]
        assert len(time_until_calls) == 1
        assert time_until_calls[0][1]["color"] == "#FF6600"

    def test_render_event_line_with_time_until_hours(self, mock_display, widget):
        """Should show 'in Xh' for events 60+ minutes away."""
        today = datetime.now().date()
        event = {"summary": "Later", "time": "16:00", "date": today}
        now = datetime.combine(today, time(13, 30))

        widget._render_event_line_with_time_until(mock_display, 0, 0, event, now)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "2h" in calls_str

    # _render_all_day_banner tests

    def test_render_all_day_banner_combines_names(self, mock_display, widget):
        """Should combine all-day event names with bullet separator."""
        events = [
            {"summary": "Holiday"},
            {"summary": "Spirit Day"},
        ]

        widget._render_all_day_banner(mock_display, 0, 0, events)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "[ALL DAY]" in calls_str
        assert "Holiday" in calls_str
        assert "Spirit Day" in calls_str

    def test_render_all_day_banner_draws_background(self, mock_display, widget):
        """Should draw a light grey background rectangle."""
        events = [{"summary": "Holiday"}]

        widget._render_all_day_banner(mock_display, 0, 0, events)

        rect_calls = mock_display.draw_rectangle.call_args_list
        assert len(rect_calls) == 1
        assert rect_calls[0][1]["fill"] == "#F5F5F5"

    def test_render_all_day_banner_returns_advanced_y(self, mock_display, widget):
        """Should return y_offset + 25."""
        events = [{"summary": "Holiday"}]

        result_y = widget._render_all_day_banner(mock_display, 0, 100, events)

        assert result_y == 125

    # _render_section_header tests

    def test_render_section_header(self, mock_display, widget):
        """Should render section header text and return advanced y."""
        result_y = widget._render_section_header(mock_display, 0, 0, "TOMORROW")

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "TOMORROW" in calls_str
        assert result_y == 20

    # _render_event_line tests

    def test_render_event_line_shows_time_and_summary(self, mock_display, widget):
        """Should render formatted time and event summary."""
        event = {"summary": "Team Sync", "time": "14:00"}

        widget._render_event_line(mock_display, 0, 0, event)

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "Team Sync" in calls_str
        assert "2:00PM" in calls_str

    def test_render_event_line_compact_uses_smaller_font(self, mock_display, widget):
        """Compact mode should use smaller font sizes."""
        event = {"summary": "Event", "time": "14:00"}

        widget._render_event_line(mock_display, 0, 0, event, compact=True)

        font_sizes = [
            call[1].get("font_size")
            for call in mock_display.draw_text.call_args_list
        ]
        assert 11 in font_sizes  # compact time font
        assert 12 in font_sizes  # compact summary font


class TestParseTime:
    """Tests for _parse_time method."""

    @pytest.fixture
    def widget(self):
        return CalendarWidget(Mock())

    def test_all_day_returns_none(self, widget):
        assert widget._parse_time("All Day") is None

    def test_12_hour_am(self, widget):
        result = widget._parse_time("9:00AM")
        assert result == time(9, 0)

    def test_12_hour_pm(self, widget):
        result = widget._parse_time("2:30PM")
        assert result == time(14, 30)

    def test_12_hour_with_space(self, widget):
        result = widget._parse_time("9:00 AM")
        assert result == time(9, 0)

    def test_24_hour_format(self, widget):
        result = widget._parse_time("14:30")
        assert result == time(14, 30)

    def test_invalid_format_returns_none(self, widget):
        assert widget._parse_time("not-a-time") is None

    def test_empty_string_returns_none(self, widget):
        assert widget._parse_time("") is None


class TestFormatTime:
    """Tests for _format_time method."""

    @pytest.fixture
    def widget(self):
        return CalendarWidget(Mock())

    def test_all_day(self, widget):
        assert widget._format_time("All Day") == "All Day"

    def test_none_returns_all_day(self, widget):
        assert widget._format_time(None) == "All Day"

    def test_empty_string_returns_all_day(self, widget):
        assert widget._format_time("") == "All Day"

    def test_24_to_12_hour_pm(self, widget):
        assert widget._format_time("14:30") == "2:30PM"

    def test_24_to_12_hour_am(self, widget):
        assert widget._format_time("09:00") == "9:00AM"

    def test_midnight(self, widget):
        assert widget._format_time("00:00") == "12:00AM"

    def test_noon(self, widget):
        assert widget._format_time("12:00") == "12:00PM"

    def test_already_12_hour_format(self, widget):
        assert widget._format_time("2:30PM") == "2:30PM"

    def test_already_12_hour_with_space(self, widget):
        assert widget._format_time("2:30 PM") == "2:30PM"


class TestGetEventEndTime:
    """Tests for _get_event_end_time method."""

    @pytest.fixture
    def widget(self):
        return CalendarWidget(Mock())

    def test_default_one_hour_duration(self, widget):
        """Should default to 1 hour if no duration specified."""
        event = {"summary": "Meeting", "time": "10:00"}
        result = widget._get_event_end_time(event, time(10, 0))

        assert result == time(11, 0)

    def test_custom_duration_minutes(self, widget):
        """Should use duration_minutes when provided."""
        event = {"summary": "Long Meeting", "time": "10:00", "duration_minutes": 90}
        result = widget._get_event_end_time(event, time(10, 0))

        assert result == time(11, 30)

    def test_short_duration(self, widget):
        """Should handle short durations correctly."""
        event = {"summary": "Quick Sync", "time": "10:00", "duration_minutes": 15}
        result = widget._get_event_end_time(event, time(10, 0))

        assert result == time(10, 15)
