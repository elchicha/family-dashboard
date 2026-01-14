from abc import ABC, abstractmethod


class WidgetInterface(ABC):
    """Base interface for all dashboard widgets"""

    @abstractmethod
    def render(self, x_offset: int = 0, y_offset: int = 0) -> None:
        """
        Render the widget at the specified offset.

        Args:
            x_offset: Horizontal offset from origin
            y_offset: Vertical offset from origin
        """
        pass
