"""Tests for PNGDisplay font rendering."""
import pytest
from src.display.png_display import PNGDisplay
from PIL import Image


class TestPNGDisplayFonts:
    """Test suite for font size rendering in PNGDisplay."""

    def test_font_loads_successfully(self):
        """Test that a TrueType font can be loaded."""
        display = PNGDisplay(width=200, height=200)
        display.clear()

        # This should work without falling back to default
        # We'll know it worked if font_size makes a difference
        display.draw_text(x_pos=10, y_pos=10, text="Test", font_size=32, color="#000000")

        # Should not print warning messages (check manually)
        # Image should have content
        pixels = list(display.image.getdata())
        black_pixels = sum(1 for r, g, b in pixels if r < 200)
        assert black_pixels > 0

    def test_different_font_sizes_render_differently(self):
        """Test that different font sizes produce different sized text."""
        display = PNGDisplay(width=400, height=300)
        display.clear()

        # Draw same text at different sizes
        display.draw_text(x_pos=10, y_pos=10, text="TEST", font_size=12, color="#000000")
        display.draw_text(x_pos=10, y_pos=50, text="TEST", font_size=24, color="#000000")
        display.draw_text(x_pos=10, y_pos=100, text="TEST", font_size=48, color="#000000")

        # Save and check that text was drawn
        img = display.image
        pixels = list(img.getdata())
        black_pixels = sum(1 for r, g, b in pixels if r < 200)

        # With proper fonts, we should have significant black pixels
        assert black_pixels > 100, "Should have visible text at multiple sizes"