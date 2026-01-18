from datetime import datetime

from src.display.display_interface import DisplayInterface
from src.widgets.widget_interface import WidgetInterface


class ClockWidget(WidgetInterface):
    """Widget that displays current time and date.

    Shows large time at top with date below in grayscale hierarchy.
    """

    def render(
        self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0
    ) -> None:
        """Render current time and date to display.

        Args:
            display: Display interface to render to
            x_offset: Horizontal offset for positioning
            y_offset: Vertical offset for positioning
        """
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")  # "02:30 PM"
        display.draw_text(
            x_pos=10 + x_offset,
            y_pos=10 + y_offset,
            text=time_str,
            font_size=100,
            color="#000000",
        )

        date_str = now.strftime("%A, %B %-d, %Y")
        display.draw_text(
            x_pos=10 + x_offset,
            y_pos=110 + y_offset,
            text=date_str,
            font_size=70,
            color="#444444",
        )
