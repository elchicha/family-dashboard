import requests
from datetime import datetime


class CalendarService:
    """A Calendar Service"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_todays_events(self):
        response = requests.get("caldav-api-url/calendar")
        data = response.json()

        raw_events = data.get("calendar-data", [])

        events_data = [
            {
                "name": event["summary"],
                "time": self._parse_caldav_time(event["dtstart"]),
            }
            for event in raw_events
        ]

        return events_data

    def _parse_caldav_time(self, dtstart: str) -> str:
        """Parse CalDAV ISO8601 timestamp to HH:MM format"""
        dt = datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
        return dt.strftime("%H:%M")
