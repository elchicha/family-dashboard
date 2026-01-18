from src.layout.layout_interface import LayoutInterface


class ThreeColumnLayout(LayoutInterface):
    def __init__(self):
        self.columns = [[], [], []]
        self.column_width = width // 3

    def add_widget(self, widget, column):
        self.columns[column].append(widget)
