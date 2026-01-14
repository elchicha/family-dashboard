import pytest
from src.display.display_interface import DisplayInterface
from src.display.mock_display import MockDisplay


@pytest.fixture
def mock_display():
    """Fixture that creates a MockDisplay instance"""
    return MockDisplay(width=800, height=480)


class TestDisplayInterface:
    """Test the display abstraction layer"""

    def test_display_implements_interface(self, mock_display):
        """MockDisplay should implement DisplayInterface"""
        assert isinstance(mock_display, DisplayInterface)

    def test_display_initializes_with_dimensions(self, mock_display):
        """Display should initialize with specified dimensions"""
        assert mock_display.width == 800
        assert mock_display.height == 480

    def test_display_clear_creates_blank_canvas(self, mock_display):
        """Clear should reset display to blank state"""
        mock_display.clear()
        # MockDisplay should track that clear was called
        assert mock_display.last_action == "clear"

    def test_display_draw_text_accepts_position_and_content(self, mock_display):
        """Display should accept text drawing commands"""
        mock_display.draw_text(x_pos=10, y_pos=20, text="Hello World", font_size=24)

        assert mock_display.last_action == "draw_text"
        assert mock_display.last_draw_params["x"] == 10
        assert mock_display.last_draw_params["y"] == 20
        assert mock_display.last_draw_params["text"] == "Hello World"

    def test_display_refresh_updates_screen(self, mock_display):
        """Refresh should commit changes to display"""
        mock_display.refresh()
        assert mock_display.refresh_count == 1
