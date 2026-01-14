from src.widgets.widget_interface import WidgetInterface


class CalendarWidget(WidgetInterface):
    """A Calendar Widget that uses the calendar and display services to render relevant information in the dashboard."""

    def __init__(self, display, calendar_service):
        self.display = display
        self.calendar_service = calendar_service

    def render(self, x_offset: int = 0, y_offset: int = 0):
        """Render calendar events at offset position"""
        events = self.calendar_service.get_todays_events()
        y_position = 10 + y_offset

        for event in events:
            event_detail = f"{event["time"]}: {event["name"]}"
            self.display.draw_text(
                x_pos=10 + x_offset, y_pos=y_position, text=event_detail, font_size=20
            )
            y_position += 30
