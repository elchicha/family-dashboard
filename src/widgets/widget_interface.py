from abc import ABC, abstractmethod


class WidgetInterface(ABC):
    """Base interface for all dashboard widgets"""

    @abstractmethod
    def render(self, display, x_offset: int = 0, y_offset: int = 0) -> None:
        """
        Render the widget at the specified offset.

        Args:
            display: Target display where to render
            x_offset: Horizontal offset from origin
            y_offset: Vertical offset from origin
        """
        pass
