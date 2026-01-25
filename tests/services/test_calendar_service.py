"""Tests for CalendarService."""

import pytest
from datetime import datetime, date, timedelta
from src.services.calendar_service import CalendarService


class TestCalendarService:
    """Test CalendarService with public .ics feeds."""

    def test_calendar_service_fetches_from_public_ics(self, mocker):
        """Should fetch events from public .ics URL without credentials."""
        # Mock the HTTP request
        mock_response = mocker.Mock()
        mock_response.content = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20250122T090000Z
DTEND:20250122T100000Z
SUMMARY:Team Meeting
UID:test123
LOCATION:Conference Room A
END:VEVENT
END:VCALENDAR"""
        mock_response.raise_for_status = mocker.Mock()

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        service = CalendarService(
            url="https://calendar.google.com/calendar/ical/example/basic.ics"
        )

        events = service.get_events(
            start_date=date(2025, 1, 22), end_date=date(2025, 1, 22)
        )

        assert len(events) == 1
        assert events[0]["summary"] == "Team Meeting"
        assert events[0]["location"] == "Conference Room A"
        assert events[0]["uid"] == "test123_2025-01-22"
        mock_get.assert_called_once()

    def test_parses_all_day_events(self, mocker):
        """Should handle all-day events (VALUE=DATE)."""
        mock_response = mocker.Mock()
        mock_response.content = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250122
DTEND;VALUE=DATE:20250123
SUMMARY:All Day Event
UID:allday123
END:VEVENT
END:VCALENDAR"""
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("requests.get", return_value=mock_response)

        service = CalendarService(url="https://example.com/cal.ics")
        events = service.get_events(
            start_date=date(2025, 1, 22), end_date=date(2025, 1, 22)
        )

        assert len(events) == 1
        assert events[0]["summary"] == "All Day Event"
        assert events[0]["time"] == "All Day"

    def test_filters_events_by_date_range(self, mocker):
        """Should only return events within date range."""
        mock_response = mocker.Mock()
        mock_response.content = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20250122T090000Z
SUMMARY:Event 1
UID:1
END:VEVENT
BEGIN:VEVENT
DTSTART:20250124T100000Z
SUMMARY:Event 2
UID:2
END:VEVENT
END:VCALENDAR"""
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("requests.get", return_value=mock_response)

        service = CalendarService(url="https://example.com/cal.ics")

        # Only fetch Jan 22
        events = service.get_events(
            start_date=date(2025, 1, 22), end_date=date(2025, 1, 22)
        )

        assert len(events) == 1
        assert events[0]["summary"] == "Event 1"

    def test_sorts_events_by_date_and_time(self, mocker):
        """Should return events sorted by date then time."""
        mock_response = mocker.Mock()
        mock_response.content = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20250122T140000Z
SUMMARY:Afternoon
UID:2
END:VEVENT
BEGIN:VEVENT
DTSTART:20250122T090000Z
SUMMARY:Morning
UID:1
END:VEVENT
BEGIN:VEVENT
DTSTART:20250123T090000Z
SUMMARY:Tomorrow
UID:3
END:VEVENT
END:VCALENDAR"""
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("requests.get", return_value=mock_response)

        service = CalendarService(url="https://example.com/cal.ics")
        events = service.get_events(
            start_date=date(2025, 1, 22), end_date=date(2025, 1, 23)
        )

        assert len(events) == 3
        assert events[0]["summary"] == "Morning"
        assert events[1]["summary"] == "Afternoon"
        assert events[2]["summary"] == "Tomorrow"
