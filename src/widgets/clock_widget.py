from datetime import datetime

from src.display.display_interface import DisplayInterface
from src.widgets.widget_interface import WidgetInterface


class ClockWidget(WidgetInterface):
    """Widget that displays current time and date.

    Shows large time at top with date below in grayscale hierarchy.
    """

    def __init__(self, hourly_format: bool = False):
        """Initialize the clock widget.

        Args:
            hourly_format : If True, shows "03 PM" instead of "03:27 PM" (for hourly updates to save power)
        """
        self.height = 200
        self.hourly_format = hourly_format

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
        # Padding from edge and between elements
        padding_left = 15
        padding_top = 20
        line_spacing = 8

        # Y positions for each element (stacked vertically)
        y_day = padding_top + y_offset
        y_date = y_day + 24 + line_spacing  # Day font + spacing
        y_time = y_date + 32 + line_spacing + 10  # Date font + extra space

        # Day name (e.g., "MONDAY") - Small, light gray, uppercase
        day_str = now.strftime("%A").upper()
        display.draw_text(
            x_pos=padding_left + x_offset,
            y_pos=y_day,
            text=day_str,
            font_size=20,  # Small and unobtrusive
            color="#808080",  # Medium gray (128 in 0-255) for E-Ink
        )

        # Date (e.g., "JAN 19") - Medium size, dark gray, abbreviated
        date_str = now.strftime("%b %d").upper()  # "JAN 19"
        display.draw_text(
            x_pos=padding_left + x_offset,
            y_pos=y_date,
            text=date_str,
            font_size=28,  # Readable but not dominant
            color="#555555",  # Dark gray (85 in 0-255) for E-Ink
        )

        # Time - Large, black, primary focus
        if self.hourly_format:
            time_str = now.strftime("%I %p")  # "03 PM" (no minutes)
        else:
            time_str = now.strftime("%I:%M %p")  # "03:27 PM"

        # Remove leading zero from hour (e.g., "3:27 PM" not "03:27 PM")
        time_str = time_str.lstrip("0")

        display.draw_text(
            x_pos=padding_left + x_offset,
            y_pos=y_time,
            text=time_str,
            font_size=64,  # Large but fits in 266px column
            color="#000000",  # Pure black for maximum contrast
        )
