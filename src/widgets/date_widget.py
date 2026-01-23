from src.widgets.widget_interface import WidgetInterface
from datetime import datetime

class DateWidget(WidgetInterface):
    """
    Display current day of week and date prominently.

    Designed for slow-refresh displays where time is not relevant.
    Emphasizes the information most useful for daily planning.

    Visual hierarchy:
    - Day of week: 32px, black (most prominent)
    - Full date: 24px, dark gray
    - Year: 16px, light gray (subtle)
    """

    def __init__(self):
        """Initialize date widget with fixed height."""
        self.height = 150

    def render(self, display, x_offset, y_offset):
        """
        Render date information with a strong visual hierarchy.

        Args:
            display: Display interface to render to
            x_offset: Horizontal offset for positioning
            y_offset: Vertical offset for positioning
        """
        now = datetime.now()
        display.draw_text(
            x_pos=x_offset + 20, y_pos= y_offset + 20,
            text= now.strftime("%A").upper(),
            font_size=32,
            color="#000000",
        )
        display.draw_text(
            x_pos=x_offset + 20, y_pos=y_offset +60,
            text= now.strftime("%B %d").upper(),
            font_size=24,
            color="#333333",
        )
        display.draw_text(
            x_pos=x_offset + 20, y_pos=y_offset +92,
            text= now.strftime("%Y").upper(),
            font_size=16,
            color="#888888",
        )