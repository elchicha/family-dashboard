from typing import Optional

import caldav
from datetime import datetime, date


class CalendarService:
    """CalDAV calendar service for fetching VEVENT items."""

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.client = caldav.DAVClient(url=url, username=username, password=password)

    def get_events(self, events_date: Optional[date] = None) -> list[dict[str, str]]:
        """Fetch all events for a specific day"""
        if events_date is None:
            events_date = date.today()
        principal = self.client.principal()
        calendars = principal.calendars()

        start = datetime.combine(events_date, datetime.min.time())  # 00:00:00
        end = datetime.combine(events_date, datetime.max.time())  # 23:59:59

        return [
            self._parse_vevent(event.data)
            for calendar in calendars
            for event in calendar.date_search(start=start, end=end)
        ]

    def _parse_vevent(self, vevent_string: str) -> dict[str, str]:
        event = {}
        for line in vevent_string.split("\n"):
            line = line.strip()
            if line.startswith("SUMMARY:"):
                event["summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("UID:"):
                event["uid"] = line.split(":", 1)[1].strip()
            elif line.startswith("DTSTART:"):
                event["time"] = self._parse_caldav_time(line.split(":", 1)[1].strip())

        return event

    def _parse_caldav_time(self, dtstart: str) -> str:
        """Parse CalDAV ISO8601 timestamp to HH:MM format"""
        dt = datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
        return dt.strftime("%H:%M")
