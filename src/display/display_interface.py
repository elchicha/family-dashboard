from abc import ABC, abstractmethod


class DisplayInterface(ABC):
    """Abstract interface for E-ink display implementation"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    @abstractmethod
    def clear(self) -> None:
        """Clear the display to blank state"""
        pass

    @abstractmethod
    def draw_text(self, x_pos: int, y_pos: int, text: str, font_size: int) -> None:
        """Draw text at a specified position"""
        pass

    @abstractmethod
    def refresh(self) -> None:
        """Commit changes and update the physical display"""
        pass
