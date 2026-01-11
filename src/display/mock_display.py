from src.display.display_interface import DisplayInterface


class MockDisplay(DisplayInterface):
    """In-memory display implementation for testing"""

    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self.last_action = None
        self.last_draw_params = {}
        self.refresh_count = 0
        self.draw_commands = []  # Track all draw commands

    def clear(self) -> None:
        """Clear the display"""
        self.last_action = "clear"
        self.draw_commands = []

    def draw_text(self, x: int, y: int, text: str, font_size: int) -> None:
        """Record text drawing command"""
        self.last_action = "draw_text"
        self.last_draw_params = {
            "x": x,
            "y": y,
            "text": text,
            "font_size": font_size
        }
        self.draw_commands.append(self.last_draw_params.copy())

    def refresh(self) -> None:
        """Increment refresh counter"""
        self.last_action = "refresh"
        self.refresh_count += 1