"""Adaptive calendar widget that intelligently fits all events without truncation."""

from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple

from src.display.display_interface import DisplayInterface
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
        view_mode: str = "adaptive",
        show_locations: bool = False,
        available_height: int = 350,
        events_per_day: int = 3,
        start_offset_days: int = 0,  # NEW: Start from today+N days
        show_header: bool = True,  # NEW: Option to hide header
    ):
        """
        Initialize calendar widget.

        Args:
            calendar_service: Service to fetch calendar events
            view_mode: "adaptive" (recommended), "three_day", "two_day", "single_day"
            show_locations: Whether to show locations (consumes more space)
            available_height: Available vertical space in pixels
            events_per_day: Max events per day in multi-day views
            start_offset_days: Start from today + N days (0=today, 1=tomorrow)
            show_header: Whether to show the date header
        """
        self.calendar_service = calendar_service
        self.view_mode = view_mode
        self.show_locations = show_locations
        self.padding = 20
        self.width = 480
        self.available_height = available_height
        self.height = available_height
        self.events_per_day = events_per_day
        self.start_offset_days = start_offset_days
        self.show_header = show_header

    def set_width(self, width: int) -> None:
        self.width = width

    def render(self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0):
        """Render the calendar widget with adaptive layout."""
        if self.view_mode == "adaptive":
            self._render_adaptive(display, x_offset, y_offset)
        elif self.view_mode == "five_day":
            self._render_multi_day_view(display, x_offset, y_offset, num_days=5)
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
        start_date = today + timedelta(days=self.start_offset_days)

        # Fetch events for next 5 days from start_date
        events = self.calendar_service.get_events(
            start_date=start_date.date(),
            end_date=(start_date + timedelta(days=4)).date(),
        )

        # Group events by date
        events_by_date = self._group_events_by_date(events)
        first_day_events = len(events_by_date.get(start_date.date(), []))

        # Count total events across 5 days
        total_events = sum(
            len(events_by_date.get((start_date + timedelta(days=i)).date(), []))
            for i in range(5)
        )
        # Smart decision: prioritize first day's density
        # If first day is very busy (15+ events), use filtered single-day view
        if first_day_events >= 15:
            self._render_single_day_filtered(
                display, x_offset, y_offset, events_by_date.get(start_date.date(), [])
            )
        # Adaptive decision logic - favor showing more days
        elif total_events == 0:  # Sparse events - show full week
            self._render_multi_day_view(display, x_offset, y_offset, num_days=5)
        elif total_events <= 30:  # Up to 6 events per day
            self._render_multi_day_view(display, x_offset, y_offset, num_days=5)
        elif total_events <= 40:  # ~13 events per day show 3 days
            self._render_multi_day_view(display, x_offset, y_offset, num_days=3)
        elif total_events <= 50:
            self._render_multi_day_view(display, x_offset, y_offset, num_days=2)
        else:
            # Dense schedule - focus on first day with filtering
            self._render_single_day_filtered(
                display, x_offset, y_offset, events_by_date.get(start_date.date(), [])
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
        start_date = today + timedelta(days=self.start_offset_days)

        # Fetch events
        events = self.calendar_service.get_events(
            start_date=start_date.date(),
            end_date=(start_date + timedelta(days=num_days - 1)).date(),
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
            spacing_between_days = 16
        elif total_events <= 12:
            font_size_event = 13
            font_size_header = 14
            line_height = 18
            spacing_between_days = 14
        else:
            font_size_event = 12
            font_size_header = 13
            line_height = 16
            spacing_between_days = 12

        # PRE-CALCULATE total height needed for all days WITH EVENTS
        total_height_needed = self.padding  # Start with top padding
        days_with_events = 0

        for day_offset in range(num_days):
            current_date = (start_date + timedelta(days=day_offset)).date()
            day_events = events_by_date.get(current_date, [])

            # Skip empty days in height calculation
            if not day_events:
                continue

            days_with_events += 1
            all_day_events, timed_events = self._separate_all_day_events(day_events)

            day_height = 26 + 8  # Header + padding

            if all_day_events:
                day_height += 40

            if timed_events:
                day_height += len(timed_events) * line_height

            day_height += spacing_between_days
            total_height_needed += day_height

        # If total height exceeds available space, reduce font sizes
        if total_height_needed > self.available_height:
            # Too tight - reduce everything slightly
            font_size_event = max(10, font_size_event - 1)
            font_size_header = max(11, font_size_header - 1)
            line_height = max(14, line_height - 2)
            spacing_between_days = max(8, spacing_between_days - 2)

        # Initialize position variables - THIS WAS MISSING
        x_pos = self.padding + x_offset
        y_pos = self.padding + y_offset

        # NOW render each day with the adjusted sizing (SKIP EMPTY DAYS)
        for day_offset in range(num_days):
            current_date = (start_date + timedelta(days=day_offset)).date()
            day_events = events_by_date.get(current_date, [])

            # Skip days with no events
            if not day_events:
                continue

            all_day_events, timed_events = self._separate_all_day_events(day_events)

            # Render day header - adjust day_offset for proper TODAY/TOMORROW labels
            display_day_offset = self.start_offset_days + day_offset
            y_pos = self._render_day_header_inverted(
                display,
                current_date,
                display_day_offset,
                x_pos,
                y_pos,
                font_size_header,
            )
            y_pos += 8

            # Render all-day events group
            if all_day_events:
                y_pos = self._render_all_day_group(
                    display, all_day_events, x_pos + 10, y_pos, font_size_event
                )

            # Render timed events
            if timed_events:
                for event in timed_events:
                    y_pos = self._render_event_compact(
                        display, event, x_pos + 10, y_pos, font_size_event
                    )

            # Add spacing between days
            y_pos += spacing_between_days

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
        today = datetime.now() + timedelta(days=self.start_offset_days)  # UPDATED
        events = self.calendar_service.get_events(
            start_date=today.date(),
            end_date=today.date(),  # UPDATED: Fetch specific day
        )

        # Sort events by time
        events = self._sort_events_by_time(events)

        x_pos = self.padding + x_offset
        y_pos = self.padding + y_offset

        # Render header with white-on-black styling (ONLY IF show_header is True)
        if self.show_header:  # NEW
            y_pos = self._render_header_inverted(display, today, x_pos, y_pos)
            y_pos += 15

        if not events:
            self._render_no_events(display, x_pos, y_pos)
            return

        # Calculate adaptive sizing based on event count BEFORE using it
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

        # Separate all-day from timed events
        all_day_events, timed_events = self._separate_all_day_events(events)

        # Render all-day events group
        if all_day_events:
            y_pos = self._render_all_day_group(
                display, all_day_events, x_pos, y_pos, font_size
            )

        # Calculate remaining space
        available_space = self.available_height + y_offset - y_pos - 20

        # Render timed events with adaptive sizing
        rendered_count = 0
        for event in timed_events:
            if y_pos + line_height > self.available_height + y_offset - 20:
                # Out of space - show remaining count
                remaining = len(timed_events) - rendered_count
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
        """Render single event in compact format with improved visual hierarchy."""
        time_str = self._format_time(event.get("time", ""))
        source = event.get("source", "")
        summary = event.get("summary", "")

        # Calculate line height
        line_height = font_size + 4

        # Build the line with proper spacing
        x_current = x_pos

        # 1. Event summary (BOLD/PRIMARY) - the focus
        summary_color = color  # Use passed color (allows dimming for past events)

        # Draw event summary
        display.draw_text(
            x_pos=x_current,
            y_pos=y_pos,
            text=summary,
            font_size=font_size,
            color=summary_color,
        )

        # 2. Time and Source positioned at ~75% of total width (much closer to title)
        # Calculate 75% position
        metadata_x = x_pos + int(
            (self.width - 2 * self.padding) * 0.70
        )  # 70% for tighter grouping

        # Draw time (MUTED)
        display.draw_text(
            x_pos=metadata_x,
            y_pos=y_pos,
            text=time_str,
            font_size=font_size - 1,  # Smaller
            color="#888888",  # Muted gray
        )

        # 3. Source tag (VERY MUTED, right after time)
        if source:
            source_x = metadata_x + 60  # Fixed offset after time
            display.draw_text(
                x_pos=source_x,
                y_pos=y_pos,
                text=f"[{source}]",
                font_size=font_size - 2,  # Even smaller
                color="#BBBBBB",  # Very light gray
            )

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

    def _separate_all_day_events(
        self, events: List[dict]
    ) -> Tuple[List[dict], List[dict]]:
        """Separate all-day events from timed events."""
        all_day_events = []
        timed_events = []

        for event in events:
            time_str = event.get("time", "")
            if time_str == "All Day" or not time_str:
                all_day_events.append(event)
            else:
                timed_events.append(event)

        return all_day_events, timed_events

    def _render_all_day_group(
        self,
        display,
        all_day_events: List[dict],
        x_pos: int,
        y_pos: int,
        font_size: int = 13,
    ) -> int:
        """Render grouped all-day events with grey background, grouped by source."""
        if not all_day_events:
            return y_pos

        # Group events by source/calendar
        events_by_source = {}
        for event in all_day_events:
            source = event.get("source", "Other")
            if source not in events_by_source:
                events_by_source[source] = []
            events_by_source[source].append(event.get("summary", "").strip())

        # Build the display text - each source gets bracketed once
        grouped_parts = []
        for source, summaries in sorted(events_by_source.items()):
            combined_summaries = " • ".join(summaries)
            grouped_parts.append(f"[{source}] {combined_summaries}")

        combined_text = " • ".join(grouped_parts)

        # Truncate if too long
        max_chars = 68 if font_size >= 13 else 78
        if len(combined_text) > max_chars:
            combined_text = combined_text[: max_chars - 3] + "..."

        # Calculate group height
        group_padding = 6
        line_height = font_size + 4

        # Estimate lines (might wrap)
        estimated_lines = 1 if len(combined_text) <= max_chars else 2
        text_height = line_height * estimated_lines
        group_height = text_height + (2 * group_padding)

        # Draw grey background
        bg_width = self.width - 2 * self.padding - 10
        display.draw_rectangle(
            x_pos=x_pos - 5,
            y_pos=y_pos - 2,
            width=bg_width,
            height=group_height,
            fill="#F5F5F5",  # Light grey
            outline="#E0E0E0",  # Slightly darker border
        )

        # Draw the combined text
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos + group_padding - 2,
            text=combined_text,
            font_size=font_size,
            color="#666666",  # Darker grey for text
        )

        return y_pos + group_height + 4  # Add small spacing after group
