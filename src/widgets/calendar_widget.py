"""Calendar widget for displaying daily events in E-Ink dashboard."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from src.services.event_categorizer import EventCategory, EventCategorizer
from src.widgets.widget_interface import WidgetInterface


class CalendarWidget(WidgetInterface):
    """
    Calendar widget with multiple view modes for E-Ink displays.

    View Modes:
    - single_day: Shows one day with full event details (time, title, location)
    - three_day: Shows 3 days (today + 2) in compact format (no locations)

    Features:
    - Date headers with day names
    - Grayscale hierarchy for readability
    - Event truncation for long days
    - Graceful handling of empty days

    Optimized for 480px wide column in two-column layout.
    """

    def __init__(
            self,
            calendar_service,
            view_mode: str = "single_day",
            max_events: int = 4,
            events_per_day: int = 3,
            show_locations: bool = True
    ):
        """
        Initialize calendar widget.

        Args:
            calendar_service: Service to fetch calendar events
            view_mode: "single_day" or "three_day"
            max_events: Max events in single_day mode
            events_per_day: Max events per day in three_day mode
            show_locations: Whether to show locations (single_day only)
        """
        self.calendar_service = calendar_service
        self.view_mode = view_mode
        self.max_events = max_events
        self.events_per_day = events_per_day
        self.show_locations = show_locations

        # Set height based on view mode
        if view_mode == "three_day":
            self.height = 480
        else:
            self.height = 350

    def render(self, display, x_offset: int = 0, y_offset: int = 0):
        """
        Render calendar based on view mode.

        Args:
            display: Display interface to render to
            x_offset: Horizontal offset for positioning
            y_offset: Vertical offset for positioning
        """
        if self.view_mode == "three_day":
            self._render_three_day_view(display, x_offset, y_offset)
        else:
            self._render_single_day_view(display, x_offset, y_offset)

    def _render_single_day_view(self, display, x_offset: int, y_offset: int):
        """Render original single-day view with full details."""
        padding_left = 15
        padding_top = 20

        y_pos = padding_top + y_offset

        # Render date header
        y_pos = self._render_header(display, x_offset + padding_left, y_pos)
        y_pos += 15

        # Get events from service with date range
        today = datetime.now().date()
        events = self.calendar_service.get_events(
            start_date=today,
            end_date=today
        ) if self.calendar_service else []

        if not events:
            self._render_no_events(display, x_offset + padding_left, y_pos)
            return

        # Render events (up to max_events)
        events_to_show = events[:self.max_events]
        remaining = len(events) - len(events_to_show)

        for event in events_to_show:
            y_pos = self._render_event(
                display,
                event,
                x_offset + padding_left,
                y_pos
            )
            y_pos += 10

        # Show truncation indicator if needed
        if remaining > 0:
            self._render_truncation_indicator(
                display,
                remaining,
                x_offset + padding_left,
                y_pos
            )

    def _render_three_day_view(self, display, x_offset: int, y_offset: int):
        """Render glanceable 3-day view with smart grouping."""
        padding_left = 15
        padding_top = 20

        y_pos = padding_top + y_offset

        # Get all events with proper date range (today + 2 days)
        today = datetime.now().date()
        all_events = self.calendar_service.get_events(
            start_date=today,
            end_date=today + timedelta(days=2)
        ) if self.calendar_service else []

        # Categorize all events
        categorized_events = []
        for event in all_events:
            category = EventCategorizer.categorize(event)
            categorized_events.append({
                'event': event,
                'category': category
            })

        # Group events by date
        today_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_show = [
            (today_dt, "TODAY"),
            (today_dt + timedelta(days=1), "TOMORROW"),
            (today_dt + timedelta(days=2), None),
        ]

        first_day = True

        for day_index, (date, label) in enumerate(days_to_show):
            # Get events for this day
            day_events = [
                item for item in categorized_events
                if item['event'].get("date", today_dt).date() == date.date()
            ]

            if not day_events:
                continue  # Skip days with no events

            # Add divider between days (but not before first day)
            if not first_day:
                y_pos = self._render_divider(display, x_offset, y_pos, width=450)
                y_pos += 15
            first_day = False

            # Sort by category priority, then by time
            day_events.sort(key=lambda x: (
                EventCategorizer.get_category_priority(x['category']),
                x['event']['time']
            ))

            # Render day header
            y_pos = self._render_day_header_smart(
                display,
                date,
                label,
                x_offset + padding_left,
                y_pos,
                day_index
            )
            y_pos += 8

            # Group events by category
            events_by_category = {}
            for item in day_events:
                cat = item['category']
                if cat not in events_by_category:
                    events_by_category[cat] = []
                events_by_category[cat].append(item['event'])

            # Render each category
            y_pos = self._render_categorized_events(
                display,
                events_by_category,
                x_offset + padding_left,
                y_pos
            )

            y_pos += 10  # Space after day's events

    def _render_divider(self, display, x_offset: int, y_pos: int, width: int = 450) -> int:
        """Render a horizontal divider line."""
        # Draw a thin line
        display.draw_line(
            x1=x_offset + 15,
            y1=y_pos,
            x2=x_offset + width,
            y2=y_pos,
            color="#CCCCCC",
            width=1
        )
        return y_pos

    def _render_day_header_smart(
            self,
            display,
            date: datetime,
            label: Optional[str],
            x_pos: int,
            y_pos: int,
            day_index: int
    ) -> int:
        """Render clean day header with visual prominence."""
        # Make today stand out more
        if day_index == 0:
            color = "#000000"
            font_size = 22  # Increased from 18
        else:
            color = "#444444"
            font_size = 20  # Increased from 16

        if label:
            header = f"{label} - {date.strftime('%a').upper()} {date.strftime('%b %d').upper()}"
        else:
            header = date.strftime("%a %b %d").upper()

        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=header,
            font_size=font_size,
            color=color,
        )

        return y_pos + 28  # Increased from 25

    def _render_categorized_events(
            self,
            display,
            events_by_category: dict,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render events grouped by category with smart formatting."""

        # Schedule (most important - show prominently)
        if EventCategory.SCHEDULE in events_by_category:
            schedules = events_by_category[EventCategory.SCHEDULE]
            schedule_text = ", ".join([e['summary'] for e in schedules])

            display.draw_text(
                x_pos=x_pos + 5,
                y_pos=y_pos,
                text=f"SCHEDULE: {schedule_text}",
                font_size=20,  # Increased from 16
                color="#000000",
            )
            y_pos += 28  # Increased from 24

        # No School (very important)
        if EventCategory.NO_SCHOOL in events_by_category:
            for event in events_by_category[EventCategory.NO_SCHOOL]:
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"NO SCHOOL - {event['summary']}",
                    font_size=20,  # Increased from 16
                    color="#000000",
                )
                y_pos += 28  # Increased from 24

        # Family Events (with times)
        if EventCategory.FAMILY_EVENT in events_by_category:
            events = events_by_category[EventCategory.FAMILY_EVENT]

            # Show header only if there are events
            if events:
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text="EVENTS:",
                    font_size=17,  # Increased from 14
                    color="#555555",
                )
                y_pos += 24  # Increased from 20

                for event in events[:3]:  # Limit to 3 events
                    time_str = self._format_time(event["time"])
                    display.draw_text(
                        x_pos=x_pos + 15,
                        y_pos=y_pos,
                        text=f"{time_str} - {event['summary']}",
                        font_size=18,  # Increased from 15
                        color="#000000",
                    )
                    y_pos += 26  # Increased from 22

                # Show "more" indicator if needed
                if len(events) > 3:
                    display.draw_text(
                        x_pos=x_pos + 15,
                        y_pos=y_pos,
                        text=f"+{len(events) - 3} more",
                        font_size=14,  # Increased from 12
                        color="#999999",
                    )
                    y_pos += 20  # Increased from 18

        # Ongoing (less prominent)
        if EventCategory.ONGOING in events_by_category:
            ongoing = events_by_category[EventCategory.ONGOING]
            if ongoing:
                ongoing_text = ", ".join([e['summary'] for e in ongoing[:2]])
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"Ongoing: {ongoing_text}",
                    font_size=15,  # Increased from 12
                    color="#888888",
                )
                y_pos += 22  # Increased from 18

        # Deadlines
        if EventCategory.DEADLINE in events_by_category:
            for event in events_by_category[EventCategory.DEADLINE]:
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"DEADLINE: {event['summary']}",
                    font_size=18,  # Increased from 15
                    color="#CC0000",
                )
                y_pos += 26  # Increased from 22

        return y_pos
    def _render_day_header_smart(
            self,
            display,
            date: datetime,
            label: Optional[str],
            x_pos: int,
            y_pos: int,
            day_index: int
    ) -> int:
        """Render clean day header."""
        colors = ["#000000", "#333333", "#666666"]
        color = colors[day_index]

        if label:
            header = f"{label} - {date.strftime('%a %b %d').upper()}"
        else:
            header = date.strftime("%a %b %d").upper()

        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=header,
            font_size=16,
            color=color,
        )

        return y_pos + 22

    def _render_categorized_events(
            self,
            display,
            events_by_category: dict,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render events grouped by category with smart formatting."""

        # Schedule (most important - show prominently)
        if EventCategory.SCHEDULE in events_by_category:
            schedules = events_by_category[EventCategory.SCHEDULE]

            for schedule in schedules:
                source_tag = f"[{schedule.get('source', '')}] " if schedule.get('source') else ""
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"{source_tag}SCHEDULE: {schedule['summary']}",
                    font_size=20,
                    color="#000000",
                )
                y_pos += 28

        # No School (very important)
        if EventCategory.NO_SCHOOL in events_by_category:
            for event in events_by_category[EventCategory.NO_SCHOOL]:
                source_tag = f"[{event.get('source', '')}] " if event.get('source') else ""
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"{source_tag}NO SCHOOL - {event['summary']}",
                    font_size=20,
                    color="#000000",
                )
                y_pos += 28

        # Family Events (with times)
        if EventCategory.FAMILY_EVENT in events_by_category:
            events = events_by_category[EventCategory.FAMILY_EVENT]

            # Show header only if there are events
            if events:
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text="EVENTS:",
                    font_size=17,
                    color="#555555",
                )
                y_pos += 24

                for event in events[:3]:  # Limit to 3 events
                    time_str = self._format_time(event["time"])
                    source_tag = f"[{event.get('source', '')}]" if event.get('source') else ""

                    display.draw_text(
                        x_pos=x_pos + 15,
                        y_pos=y_pos,
                        text=f"{time_str} {source_tag} {event['summary']}",
                        font_size=18,
                        color="#000000",
                    )
                    y_pos += 26

                # Show "more" indicator if needed
                if len(events) > 3:
                    display.draw_text(
                        x_pos=x_pos + 15,
                        y_pos=y_pos,
                        text=f"+{len(events) - 3} more",
                        font_size=14,
                        color="#999999",
                    )
                    y_pos += 20

        # Ongoing (less prominent)
        if EventCategory.ONGOING in events_by_category:
            ongoing = events_by_category[EventCategory.ONGOING]
            if ongoing:
                # Group by source
                ongoing_text = ", ".join([
                    f"[{e.get('source', '')}] {e['summary']}" if e.get('source') else e['summary']
                    for e in ongoing[:2]
                ])
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"Ongoing: {ongoing_text}",
                    font_size=15,
                    color="#888888",
                )
                y_pos += 22

        # Deadlines
        if EventCategory.DEADLINE in events_by_category:
            for event in events_by_category[EventCategory.DEADLINE]:
                source_tag = f"[{event.get('source', '')}] " if event.get('source') else ""
                display.draw_text(
                    x_pos=x_pos + 5,
                    y_pos=y_pos,
                    text=f"{source_tag}DEADLINE: {event['summary']}",
                    font_size=18,
                    color="#CC0000",
                )
                y_pos += 26

        return y_pos
    # ========== Single-Day View Rendering Methods ==========

    def _render_header(
            self,
            display,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render date header for single-day view."""
        now = datetime.now()

        # Day name (e.g., "MONDAY")
        day_str = now.strftime("%A").upper()
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=day_str,
            font_size=20,
            color="#666666",
        )

        # Date (e.g., "JAN 20")
        date_str = now.strftime("%b %d").upper()
        display.draw_text(
            x_pos=x_pos + 120,
            y_pos=y_pos,
            text=date_str,
            font_size=20,
            color="#666666",
        )

        return y_pos + 30

    def _render_event(
            self,
            display,
            event: dict,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render a single event with full details."""
        time_str = self._format_time(event["time"])

        # Render time and title on same line
        event_line = f"{time_str}  {event['summary']}"
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=event_line,
            font_size=18,
            color="#000000",
        )

        y_pos += 24

        # Render location if present and enabled
        if self.show_locations and "location" in event and event["location"]:
            display.draw_text(
                x_pos=x_pos + 20,
                y_pos=y_pos,
                text=event["location"],
                font_size=14,
                color="#888888",
            )
            y_pos += 20

        return y_pos

    def _render_no_events(
            self,
            display,
            x_pos: int,
            y_pos: int
    ) -> None:
        """Render message when no events scheduled."""
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text="No events today",
            font_size=16,
            color="#999999",
        )

    def _render_truncation_indicator(
            self,
            display,
            remaining: int,
            x_pos: int,
            y_pos: int
    ) -> None:
        """Render indicator showing how many events are hidden."""
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=f"+{remaining} more event{'s' if remaining > 1 else ''}",
            font_size=14,
            color="#999999",
        )

    # ========== Three-Day Compact View Rendering Methods ==========

    def _render_day_header_compact(
            self,
            display,
            date: datetime,
            label: Optional[str],
            x_pos: int,
            y_pos: int,
            day_index: int
    ) -> int:
        """Render compact day header with grayscale hierarchy."""
        colors = ["#000000", "#555555", "#888888"]
        color = colors[day_index]

        if label:
            header = f"{label} - {date.strftime('%a %b %d').upper()}"
        else:
            header = date.strftime("%a %b %d").upper()

        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=header,
            font_size=16,
            color=color,
        )

        return y_pos + 22

    def _render_event_compact(
            self,
            display,
            event: dict,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render single event in compact format."""
        time_str = self._format_time(event["time"])
        event_line = f"{time_str}  {event['summary']}"  # Removed the bullet point

        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=event_line,
            font_size=14,
            color="#000000",
        )

        return y_pos + 20

    def _render_no_events_compact(
            self,
            display,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render 'no events' message in compact format."""
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text="No events",  # Removed the bullet point
            font_size=14,
            color="#AAAAAA",
        )
        return y_pos + 20

    def _render_truncation_compact(
            self,
            display,
            remaining: int,
            x_pos: int,
            y_pos: int
    ) -> int:
        """Render truncation indicator in compact format."""
        display.draw_text(
            x_pos=x_pos,
            y_pos=y_pos,
            text=f"  +{remaining} more",
            font_size=12,
            color="#999999",
        )
        return y_pos + 18

    # ========== Utility Methods ==========

    def _format_time(self, time_str: str) -> str:
        """Format time string to 12-hour format."""
        if "AM" in time_str or "PM" in time_str:
            return time_str

        try:
            hour, minute = map(int, time_str.split(":"))
            period = "AM" if hour < 12 else "PM"
            if hour == 0:
                hour = 12
            elif hour > 12:
                hour = hour - 12

            return f"{hour}:{minute:02d} {period}"
        except (ValueError, AttributeError):
            return time_str