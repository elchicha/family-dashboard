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