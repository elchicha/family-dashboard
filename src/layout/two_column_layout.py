from src.layout.layout_interface import LayoutInterface
from src.widgets.widget_interface import WidgetInterface


class TwoColumnLayout(LayoutInterface):

    def __init__(self, width=800, height=480, left_ratio=0.6, widget_spacing=0):
        """
        Initialize two-column layout.

        Args:
            width: Display width in pixels (default: 800 for 7.5" display)
            height: Display height in pixels (default: 480 for 7.5" display)
            left_ratio: Ratio of width for left column (default: 0.6 = 60%)
            widget_spacing: Vertical spacing between widgets in pixels
        """
        self.width = width
        self.height = height
        if left_ratio <= 0 or left_ratio >= 1:
            raise ValueError("left_ratio must be between 0 and 1")
        self.left_width = int(self.width * left_ratio)
        self.right_width = self.width - self.left_width
        self.left_column = []
        self.right_column = []
        self.widget_spacing = widget_spacing

    def add_widget(self, widget: WidgetInterface, column: str) -> None:
        """Add widgets to a specific column.

        Args:
            widget: Widget to add
            column: Column identifier ('left' or 'right')

        Raises:
            ValueError: If column is not 'left' or 'right'
        """
        if column == "left":
            self.left_column.append(widget)
        elif column == "right":
            self.right_column.append(widget)
        else:
            raise ValueError(f"Column must be 'left' or 'right'")

    def render(self, display):
        """
        Render all widgets in their assigned columns.

        Widgets are positioned at column x-offsets and stacked vertically
        based on their height attribute. Widget widths are automatically
        set to match their column width.

        Args:
            display: Display to render to
        """

        # Render left column
        x_offset = 0
        y_offset = 0

        for widget in self.left_column:
            # Set widget width to match column width
            if hasattr(widget, "set_width"):
                widget.set_width(self.left_width)

            widget.render(display, x_offset, y_offset)
            y_offset += self.widget_spacing + widget.height

        # Render right column
        x_offset = self.left_width
        y_offset = 0

        for widget in self.right_column:
            # Set widget width to match column width
            if hasattr(widget, "set_width"):
                widget.set_width(self.right_width)

            widget.render(display, x_offset, y_offset)
            y_offset += self.widget_spacing + widget.height
