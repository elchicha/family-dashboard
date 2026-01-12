# tests/test_calendar_service.py
import pytest
from src.services.calendar_service import CalendarService


class TestCalendarService:

    @pytest.fixture
    def calendar_service(self):
        return CalendarService(api_key="test_key")

    def test_get_todays_events_returns_event_list(self, calendar_service, mocker):
        """Should fetch and parse today's events"""
        # TODO: Create fake API response data
        # Hint: Imagine what a calendar API returns
        fake_events = [
            {"name": "Team Meeting", "time": "10:00"},
            {"name": "Lunch", "time": "12:00"}
        ]

        # TODO: Mock requests.get to return your fake data
        # Hint: Use what you learned from weather service

        # TODO: Call calendar_service.get_todays_events()

        # TODO: Assert the results match your fake data