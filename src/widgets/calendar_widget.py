from src.widgets.widget_interface import WidgetInterface


class CalendarWidget(WidgetInterface):
    """A Calendar Widget that uses the calendar and display services to render relevant information in the dashboard."""

    def __init__(self, calendar_service):
        self.calendar_service = calendar_service
        self.height = 300

    def render(self, display, x_offset: int = 0, y_offset: int = 0):
        """Render calendar events at offset position"""
        padding_left = 15
        padding_top = 20

        y_position = padding_top + y_offset

        y_position = self._render_header(display, x_offset + padding_left, y_position)

        events = self.calendar_service.get_events()
        y_position = 10 + y_offset

        for event in events:
            event_detail = f"{event["time"]}: {event["summary"]}"
            display.draw_text(
                x_pos=10 + x_offset, y_pos=y_position, text=event_detail, font_size=20
            )
            y_position += 30

    def _render_header(self, display, x_position: int, y_position: int) -> int:
        now = datetime.now()
        day_str = now.strftime("%A").upper()
        display.draw_text(x_pos=x_position, y_pos=y_position, text=day_str, font_size=20, color="#666666",)

        return y_position + 30

    def _render_event(self,display, event: dict,x_position: int, y_position: int) -> int:
        """Render a single event.

        Args:
            display: Display interface to render to
            event: Event dict with 'time', 'summary', optional 'location'
            x_position: Horizontal position to render
            y_position: Vertical position to render

        Returns:
            New vertical position after rendering event
            """
        time_str = event["time"]
        event_line = f"{time_str} {event['summary']}"
        display.draw_text(x_pos=x_position, y_pos=y_position, text=event_line, font_size=20, color="#000000")
        y_position += 24

        if "location" in event:
            display.draw_text(x_pos=x_position, y_pos=y_position, text=event["location"], font_size=14, color="#888888")
            y_position += 20


        return y_position