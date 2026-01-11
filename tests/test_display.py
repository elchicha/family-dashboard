import pytest
from src.display.display_interface import DisplayInterface
from src.display.mock_display import MockDisplay


class TestDisplayInterface:
    """Test the display abstraction layer"""

    def test_display_implements_interface(self):
        """MockDisplay should implement DisplayInterface"""
        display = MockDisplay(width=800, height=480)
        assert isinstance(display, DisplayInterface)

    def test_display_initializes_with_dimensions(self):
        """Display should initialize with specified dimensions"""
        display = MockDisplay(width=800, height=480)
        assert display.width == 800
        assert display.height == 480

    def test_display_clear_creates_blank_canvas(self):
        """Clear should reset display to blank state"""
        display = MockDisplay(width=800, height=480)
        display.clear()
        # MockDisplay should track that clear was called
        assert display.last_action == "clear"

    def test_display_draw_text_accepts_position_and_content(self):
        """Display should accept text drawing commands"""
        display = MockDisplay(width=800, height=480)
        display.draw_text(x=10, y=20, text="Hello World", font_size=24)

        assert display.last_action == "draw_text"
        assert display.last_draw_params["x"] == 10
        assert display.last_draw_params["y"] == 20
        assert display.last_draw_params["text"] == "Hello World"

    def test_display_refresh_updates_screen(self):
        """Refresh should commit changes to display"""
        display = MockDisplay(width=800, height=480)
        display.refresh()
        assert display.refresh_count == 1