# tests/test_calendar_service.py
import pytest
from src.services.calendar_service import CalendarService


class TestCalendarService:

    @pytest.fixture
    def calendar_service(self):
        return CalendarService(api_key="test_key")

    def test_get_todays_events_returns_event_list(self, calendar_service, mocker):
        """Should fetch and parse today's events from CalDAV"""
        fake_caldav_response = {
            "calendar-data": [
                {
                    "uid": "event-123",
                    "summary": "Team Meeting",
                    "dtstart": "20260112T100000Z",
                    "location": "Conference Room",
                },
                {
                    "uid": "event-456",
                    "summary": "Lunch",
                    "dtstart": "20260112T120000Z",
                    "location": "Cafeteria",
                },
            ]
        }

        mock_get = mocker.patch("src.services.calendar_service.requests.get")
        mock_get.return_value.json.return_value = fake_caldav_response
        mock_get.return_value.status_code = 200

        events = calendar_service.get_todays_events()

        assert events is not None
        assert len(events) == 2
        assert events[0]["name"] == "Team Meeting"
        assert events[0]["time"] == "10:00"  # Parsed from ISO timestamp
        assert events[1]["name"] == "Lunch"
        assert events[1]["time"] == "12:00"

    def test_get_todays_events_parses_caldav_timestamps(self, calendar_service, mocker):
        """Should parse CalDAV ISO8601 timestamps correctly"""
        fake_caldav_response = {
            "calendar-data": [
                {
                    "uid": "event-789",
                    "summary": "Standup",
                    "dtstart": "20260112T090000Z",
                    "location": "Zoom",
                },
                {
                    "uid": "event-101",
                    "summary": "Deploy",
                    "dtstart": "20260112T160000Z",
                    "location": "Production",
                },
            ]
        }

        mock_get = mocker.patch("src.services.calendar_service.requests.get")
        mock_get.return_value.json.return_value = fake_caldav_response
        mock_get.return_value.status_code = 200

        events = calendar_service.get_todays_events()

        assert len(events) == 2
        assert events[0]["name"] == "Standup"
        assert events[0]["time"] == "09:00"
        assert events[1]["name"] == "Deploy"
        assert events[1]["time"] == "16:00"
