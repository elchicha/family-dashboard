import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
from src.services.calendar_service import CalendarService


class TestCalendarService:

    @pytest.fixture
    def mock_caldav_client(self):
        """Mock CalDAV client"""
        with patch("src.services.calendar_service.caldav.DAVClient") as mock:
            yield mock

    @pytest.fixture
    def mock_vevent_data(self):
        """Sample VEVENT data from CalDAV"""
        return [
            {
                "uid": "event-123",
                "summary": "Team Meeting",
                "dtstart": "20260112T100000Z",
            },
            {
                "uid": "event-456",
                "summary": "Lunch",
                "dtstart": "20260112T120000Z",
            },
        ]

    def test_calendar_service_initializes_with_credentials(self, mock_caldav_client):
        """CalendarService should initialize with CalDAV credentials"""
        service = CalendarService(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="app-specific-password",
        )

        assert service.url == "https://caldav.icloud.com/"
        assert service.username == "test@icloud.com"
        assert service.password == "app-specific-password"

        # Should create CalDAV client
        mock_caldav_client.assert_called_once_with(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="app-specific-password",
        )

    def test_get_events_returns_event_list(self, mock_caldav_client, mock_vevent_data):
        """Should fetch and parse events from CalDAV"""
        # Setup mock to return events
        mock_principal = Mock()
        mock_calendar = Mock()
        mock_events = []

        for event_data in mock_vevent_data:
            mock_event = Mock()
            mock_event.data = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:{event_data['uid']}
SUMMARY:{event_data['summary']}
DTSTART:{event_data['dtstart']}
END:VEVENT
END:VCALENDAR"""
            mock_events.append(mock_event)

        mock_calendar.date_search.return_value = mock_events
        mock_principal.calendars.return_value = [mock_calendar]
        mock_caldav_client.return_value.principal.return_value = mock_principal

        service = CalendarService(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="test-password",
        )

        today = date(2026, 1, 12)
        events = service.get_events(today)

        assert len(events) == 2
        assert events[0]["summary"] == "Team Meeting"
        assert events[0]["time"] == "10:00"
        assert events[1]["summary"] == "Lunch"
        assert events[1]["time"] == "12:00"

    def test_parse_vevent_extracts_summary_and_time(self, mock_caldav_client):
        """Should parse VEVENT data correctly"""
        service = CalendarService(
            url="https://caldav.icloud.com/",
            username="test@icloud.com",
            password="test-password",
        )

        vevent_data = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event-789
SUMMARY:Standup
DTSTART:20260112T090000Z
END:VEVENT
END:VCALENDAR"""

        event = service._parse_vevent(vevent_data)

        assert event["summary"] == "Standup"
        assert event["time"] == "09:00"
        assert event["uid"] == "event-789"
