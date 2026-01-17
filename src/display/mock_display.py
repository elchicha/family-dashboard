from src.display.display_interface import DisplayInterface


class MockDisplay(DisplayInterface):
    """In-memory display implementation for testing"""

    def __init__(self, width: int, height: int, grayscale_levels: int = 0):
        super().__init__(width, height, grayscale_levels)
        self.last_action = None
        self.last_draw_params = {}
        self.refresh_count = 0
        self.draw_commands = []  # Track all draw commands

    def clear(self) -> None:
        """Clear the display"""
        self.last_action = "clear"
        self.draw_commands = []

    def draw_text(
        self, x_pos: int, y_pos: int, text: str, font_size: int, color: str = "#000000"
    ) -> None:
        """Record text drawing command"""
        self.last_action = "draw_text"
        self.last_draw_params = {
            "x": x_pos,
            "y": y_pos,
            "text": text,
            "font_size": font_size,
            "color": color,
        }
        self.draw_commands.append(self.last_draw_params.copy())

    def refresh(self) -> None:
        """Increment refresh counter"""
        self.last_action = "refresh"
        self.refresh_count += 1

    def draw_rectangle(
        self,
        x_pos: int,
        y_pos: int,
        width: int,
        height: int,
        fill: str,
        outline: str = "#000000",
    ) -> None:
        self.last_action = "draw_rectangle"
        self.last_draw_params = {
            "x": x_pos,
            "y": y_pos,
            "width": width,
            "height": height,
            "fill": fill,
            "outline": outline,
        }
        self.draw_commands.append(self.last_draw_params.copy())
