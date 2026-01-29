"""Adaptive calendar widget that intelligently fits all events without truncation."""

from datetime import datetime, timedelta, date, time as time_class, time
from typing import List, Dict, Tuple, Any

from src.display.display_interface import DisplayInterface
from src.widgets.widget_interface import WidgetInterface

# Layout dimensions
DEFAULT_WIDTH = 480
DEFAULT_HEIGHT = 350
DEFAULT_PADDING = 20

# Spacing between days
SPACING_COMFORTABLE = 16
SPACING_MEDIUM = 14
SPACING_COMPACT = 12

# Font size for different event densities
FONT_SIZE_HEADER_SMALL = 13
FONT_SIZE_HEADER_MEDIUM = 14
FONT_SIZE_HEADER_LARGE = 15

FONT_SIZE_EVENT_LARGE = 14
FONT_SIZE_EVENT_MEDIUM = 13
FONT_SIZE_EVENT_SMALL = 12

# Line heights
LINE_HEIGHT_COMPACT = 16
LINE_HEIGHT_NORMAL = 18
LINE_HEIGHT_COMFORTABLE = 20

# Event count thresholds for adaptive sizing
EVENTS_THRESHOLD_SMALL = 6
EVENTS_THRESHOLD_MEDIUM = 12


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
        view_mode="adaptive",
        available_height=DEFAULT_HEIGHT,
        start_offset_days=0,
        show_header=True,
        show_locations=False,
        horizon_mode=False,
        events_per_day=None,
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
        self.padding = DEFAULT_PADDING
        self.width = DEFAULT_WIDTH
        self.available_height = available_height
        self.height = available_height
        self.events_per_day = events_per_day
        self.start_offset_days = start_offset_days
        self.show_header = show_header
        self.horizon_mode = horizon_mode

    def set_width(self, width: int) -> None:
        self.width = width

    def render(self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0):
        """Render the calendar widget with adaptive layout."""
        if self.horizon_mode:
            self._render_horizon_view(display, x_offset, y_offset)
        elif self.view_mode == "adaptive":
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
        if total_events <= EVENTS_THRESHOLD_SMALL:
            font_size_event = FONT_SIZE_EVENT_LARGE
            font_size_header = FONT_SIZE_HEADER_LARGE
            line_height = LINE_HEIGHT_COMFORTABLE
            spacing_between_days = SPACING_COMFORTABLE
        elif total_events <= EVENTS_THRESHOLD_MEDIUM:
            font_size_event = FONT_SIZE_EVENT_MEDIUM
            font_size_header = FONT_SIZE_HEADER_MEDIUM
            line_height = LINE_HEIGHT_NORMAL
            spacing_between_days = SPACING_MEDIUM
        else:
            font_size_event = FONT_SIZE_EVENT_SMALL
            font_size_header = FONT_SIZE_HEADER_SMALL
            line_height = LINE_HEIGHT_COMPACT
            spacing_between_days = SPACING_COMPACT

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
            y_pos = self._render_inverted_header(
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
        y_pos = self._render_inverted_header(display, today, x_pos, y_pos)
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
            y_pos = self._render_inverted_header(display, today, x_pos, y_pos)
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
    def _render_inverted_header(
        self, display, date_obj: datetime, x_pos, y_pos, font_size=15, height=26
    ):
        date_obj = f" TODAY - {date_obj.strftime('%A, %b %d').upper()} "

        rect_width = self.width - 2 * self.padding + 10
        display.draw_rectangle(
            x_pos=x_pos - 10,
            y_pos=y_pos,
            width=rect_width,
            height=height,
            fill="#000000",
            outline="#000000",
        )
        display.draw_text(
            x_pos=x_pos + self.padding,
            y_pos=y_pos + 5,
            text=date_obj,
            font_size=font_size,
            color="#FFFFFF",
        )
        return y_pos + height

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

    def _render_horizon_view(self, display, x_offset, y_offset):
        """
        Render time-aware horizon view optimized for 15-min refresh rate.
        PRIORITY: Show ALL upcoming events - no surprises.
        Past events minimized but visible.
        """
        current_time, now, today_events, tomorrow_events = self._fetch_horizon_events()

        # Categorize today's events by time
        all_day_events, happening_now, past_events, upcoming_today = (
            self._categorize_events_by_time(current_time, today_events)
        )

        # Calculate space budget
        y = y_offset + self.padding
        available_height = self.available_height - self.padding * 2

        # CRITICAL: Reserve space for upcoming events FIRST
        upcoming_count = len(happening_now) + len(upcoming_today)

        # Estimate space needed for upcoming (priority content)
        space_per_upcoming = 23
        space_for_upcoming = upcoming_count * space_per_upcoming
        space_for_now_highlight = 55 if happening_now else 0
        space_for_next_highlight = 50 if upcoming_today else 0
        space_for_all_day = 27 if all_day_events else 0

        # Calculate space remaining for past events
        priority_space = (
            space_for_all_day
            + space_for_now_highlight
            + space_for_next_highlight
            + space_for_upcoming
        )
        remaining_space = available_height - priority_space - 50  # 50 = margins/headers

        # Render all-day events (always visible, compact)
        if all_day_events:
            y = self._render_all_day_banner(display, x_offset, y, all_day_events)
            y += 12

        # HAPPENING NOW - always prominent
        if happening_now:
            for event in happening_now:
                y = self._render_now_event(display, x_offset, y, event, now)
                y += 8

        # NEXT EVENT with countdown - always show first upcoming
        if upcoming_today:
            y = self._render_next_event_with_countdown(
                display, x_offset, y, upcoming_today[0], now
            )
            y += 12

        # ALL REMAINING UPCOMING TODAY - NO SURPRISES
        if len(upcoming_today) > 1:
            display.draw_text(
                x_pos=x_offset + self.padding,
                y_pos=y,
                text="COMING UP TODAY",
                font_size=11,
                color="#666666",
            )
            y += 20

            for event in upcoming_today[1:]:
                y = self._render_event_line_with_time_until(
                    display, x_offset, y, event, now
                )
                y += 23

                # Safety check - if running out of space, continue to tomorrow
                if y > y_offset + available_height - 80:
                    break

        # If nothing left today, show completion message
        elif not happening_now and not upcoming_today:
            display.draw_text(
                x_pos=x_offset + self.padding,
                y_pos=y,
                text="✓ Rest of day is clear",
                font_size=13,
                color="#888888",
            )
            y += 25

        # TOMORROW PREVIEW - always show if events exist
        if tomorrow_events and y < y_offset + available_height - 60:
            y += 8
            display.draw_text(
                x_pos=x_offset + self.padding,
                y_pos=y,
                text="TOMORROW",
                font_size=12,
                color="#666666",
            )
            y += 20

            # Show as many tomorrow events as space allows
            remaining_space = (y_offset + available_height) - y - 40
            max_tomorrow = max(3, remaining_space // 23)

            for event in tomorrow_events[:max_tomorrow]:
                y = self._render_event_line(display, x_offset, y, event, compact=True)
                y += 23

            # Show count if more events
            if len(tomorrow_events) > max_tomorrow:
                display.draw_text(
                    x_pos=x_offset + self.padding,
                    y_pos=y,
                    text=f"+ {len(tomorrow_events) - max_tomorrow} more tomorrow",
                    font_size=10,
                    color="#999999",
                )
                y += 20

        # PAST EVENTS - minimized at bottom if space remains
        if past_events and remaining_space > 40:
            y_past_start = y + 15

            # Collapsible header
            display.draw_text(
                x_pos=x_offset + self.padding,
                y_pos=y_past_start,
                text=f"▼ Earlier ({len(past_events)})",
                font_size=10,
                color="#AAAAAA",
            )
            y_past_start += 18

            # Show up to 3 past events in very compact form
            max_past = min(3, int(remaining_space / 20))
            for event in past_events[-max_past:]:  # Show most recent past events
                display.draw_text(
                    x_pos=x_offset + self.padding + 5,
                    y_pos=y_past_start,
                    text=f"{self._format_time(event['time'])} {event['summary'][:35]}",
                    font_size=10,
                    color="#CCCCCC",
                )
                y_past_start += 18

        return y

    def _categorize_events_by_time(
        self, current_time: time, today_events: list[Any]
    ) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
        """
        Categorize events by their time relative to current time.
        """
        past_events = []
        happening_now = []
        upcoming_today = []
        all_day_events = []

        for event in today_events:
            event_time_str = event.get("time", "")

            if event_time_str == "All Day" or not event_time_str:
                all_day_events.append(event)
                continue

            event_time = self._parse_time(event_time_str)
            if event_time:
                event_end = self._get_event_end_time(event, event_time)

                if event_end < current_time:
                    past_events.append(event)
                elif event_time <= current_time < event_end:
                    happening_now.append(event)
                else:
                    upcoming_today.append(event)
        return all_day_events, happening_now, past_events, upcoming_today

    def _fetch_horizon_events(self) -> tuple[time, datetime, list[Any], list[Any]]:
        """
        Fetch events for today and tomorrow, separated by day.

        Returns:
            tuple(now, current_time, today, tomorrow, today_events, tomorrow_events)
        """
        now = datetime.now()
        current_time = now.time()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Get events for today and tomorrow
        events = self.calendar_service.get_events(
            start_date=today, end_date=tomorrow + timedelta(days=1)
        )

        # Separate today's and tomorrow's events
        today_events = []
        tomorrow_events = []

        for e in events:
            event_date = e["date"]
            if hasattr(event_date, "date"):
                event_date = event_date.date()
            elif isinstance(event_date, str):
                event_date = datetime.strptime(event_date, "%Y-%m-%d").date()

            if event_date == today:
                today_events.append(e)
            elif event_date == tomorrow:
                tomorrow_events.append(e)
        return current_time, now, today_events, tomorrow_events

    def _render_event_line_with_time_until(
        self, display, x_offset, y_offset, event, now
    ):
        """Render event line with 'in X min' indicator"""
        x = x_offset + self.padding

        # Calculate time until
        event_time = self._parse_time(event["time"])
        time_until_text = ""

        if event_time:
            event_datetime = datetime.combine(event["date"], event_time)
            minutes_until = int((event_datetime - now).total_seconds() / 60)

            if minutes_until < 60:
                time_until_text = f" (in {minutes_until}m)"
                time_color = "#FF6600" if minutes_until < 15 else "#666666"
            else:
                time_until_text = f" (in {minutes_until//60}h)"
                time_color = "#666666"
        else:
            time_color = "#666666"

        # Time
        display.draw_text(
            x_pos=x,
            y_pos=y_offset,
            text=self._format_time(event["time"]),
            font_size=11,
            color="#666666",
        )

        # Event summary
        display.draw_text(
            x_pos=x + 65,
            y_pos=y_offset,
            text=event["summary"][:40],  # Truncate if too long
            font_size=12,
            color="#000000",
        )

        # Time until (right-aligned)
        if time_until_text:
            display.draw_text(
                x_pos=x + DEFAULT_HEIGHT,
                y_pos=y_offset,
                text=time_until_text,
                font_size=10,
                color=time_color,
            )

        return y_offset

    def _render_now_event(self, display, x_offset, y_offset, event, now):
        """Render highlighted 'happening now' event"""
        x = x_offset + self.padding

        # Subtle background box
        display.draw_rectangle(
            x_pos=x - 5,
            y_pos=y_offset - 3,
            width=self.width - 2 * self.padding + 10,
            height=50,
            fill="#F5F5F5",
            outline="#000000",
        )

        # "NOW" badge
        display.draw_text(
            x_pos=x,
            y_pos=y_offset + 2,
            text="● NOW",
            font_size=12,  # Changed
            color="#CC0000",
        )

        # Event details
        display.draw_text(
            x_pos=x,
            y_pos=y_offset + 20,
            text=event["summary"],
            font_size=14,  # Changed
            color="#000000",
        )

        # Location if available
        if event.get("location") and self.show_locations:
            display.draw_text(
                x_pos=x + 10,
                y_pos=y_offset + 37,
                text=f"📍 {event['location']}",
                font_size=11,  # Changed
                color="#666666",
            )

        return y_offset + 55

    def _render_next_event_with_countdown(
        self, display, x_offset, y_offset, event, now
    ):
        """Render next event with time until it starts"""
        x = x_offset + self.padding

        # Calculate time until event
        event_time = self._parse_time(event["time"])
        if event_time:
            event_datetime = datetime.combine(event["date"], event_time)
            time_until = event_datetime - now
            minutes_until = int(time_until.total_seconds() / 60)

            # Countdown text
            if minutes_until < 60:
                countdown = f"in {minutes_until} min"
                countdown_color = "#FF6600" if minutes_until < 15 else "#666666"
            else:
                hours = minutes_until // 60
                countdown = f"in {hours}h {minutes_until % 60}m"
                countdown_color = "#666666"

            # "UP NEXT" label
            display.draw_text(
                x_pos=x,
                y_pos=y_offset,
                text="UP NEXT",
                font_size=11,
                color="#666666",
            )

            # Event time and countdown
            display.draw_text(
                x_pos=x,
                y_pos=y_offset + 16,
                text=f"{self._format_time(event['time'])}  •  {countdown}",
                font_size=12,
                color=countdown_color,
            )

            # Event summary
            display.draw_text(
                x_pos=x,
                y_pos=y_offset + 33,
                text=event["summary"],
                font_size=14,
                color="#000000",
            )

            return y_offset + 50

        # Fallback if time parsing fails
        return self._render_event_line(display, x_offset, y_offset, event)

    def _render_events_compact(
        self,
        display,
        x_offset,
        y_offset,
        events,
        max_events=None,
        style="normal",
        show_countdown_to_first=False,
    ):
        """Render events in compact format"""
        y = y_offset

        if max_events:
            events = events[:max_events]

        for idx, event in enumerate(events):
            # Show countdown only for first event if requested
            if idx == 0 and show_countdown_to_first:
                event_time = self._parse_time(event["time"])
                if event_time:
                    now = datetime.now()
                    event_datetime = datetime.combine(event["date"], event_time)
                    minutes_until = int((event_datetime - now).total_seconds() / 60)

                    if 0 < minutes_until < 120:
                        countdown_text = (
                            f" (in {minutes_until}m)"
                            if minutes_until < 60
                            else f" (in {minutes_until//60}h)"
                        )
                        event["_countdown"] = countdown_text

            y = self._render_event_line(display, x_offset, y, event, compact=True)

            # Spacing between events
            y += 23 if style == "normal" else 21

            # Check if we're running out of space
            if y > y_offset + self.available_height - 40:
                remaining = len(events) - idx - 1
                if remaining > 0:
                    display.draw_text(
                        x_pos=x_offset + self.padding,
                        y_pos=y,
                        text=f"+ {remaining} more...",
                        font_size=11,
                        color="#999999",
                    )
                break

        return y

    def _render_event_line(self, display, x_offset, y_offset, event, compact=False):
        """Render a single event line"""
        x = x_offset + self.padding

        # Time
        time_text = self._format_time(event["time"])
        display.draw_text(
            x_pos=x,
            y_pos=y_offset,
            text=time_text,
            font_size=11 if compact else 12,
            color="#666666",
        )

        # Event summary (with optional countdown)
        summary_text = event["summary"]
        if event.get("_countdown"):
            summary_text += event["_countdown"]

        display.draw_text(
            x_pos=x + 65,
            y_pos=y_offset,
            text=summary_text,
            font_size=12 if compact else 14,
            color="#000000",
        )

        return y_offset

    def _render_all_day_banner(self, display, x_offset, y_offset, all_day_events):
        """Render all-day events in a compact banner"""
        x = x_offset + self.padding

        # Combine all-day event names
        event_names = [e["summary"] for e in all_day_events]
        combined_text = " • ".join(event_names)

        # Light grey background
        display.draw_rectangle(
            x_pos=x - 5,
            y_pos=y_offset - 2,
            width=self.width - 2 * self.padding + 10,
            height=22,
            fill="#F5F5F5",
            outline=None,
        )

        # "[AYO]" tag + event names
        display.draw_text(
            x_pos=x,
            y_pos=y_offset + 2,
            text=f"[ALL DAY] {combined_text}",
            font_size=11,
            color="#666666",
        )

        return y_offset + 25

    def _render_section_header(self, display, x_offset, y_offset, text):
        """Render a section header"""
        display.draw_text(
            x_pos=x_offset + self.padding,
            y_pos=y_offset,
            text=text,
            font_size=12,  # Changed from font="roboto_bold_12"
            color="#666666",
        )
        return y_offset + 20

    def _get_event_end_time(self, event, start_time):
        """
        Get event end time. Assumes 1 hour if not specified.
        Can be enhanced to parse duration from event data.
        """
        # Check if event has duration/end time
        if "duration_minutes" in event:
            duration = timedelta(minutes=event["duration_minutes"])
        else:
            # Default 1 hour duration
            duration = timedelta(hours=1)

        # Combine start time with duration
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = start_datetime + duration

        return end_datetime.time()

    def _parse_time(self, time_str):
        """Parse time string to time object"""
        if time_str == "All Day":
            return None

        try:
            time_str = time_str.replace(" ", "").upper()
            if "AM" in time_str or "PM" in time_str:
                return datetime.strptime(time_str, "%I:%M%p").time()
            else:
                return datetime.strptime(time_str, "%H:%M").time()
        except:
            return None

    def _format_time(self, time_str):
        """Format time string to compact 12-hour format."""
        if not time_str or time_str == "All Day":
            return "All Day"

        # Already in 12-hour format
        if "AM" in time_str or "PM" in time_str:
            return time_str.replace(" ", "")

        # Convert 24-hour to 12-hour format
        try:
            if ":" in time_str:
                hour, minute = map(int, time_str.split(":"))
            else:
                hour = int(time_str)
                minute = 0

            period = "AM" if hour < 12 else "PM"
            if hour == 0:
                hour = 12
            elif hour > 12:
                hour = hour - 12

            return f"{hour}:{minute:02d}{period}"
        except (ValueError, AttributeError):
            return time_str

    def _get_font_size(self, font_name):
        """Extract font size from font name like 'roboto_regular_14'"""
        # Map font names to sizes
        font_map = {
            "roboto_bold_16": 16,
            "roboto_bold_14": 14,
            "roboto_bold_12": 12,
            "roboto_bold_11": 11,
            "roboto_medium_14": 14,
            "roboto_medium_12": 12,
            "roboto_medium_11": 11,
            "roboto_regular_14": 14,
            "roboto_regular_12": 12,
            "roboto_regular_11": 11,
        }
        return font_map.get(font_name, 12)
