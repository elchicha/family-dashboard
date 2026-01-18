from src.layout.layout_interface import LayoutInterface


class ThreeColumnLayout(LayoutInterface):
    def __init__(self):
        self.columns = [[], [], []]
