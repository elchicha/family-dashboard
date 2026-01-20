from src.layout.layout_interface import LayoutInterface
from src.widgets.widget_interface import WidgetInterface


class ThreeColumnLayout(LayoutInterface):
    """
    Three-column layout for E-Ink dashboards.

    Divides the display into three equal-width columns. Widgets are
    stacked vertically within their assigned column.

    Supported displays:
    - 800×480 (7.5" E-Ink with ESP32 - Waveshare SKU:13187)
    - 960×680 (13.3" E-Ink Pi HAT - Waveshare SKU:25726)
    - Custom resolutions supported via width/height parameters

    Note: Widgets must have a 'height' attribute for proper stacking.
    """

    def __init__(self, width=800, height=480):
        """
        Initialize three-column layout.

        Args:
            width: Display width in pixels (default: 800 for 7.5" display)
            height: Display height in pixels (default: 480 for 7.5" display)
        """
        self.width = width
        self.height = height
        self.columns = [[], [], []]
        self.column_width = width // 3

    def add_widget(self, widget: WidgetInterface, column: int) -> None:
        """Add widgets to a specific column.
        Args:
            widget: Widget to add
            column: Column index

        Raises:
            ValueError: If column is not in range
        """
        if not 0 <= column < len(self.columns):
            raise ValueError(f"Column must be 0-{len(self.columns)-1}, got {column}")
        self.columns[column].append(widget)

    def render(self, display):
        """
        Render all widgets in their assigned columns.

        Widgets are positioned at column x-offsets and stacked vertically
        based on their height attribute.

        Args:
            display: Display to render to
        """
        for column_index in range(len(self.columns)):
            x_offset = column_index * self.column_width
            y_offset = 0

            for widget in self.columns[column_index]:
                widget.render(display, x_offset, y_offset)
                y_offset += widget.height
