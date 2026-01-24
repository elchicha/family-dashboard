"""Adaptive calendar widget that intelligently fits all events without truncation."""

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.display.display_interface import DisplayInterface
from src.services.event_categorizer import EventCategory, EventCategorizer
from src.widgets.widget_interface import WidgetInterface


class CalendarWidget(WidgetInterface):
    """
    Adaptive calendar widget that never truncates - intelligently adjusts to fit all content.

    Adaptive Strategy:
    1. Calculate total events across days
    2. Estimate required space
    3. Choose optimal layout:
       - Three-day view (if space permits)
       - Two-day view (if moderate events)
       - Single-day view with time filtering (if many events)
    4. Dynamically adjust font sizes and spacing

    Features:
    - White-on-black date headers for visual prominence
    - Grayscale hierarchy for readability
    - Smart time-based filtering (prioritizes upcoming/current events)
    - Graceful handling of empty days
    - Compact layout optimized for E-Ink

    Optimized for 480px wide column in two-column layout.
    """

    def __init__(
        self,
        calendar_service,
        view_mode: str = "adaptive",  # "adaptive", "three_day", "two_day", "single_day"
        show_locations: bool = False,  # Locations disabled by default for space
        available_height: int = 350,  # Default height for single-day compatibility
        events_per_day: int = 3,  # For multi-day views
    ):
        """
        Initialize calendar widget.

        Args:
            calendar_service: Service to fetch calendar events
            view_mode: "adaptive" (recommended), "three_day", "two_day", "single_day"
            show_locations: Whether to show locations (consumes more space)
            available_height: Available vertical space in pixels
            events_per_day: Max events per day in multi-day views
        """
        self.calendar_service = calendar_service
        self.view_mode = view_mode
        self.show_locations = show_locations
        self.padding = 20
        self.width = 480
        self.available_height = available_height
        self.height = available_height  # Required by layout manager
        self.events_per_day = events_per_day

    def render(self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0):
        """Render the calendar widget with adaptive layout."""
        if self.view_mode == "adaptive":
            self._render_adaptive(display, x_offset, y_offset)
        elif self.view_mode == "two_day":
            self._render_multi_day_view(display, x_offset, y_offset, num_days=2)
        elif self.view_mode == "three_day":
            self._render_multi_day_view(display, x_offset, y_offset, num_days=3)
        else:
            self._render_single_day_view(display, x_offset, y_offset)

    # ========== Adaptive Layout Logic ==========

    def _render_adaptive(
        self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0
    ):
        """Intelligently choose the best layout to fit all events."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Fetch events for next 3 days
        events = self.calendar_service.get_events(
            start_date=today.date(), end_date=(today + timedelta(days=2)).date()
        )

        # Group events by date
        events_by_date = self._group_events_by_date(events)

        # Count events per day
        today_count = len(events_by_date.get(today.date(), []))
        tomorrow_count = len(events_by_date.get((today + timedelta(days=1)).date(), []))
        day_after_count = len(
            events_by_date.get((today + timedelta(days=2)).date(), [])
        )
        total_events = today_count + tomorrow_count + day_after_count

        # Decision logic
        if total_events == 0:
            # Show 3 days if no events
            self._render_multi_day_view(display, x_offset, y_offset, num_days=3)
        elif total_events <= 9:  # ~3 events per day
            # Three-day view fits comfortably
            self._render_multi_day_view(display, x_offset, y_offset, num_days=3)
        elif total_events <= 15:  # ~7-8 events per day
            # Two-day view with more space per event
            self._render_multi_day_view(display, x_offset, y_offset, num_days=2)
        else:
            # Many events today - focus on current day with time filtering
            self._render_single_day_filtered(
                display, x_offset, y_offset, events_by_date.get(today.date(), [])
            )

    # ========== Multi-Day View (2 or 3 days) ==========

    def _render_multi_day_view(
        self,
        display: DisplayInterface,
        x_offset: int = 0,
        y_offset: int = 0,
        num_days: int = 3,
    ):
        """Render multiple consecutive days with adaptive sizing."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Fetch events
        events = self.calendar_service.get_events(
            start_date=today.date(),
            end_date=(today + timedelta(days=num_days - 1)).date(),
        )

        # Group events by date
        events_by_date = self._group_events_by_date(events)

        # Count total events to determine sizing
        total_events = len(events)

        # Adaptive sizing based on event count
        if total_events <= 6:
            font_size_event = 14
            font_size_header = 15
            line_height = 20
            spacing_between_days = 12
        elif total_events <= 12:
            font_size_event = 13
            font_size_header = 14
            line_height = 18
            spacing_between_days = 10
        else:
            font_size_event = 12
            font_size_header = 13
            line_height = 16
            spacing_between_days = 8

        x_pos = self.padding + x_offset
        y_pos = self.padding + y_offset

        # Render each day
        for day_offset in range(num_days):
            current_date = (today + timedelta(days=day_offset)).date()
            day_events = events_by_date.get(current_date, [])

            # Check if we have space for this day
            estimated_day_height = (
                26
                + (len(day_events) * line_height if day_events else line_height)
                + spacing_between_days
            )
            if y_pos + estimated_day_height > self.available_height + y_offset - 20:
                # Not enough space for this day, stop here
                break

            # Render day header (white-on-black)
            y_pos = self._render_day_header_inverted(
                display, current_date, day_offset, x_pos, y_pos, font_size_header
            )
            y_pos += 8

            # Render events for this day
            if day_events:
                for event in day_events:
                    # Stop if we run out of space
                    if y_pos + line_height > self.available_height + y_offset - 20:
                        # Show remaining count
                        remaining = len(day_events) - day_events.index(event)
                        display.draw_text(
                            x_pos=x_pos + 10,
                            y_pos=y_pos,
                            text=f"+{remaining} more",
                            font_size=font_size_event - 2,
                            color="#999999",
                        )
                        break

                    y_pos = self._render_event_compact(
                        display, event, x_pos + 10, y_pos, font_size_event
                    )
            else:
                display.draw_text(
                    x_pos=x_pos + 10,
                    y_pos=y_pos,
                    text="No events",
                    font_size=font_size_event,
                    color="#AAAAAA",
                )
                y_pos += line_height

            # Add spacing between days
            y_pos += spacing_between_days

    # ========== Single-Day Filtered View ==========

    def _render_single_day_filtered(
        self,
        display: DisplayInterface,
        x_offset: int = 0,
        y_offset: int = 0,
        events: List[dict] = None,
    ):
        """
        Render single day with time-based filtering.
        Prioritizes: current/upcoming events > past events.
        """
        today = datetime.now()
        current_time = today.time()

        if events is None:
            events = self.calendar_service.get_events()

        # Sort all events by time first
        events = self._sort_events_by_time(events)

        x_pos = self.padding + x_offset
        y_pos = self.padding + y_offset

        # Render header
        y_pos = self._render_header_inverted(display, today, x_pos, y_pos)
        y_pos += 15

        if not events:
            self._render_no_events(display, x_pos, y_pos)
            return

        # Separate events into past and future (already sorted by time)
        future_events = []
        past_events = []

        for event in events:
            event_time_str = event.get("time", "")
            try:
                # Parse event time
                if ":" in event_time_str:
                    time_parts = (
                        event_time_str.replace("AM", "")
                        .replace("PM", "")
                        .strip()
                        .split(":")
                    )
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                    # Handle PM times
                    if "PM" in event_time_str and hour != 12:
                        hour += 12
                    elif "AM" in event_time_str and hour == 12:
                        hour = 0

                    event_time = datetime.now().replace(hour=hour, minute=minute).time()

                    if event_time >= current_time:
                        future_events.append(event)
                    else:
                        past_events.append(event)
                else:
                    future_events.append(event)  # All-day events
            except (ValueError, AttributeError):
                future_events.append(event)  # Can't parse, assume future

        # Render future events first (priority) - already sorted
        font_size = 14
        line_height = 20

        # Estimate space available
        available_lines = (self.available_height + y_offset - y_pos - 20) // line_height

        for event in future_events:
            if available_lines <= 0:
                break
            y_pos = self._render_event_compact(display, event, x_pos, y_pos, font_size)
            available_lines -= 1

        # Show past events if space remains - already sorted
        if available_lines > 0 and past_events:
            # Add separator
            display.draw_text(
                x_pos=x_pos,
                y_pos=y_pos,
                text="─── Earlier today ───",
                font_size=12,
                color="#CCCCCC",
            )
            y_pos += line_height
            available_lines -= 1

            for event in past_events:
                if available_lines <= 0:
                    break
                y_pos = self._render_event_compact(
                    display, event, x_pos, y_pos, font_size, color="#888888"
                )
                available_lines -= 1

        # Show count of hidden past events if any
        if available_lines <= 0 and past_events:
            remaining_past = len(past_events) - (len(future_events) - available_lines)
            if remaining_past > 0:
                display.draw_text(
                    x_pos=x_pos,
                    y_pos=y_pos,
                    text=f"+{remaining_past} earlier events not shown",
                    font_size=11,
                    color="#AAAAAA",
                )

    # ========== Single-Day View (Standard) ==========

    def _render_single_day_view(
        self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0
    ):
        """Render a single day's events with adaptive sizing."""
        today = datetime.now()
        events = self.calendar_service.get_events()

        # Sort events by time
        events = self._sort_events_by_time(events)

        x_pos = self.padding + x_offset
        y_pos = self.padding + y_offset

        # Render header with white-on-black styling
        y_pos = self._render_header_inverted(display, today, x_pos, y_pos)
        y_pos += 15

        if not events:
            self._render_no_events(display, x_pos, y_pos)
            return

        # Calculate adaptive sizing based on event count
        event_count = len(events)
        available_space = self.available_height + y_offset - y_pos - 20

        if event_count <= 8:
            font_size = 14
            line_height = 20
        elif event_count <= 12:
            font_size = 13
            line_height = 18
        else:
            font_size = 12
            line_height = 16

        # Render events with adaptive sizing
        rendered_count = 0
        for event in events:
            if y_pos + line_height > self.available_height + y_offset - 20:
                # Out of space - show remaining count
                remaining = len(events) - rendered_count
                if remaining > 0:
                    display.draw_text(
                        x_pos=x_pos,
                        y_pos=y_pos,
                        text=f"+{remaining} more",
                        font_size=font_size - 2,
                        color="#999999",
                    )
                break

            y_pos = self._render_event_compact(display, event, x_pos, y_pos, font_size)
            rendered_count += 1

    # ========== Header Rendering ==========

    def _render_header_inverted(
        self, display, date_obj: datetime, x_pos: int, y_pos: int
    ) -> int:
        """Render white-on-black header for single day view."""
        # Format header text
        header_text = f" TODAY - {date_obj.strftime('%A, %b %d').upper()} "

        # Draw black rectangle background (full width)
        header_height = 28
        rect_width = self.width - 2 * self.padding + 10
        display.draw_rectangle(
            x_pos=x_pos - 10,
            y_pos=y_pos,
            width=rect_width,
            height=header_height,
            fill="#000000",
            outline="#000000",
        )

        # Draw white text on black background
        display.draw_text(
            x_pos=x_pos + 5,
            y_pos=y_pos + 6,
            text=header_text,
            font_size=16,
            color="#FFFFFF",
        )

        return y_pos + header_height

    def _render_day_header_inverted(
        self,
        display,
        date_obj: date,
        day_offset: int,
        x_pos: int,
        y_pos: int,
        font_size: int = 15,
    ) -> int:
        """Render compact white-on-black day header."""
        # Format header text
        header_text = self._format_day_header(date_obj, day_offset)

        # Draw black rectangle background
        header_height = 26
        rect_width = self.width - 2 * self.padding + 10
        display.draw_rectangle(
            x_pos=x_pos - 10,
            y_pos=y_pos,
            width=rect_width,
            height=header_height,
            fill="#000000",
            outline="#000000",
        )

        # Draw white text on black background
        display.draw_text(
            x_pos=x_pos + 5,
            y_pos=y_pos + 5,
            text=header_text,
            font_size=font_size,
            color="#FFFFFF",
        )

        return y_pos + header_height

    # ========== Event Rendering ==========

    def _render_event_compact(
        self,
        display,
        event: dict,
        x_pos: int,
        y_pos: int,
        font_size: int = 13,
        color: str = "#000000",
    ) -> int:
        """Render single event in compact format, optionally with location."""
        time_str = self._format_time(event.get("time", ""))
        source_tag = f"[{event.get('source', '')}] " if event.get("source") else ""
        event_line = f"{time_str} {source_tag}{event['summary']}"

        # Truncate if too long
        max_chars = 55 if font_size >= 13 else 60
        if len(event_line) > max_chars:
            event_line = event_line[: max_chars - 3] + "..."

        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=event_line,
            font_size=font_size,
            color=color,
        )

        # Calculate line height based on font size
        line_height = font_size + 4
        y_pos += line_height

        # Render location if enabled and present
        if self.show_locations and event.get("location"):
            location_text = f"  @ {event['location']}"
            display.draw_text(
                x_pos=x_pos + 15,  # Indent location
                y_pos=y_pos,
                text=location_text,
                font_size=font_size - 2,
                color="#888888",
            )
            y_pos += line_height - 2

        return y_pos

    # ========== Empty State ==========

    def _render_no_events(self, display, x_pos: int, y_pos: int) -> None:
        """Render message when no events scheduled."""
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text="No events today",
            font_size=14,
            color="#999999",
        )

    # ========== Utility Methods ==========

    def _group_events_by_date(self, events: List[dict]) -> Dict[date, List[dict]]:
        """Group events by their date and sort by time."""
        events_by_date = {}
        today = datetime.now().date()

        for event in events:
            # If event doesn't have a date field, assume it's for today
            if "date" in event:
                event_date = (
                    event["date"].date()
                    if hasattr(event["date"], "date")
                    else event["date"]
                )
            else:
                event_date = today

            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

        # Sort events within each day by time
        for date_key in events_by_date:
            events_by_date[date_key] = self._sort_events_by_time(
                events_by_date[date_key]
            )

        return events_by_date

    def _sort_events_by_time(self, events: List[dict]) -> List[dict]:
        """Sort events by their time, handling various time formats."""

        def time_sort_key(event):
            time_str = event.get("time", "")

            # Handle empty time (all-day events) - put them first
            if not time_str or time_str == "All Day":
                return (0, 0)  # Midnight (sorts first)

            try:
                # Remove AM/PM and spaces
                time_clean = time_str.replace("AM", "").replace("PM", "").strip()

                # Parse hour and minute
                if ":" in time_clean:
                    parts = time_clean.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                else:
                    hour = int(time_clean)
                    minute = 0

                # Convert to 24-hour format
                if "PM" in time_str and hour != 12:
                    hour += 12
                elif "AM" in time_str and hour == 12:
                    hour = 0

                return (hour, minute)
            except (ValueError, AttributeError, IndexError):
                # If parsing fails, put at end
                return (99, 99)

        return sorted(events, key=time_sort_key)

    def _format_day_header(self, date_obj: date, day_offset: int) -> str:
        """Format day header with day label and date."""
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        day_name = day_names[date_obj.weekday()]

        if day_offset == 0:
            day_label = "● TODAY"
        elif day_offset == 1:
            day_label = "○ TOMORROW"
        else:
            day_label = f"  {day_name.upper()}"

        return f"{day_label} - {date_obj.strftime('%b %d').upper()}"

    def _format_time(self, time_str: str) -> str:
        """Format time string to compact 12-hour format."""
        if not time_str:
            return "All Day"

        if "AM" in time_str or "PM" in time_str:
            # Remove spaces for compactness: "5:30 PM" -> "5:30PM"
            return time_str.replace(" ", "")

        try:
            hour, minute = map(int, time_str.split(":"))
            period = "AM" if hour < 12 else "PM"
            if hour == 0:
                hour = 12
            elif hour > 12:
                hour = hour - 12

            return f"{hour}:{minute:02d}{period}"
        except (ValueError, AttributeError):
            return time_str
