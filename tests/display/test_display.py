import pytest
from src.display.display_interface import DisplayInterface
from src.display.mock_display import MockDisplay


@pytest.fixture
def mock_display():
    """Fixture that creates a MockDisplay instance"""
    return MockDisplay(width=1872, height=1404, grayscale_levels=16)


class TestDisplayInterface:
    """Test the display abstraction layer"""

    def test_display_implements_interface(self, mock_display):
        """MockDisplay should implement DisplayInterface"""
        assert isinstance(mock_display, DisplayInterface)

    def test_display_initializes_with_dimensions(self, mock_display):
        """Display should initialize with specified dimensions"""
        assert mock_display.width == 1872
        assert mock_display.height == 1404

    def test_display_initializes_with_grayscale_levels(self, mock_display):
        """Display should support grayscale levels"""
        assert mock_display.grayscale_levels == 16

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
        assert mock_display.last_draw_params["font_size"] == 24

    def test_display_draw_text_supports_color(self, mock_display):
        """Draw text should support hex color codes"""
        mock_display.draw_text(
            x_pos=10, y_pos=20, text="Gray Text", font_size=24, color="#888888"
        )

        assert mock_display.last_draw_params["color"] == "#888888"

    def test_display_draw_text_defaults_to_black(self, mock_display):
        """Draw text should default to black if no color specified"""
        mock_display.draw_text(x_pos=10, y_pos=20, text="Default", font_size=24)

        assert mock_display.last_draw_params["color"] == "#000000"

    def test_display_draw_rectangle(self, mock_display):
        """Display should support drawing rectangles"""
        mock_display.draw_rectangle(
            x_pos=50,
            y_pos=100,
            width=200,
            height=150,
            fill="#EEEEEE",
            outline="#000000",
        )

        assert mock_display.last_action == "draw_rectangle"
        assert mock_display.last_draw_params["x"] == 50
        assert mock_display.last_draw_params["y"] == 100
        assert mock_display.last_draw_params["width"] == 200
        assert mock_display.last_draw_params["height"] == 150
        assert mock_display.last_draw_params["fill"] == "#EEEEEE"
        assert mock_display.last_draw_params["outline"] == "#000000"

    def test_display_draw_rectangle_with_no_fill(self, mock_display):
        """Rectangle should support outline-only (no fill)"""
        mock_display.draw_rectangle(
            x_pos=50, y_pos=100, width=200, height=150, fill=None, outline="#000000"
        )

        assert mock_display.last_draw_params["fill"] is None

    def test_display_refresh_updates_screen(self, mock_display):
        """Refresh should commit changes to display"""
        mock_display.refresh()
        assert mock_display.refresh_count == 1
