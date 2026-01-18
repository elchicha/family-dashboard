from src.layout.layout_interface import LayoutInterface
from src.widgets.widget_interface import WidgetInterface


class ThreeColumnLayout(LayoutInterface):
    def __init__(self, width=1872, height=1404):
        self.width = width
        self.height = height
        self.columns = [[], [], []]
        self.column_width = width // 3

    def add_widget(self, widget: WidgetInterface, column: int) -> None:
        """Add widget to a specific column.
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
        for column_index in range(len(self.columns)):
            x_offset = column_index * self.column_width
            y_offset = 0

            for widget in self.columns[column_index]:
                widget.render(display, x_offset, y_offset)
                y_offset += widget.height
