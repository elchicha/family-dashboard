"""CalDAV calendar service for fetching VEVENT items."""
from typing import Optional
from datetime import datetime, date, timedelta
import caldav
from icalendar import Calendar


class CalendarService:
    """CalDAV calendar service for fetching VEVENT items."""

    def __init__(self, url: str, username: Optional[str] = None, password: Optional[str] = None, source_name: Optional[str] = None):
        """
        Initialize calendar service.

        Args:
            url: CalDAV URL or direct .ics URL
            username: Optional username for authenticated calendars
            password: Optional password for authenticated calendars
            source_name: Optional name to tag events with (e.g., "Arroyo", "SFHS")
        """
        self.url = url
        self.username = username
        self.password = password
        self.source_name = source_name

        # Only create client if credentials provided (for CalDAV)
        if username and password:
            self.client = caldav.DAVClient(url=url, username=username, password=password)
        else:
            self.client = None

    def get_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[dict]:
        """
        Fetch events within a date range.

        Args:
            start_date: Start date (defaults to today)
            end_date: End date (defaults to today)

        Returns:
            List of event dictionaries with summary, time, date, uid, location
        """
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date

        # If using CalDAV
        if self.client:
            return self._fetch_from_caldav(start_date, end_date)
        # If using direct .ics URL (like Google Calendar public feed)
        else:
            return self._fetch_from_ics_url(start_date, end_date)

    def _fetch_from_caldav(self, start_date: date, end_date: date) -> list[dict]:
        """Fetch events from CalDAV server."""
        principal = self.client.principal()
        calendars = principal.calendars()

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())

        events = []
        for calendar in calendars:
            for event in calendar.date_search(start=start, end=end):
                parsed = self._parse_vevent(event.data)
                if parsed:
                    events.append(parsed)

        return sorted(events, key=lambda e: (e['date'], e['time']))

    def _fetch_from_ics_url(self, start_date: date, end_date: date) -> list[dict]:
        """Fetch and parse events from a public .ics URL."""
        import requests

        response = requests.get(self.url)
        response.raise_for_status()

        cal = Calendar.from_ical(response.content)
        events = []

        for component in cal.walk('VEVENT'):
            parsed_events = self._parse_ical_event(component, start_date, end_date)
            if parsed_events:
                # Add source name to each event
                for event in parsed_events:
                    if self.source_name:
                        event['source'] = self.source_name
                events.extend(parsed_events)

        return sorted(events, key=lambda e: (e['date'], e['time']))

    def _parse_ical_event(
            self,
            component,
            start_date: date,
            end_date: date
    ) -> list[dict]:
        """Parse an iCalendar event component, expanding multi-day events."""
        try:
            # Get start date/time
            dtstart = component.get('DTSTART')
            if not dtstart:
                return []

            dt = dtstart.dt

            # Get end date/time
            dtend = component.get('DTEND')

            # Handle all-day events (date objects)
            if isinstance(dt, date) and not isinstance(dt, datetime):
                event_start_date = dt
                time_str = "All Day"

                # For all-day events, check if it's a multi-day event
                if dtend:
                    event_end_date = dtend.dt
                    if isinstance(event_end_date, datetime):
                        event_end_date = event_end_date.date()
                    # For multi-day all-day events, the end date in iCal is exclusive
                    # So we subtract one day to get the actual last day
                    event_end_date = event_end_date - timedelta(days=1)
                else:
                    event_end_date = event_start_date

            else:
                # Handle datetime objects with timezone conversion
                event_start_date = dt.date()
                event_end_date = event_start_date  # Single-day event

                # Convert to local timezone if needed
                if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                    # Convert to local time
                    import pytz
                    local_tz = pytz.timezone('America/Los_Angeles')  # Pacific Time
                    if dt.tzinfo != local_tz:
                        dt = dt.astimezone(local_tz)

                time_str = dt.strftime("%-I:%M %p")  # e.g., "4:05 PM" (no leading zero)

            # Check if the event overlaps with our date range
            if event_end_date < start_date or event_start_date > end_date:
                return []

            # Extract event details
            summary = str(component.get('SUMMARY', 'Untitled Event'))
            uid = str(component.get('UID', ''))
            location = str(component.get('LOCATION', '')) if component.get('LOCATION') else None

            # Generate one event instance per day in the range
            events = []
            current_date = max(event_start_date, start_date)
            last_date = min(event_end_date, end_date)

            while current_date <= last_date:
                events.append({
                    'summary': summary,
                    'time': time_str,
                    'date': datetime.combine(current_date, datetime.min.time()),
                    'uid': f"{uid}_{current_date.isoformat()}",
                    'location': location,
                })

                current_date += timedelta(days=1)

            return events

        except Exception as e:
            # Skip events that fail to parse
            print(f"Warning: Failed to parse event: {e}")
            return []
    def _parse_vevent(self, vevent_string: str) -> Optional[dict]:
        """Parse a VEVENT string (for CalDAV)."""
        try:
            cal = Calendar.from_ical(vevent_string)
            for component in cal.walk('VEVENT'):
                # Reuse the same parsing logic
                return self._parse_ical_event(
                    component,
                    date.today(),
                    date.today() + timedelta(days=365)
                )
        except Exception as e:
            print(f"Warning: Failed to parse vevent: {e}")
            return None