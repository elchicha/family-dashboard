from src.display.display_interface import DisplayInterface
from src.services.calendar_service import CalendarService


class CalendarWidget:
    """A Calendar Widget that uses the calendar and display services to render relevant information in the dashboard."""

    def __init__(self, display: DisplayInterface, calendar_service: CalendarService):
        self.display = display
        self.calendar_service = calendar_service

    def render(self):
        events = self.calendar_service.get_todays_events()
        for event in events:
            event_detail = f"{event["time"]}: {event["name"]}"
            self.display.draw_text(0, 0, event_detail)
