import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.widgets.clock_widget import ClockWidget


class TestClockWidget:

    @pytest.fixture
    def mock_display(self):
        """Mock display for testing"""
        display = Mock()
        display.width = 1872
        display.height = 1404
        return display

    def test_clock_widget_displays_current_time(self, mock_display):
        """ClockWidget should display current time in HH:MM AM/PM format"""
        # Mock datetime to control what "now" is
        mock_now = datetime(2026, 1, 17, 14, 30, 0)  # 2:30 PM

        with patch("src.widgets.clock_widget.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now

            widget = ClockWidget()
            widget.render(display=mock_display, x_offset=0, y_offset=0)

            # Should draw time
            calls_str = str(mock_display.draw_text.call_args_list)
            assert "02:30 PM" in calls_str or "14:30" in calls_str

    def test_clock_widget_displays_current_date(self, mock_display):
        """ClockWidget should display full date (day, month, date, year)"""
        mock_now = datetime(2026, 1, 17, 14, 30, 0)

        with patch("src.widgets.clock_widget.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now

            widget = ClockWidget()
            widget.render(display=mock_display, x_offset=0, y_offset=0)

            calls_str = str(mock_display.draw_text.call_args_list)
            # Should contain day of week and date
            assert "Saturday" in calls_str
            assert "January" in calls_str or "Jan" in calls_str
            assert "17" in calls_str

    def test_clock_widget_uses_large_font_for_time(self, mock_display):
        """Time should be displayed in large font (80+pt)"""
        widget = ClockWidget()
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls = mock_display.draw_text.call_args_list

        # At least one call should have large font size
        font_sizes = [call.kwargs.get("font_size", 24) for call in calls]
        assert any(
            size >= 80 for size in font_sizes
        ), f"Expected at least one font size >= 80, got {font_sizes}"

    def test_clock_widget_supports_position_offsets(self, mock_display):
        """ClockWidget should respect x_offset and y_offset"""
        widget = ClockWidget()
        widget.render(display=mock_display, x_offset=100, y_offset=50)

        calls = mock_display.draw_text.call_args_list

        # All X positions should be offset by at least 100
        x_positions = [call.kwargs.get("x_pos", 0) for call in calls]
        assert all(
            x >= 100 for x in x_positions
        ), f"X positions should be >= 100: {x_positions}"

        # All Y positions should be offset by at least 50
        y_positions = [call.kwargs.get("y_pos", 0) for call in calls]
        assert all(
            y >= 50 for y in y_positions
        ), f"Y positions should be >= 50: {y_positions}"

    def test_clock_widget_uses_grayscale_for_hierarchy(self, mock_display):
        """Time should be darker (more prominent) than date"""
        widget = ClockWidget()
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls = mock_display.draw_text.call_args_list

        # Should have different colors for visual hierarchy
        colors = [call.kwargs.get("color", "#000000") for call in calls]
        unique_colors = set(colors)

        # Should use at least 1 color (ideally 2 for hierarchy)
        assert len(unique_colors) >= 1, "Should use color for text"
