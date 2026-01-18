from src.layout.layout_interface import LayoutInterface


class ThreeColumnLayout(LayoutInterface):
    def __init__(self, width=1872, height=1404):
        self.width = width
        self.height = height
        self.columns = [[], [], []]
        self.column_width = width // 3

    def add_widget(self, widget, column):
        self.columns[column].append(widget)
