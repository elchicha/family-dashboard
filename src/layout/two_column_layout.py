from src.layout.layout_interface import LayoutInterface
from src.widgets.widget_interface import WidgetInterface
from PIL import ImageDraw


class TwoColumnLayout(LayoutInterface):

    def __init__(
        self, width=800, height=480, left_ratio=0.6, widget_spacing=0, debug=False
    ):
        """
        Initialize two-column layout.

        Args:
            width: Display width in pixels (default: 800 for 7.5" display)
            height: Display height in pixels (default: 480 for 7.5" display)
            left_ratio: Ratio of width for left column (default: 0.6 = 60%)
            widget_spacing: Vertical spacing between widgets in pixels
            debug: Enable visual debugging overlay (default: False)
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
        self.debug = debug

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

            if self.debug:
                print(
                    f"[LEFT] Rendering {widget.__class__.__name__} at x={x_offset}, y={y_offset}, width={self.left_width}, height={widget.height}"
                )

            widget.render(display, x_offset, y_offset)
            y_offset += self.widget_spacing + widget.height

        # Render right column
        x_offset = self.left_width
        y_offset = 0

        for widget in self.right_column:
            # Set widget width to match column width
            if hasattr(widget, "set_width"):
                widget.set_width(self.right_width)

            if self.debug:
                print(
                    f"[RIGHT] Rendering {widget.__class__.__name__} at x={x_offset}, y={y_offset}, width={self.right_width}, height={widget.height}"
                )

            widget.render(display, x_offset, y_offset)
            y_offset += self.widget_spacing + widget.height

        # Draw debug overlay if enabled
        if self.debug:
            self._draw_debug_overlay(display)

    def _draw_debug_overlay(self, display):
        """Draw visual debugging information on the display."""
        # Get the PIL Image from the display
        if hasattr(display, "image"):
            img = display.image
        elif hasattr(display, "get_image"):
            img = display.get_image()
        else:
            print("[DEBUG] Warning: Cannot access display image for debug overlay")
            return

        draw = ImageDraw.Draw(img)

        # Draw column divider (red dashed line)
        divider_x = self.left_width
        for y in range(0, self.height, 10):
            draw.line(
                [(divider_x, y), (divider_x, min(y + 5, self.height))],
                fill="red",
                width=2,
            )

        # Draw column boundaries (blue rectangles)
        # Left column boundary
        draw.rectangle(
            [(0, 0), (self.left_width - 1, self.height - 1)], outline="blue", width=2
        )
        # Right column boundary
        draw.rectangle(
            [(self.left_width, 0), (self.width - 1, self.height - 1)],
            outline="blue",
            width=2,
        )

        # Draw widget bounding boxes and info
        # Left column widgets
        y_offset = 0
        for i, widget in enumerate(self.left_column):
            widget_height = widget.height if hasattr(widget, "height") else 0
            # Green box around widget
            draw.rectangle(
                [(0, y_offset), (self.left_width - 1, y_offset + widget_height - 1)],
                outline="green",
                width=1,
            )

            # Label widget
            label = (
                f"L{i}: {widget.__class__.__name__} ({self.left_width}x{widget_height})"
            )
            draw.text((5, y_offset + 2), label, fill="green")

            y_offset += self.widget_spacing + widget_height

        # Right column widgets
        y_offset = 0
        for i, widget in enumerate(self.right_column):
            widget_height = widget.height if hasattr(widget, "height") else 0
            # Orange box around widget
            draw.rectangle(
                [
                    (self.left_width, y_offset),
                    (self.width - 1, y_offset + widget_height - 1),
                ],
                outline="orange",
                width=1,
            )

            # Label widget
            label = f"R{i}: {widget.__class__.__name__} ({self.right_width}x{widget_height})"
            draw.text((self.left_width + 5, y_offset + 2), label, fill="orange")

            y_offset += self.widget_spacing + widget_height

        # Draw center line of right column (to check centering)
        center_x = self.left_width + (self.right_width // 2)
        for y in range(0, self.height, 10):
            draw.line(
                [(center_x, y), (center_x, min(y + 5, self.height))],
                fill="purple",
                width=1,
            )

        # Add legend
        legend_y = self.height - 60
        draw.rectangle(
            [(5, legend_y), (250, self.height - 5)], fill="white", outline="black"
        )
        draw.text((10, legend_y + 5), "Debug Legend:", fill="black")
        draw.text((10, legend_y + 20), "Blue: Column bounds", fill="blue")
        draw.text((10, legend_y + 35), "Red: Column divider", fill="red")
        draw.text((130, legend_y + 20), "Green: Left widgets", fill="green")
        draw.text((130, legend_y + 35), "Orange: Right widgets", fill="orange")
