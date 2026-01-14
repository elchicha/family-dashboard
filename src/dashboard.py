from src.display.display_interface import DisplayInterface


class Dashboard:

    def __init__(self, display: DisplayInterface):
        self.display = display
        self.widgets = []

    def add_widget(self, widget, x_pos: int, y_pos: int):
        self.widgets.append((widget, x_pos, y_pos))

    def render(self):
        self.display.clear()
        for widget, x_pos, y_pos in self.widgets:
            widget.render(x_offset=x_pos, y_offset=y_pos)

        self.display.refresh()
