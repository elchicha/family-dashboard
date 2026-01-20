"""Tests for ClockWidget."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.widgets.clock_widget import ClockWidget


class TestClockWidget:
    """Test suite for ClockWidget"""

    @pytest.fixture
    def mock_display(self):
        """Mock display for testing"""
        display = Mock()
        display.width = 800
        display.height = 480
        return display

    def test_widget_has_height_attribute(self):
        """Widget must have height for layout stacking."""
        clock = ClockWidget()
        assert hasattr(clock, "height")
        assert clock.height > 0

    def test_height_is_reasonable_for_content(self):
        """Height should accommodate time + date + padding."""
        clock = ClockWidget()
        # Updated to match new implementation
        assert clock.height == 200

    def test_clock_widget_displays_current_time(self, mock_display):
        """ClockWidget should display current time in 12-hour format with leading zero stripped."""
        mock_now = datetime(2026, 1, 17, 14, 30, 0)  # 2:30 PM

        with patch("src.widgets.clock_widget.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now

            widget = ClockWidget()
            widget.render(display=mock_display, x_offset=0, y_offset=0)

            # Should draw time with leading zero stripped: "2:30 PM" not "02:30 PM"
            calls_str = str(mock_display.draw_text.call_args_list)
            assert "2:30 PM" in calls_str

    def test_clock_widget_displays_current_date(self, mock_display):
        """ClockWidget should display day and abbreviated date."""
        mock_now = datetime(2026, 1, 17, 14, 30, 0)  # Saturday

        with patch("src.widgets.clock_widget.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now

            widget = ClockWidget()
            widget.render(display=mock_display, x_offset=0, y_offset=0)

            calls_str = str(mock_display.draw_text.call_args_list)
            # Day is uppercase: "SATURDAY"
            assert "SATURDAY" in calls_str
            # Date is abbreviated: "JAN 17"
            assert "JAN 17" in calls_str

    def test_clock_widget_uses_large_font_for_time(self, mock_display):
        """Time should be displayed in large font (optimized for 266px column)."""
        widget = ClockWidget()
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls = mock_display.draw_text.call_args_list

        # Time font should be 64px (largest element)
        font_sizes = [call.kwargs.get("font_size", 0) for call in calls]
        assert 64 in font_sizes, f"Expected 64px font for time, got {font_sizes}"
        assert max(font_sizes) == 64, "Time should have the largest font"

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
        """Should use different colors for visual hierarchy."""
        widget = ClockWidget()
        widget.render(display=mock_display, x_offset=0, y_offset=0)

        calls = mock_display.draw_text.call_args_list

        # Should have different colors for visual hierarchy
        colors = [call.kwargs.get("color", "#000000") for call in calls]
        unique_colors = set(colors)

        # Should use 3 different colors (day, date, time)
        assert (
            len(unique_colors) == 3
        ), f"Expected 3 colors for hierarchy, got {unique_colors}"

    @patch("src.widgets.clock_widget.datetime")
    def test_renders_time_in_12_hour_format(self, mock_datetime):
        """Time should display in 12-hour format with AM/PM, leading zero stripped."""
        mock_datetime.now.return_value = datetime(2025, 1, 19, 15, 27)

        clock = ClockWidget()
        display = Mock()

        clock.render(display, x_offset=0, y_offset=0)

        # Should render "3:27 PM" (leading zero stripped from "03:27 PM")
        calls_str = str(display.draw_text.call_args_list)
        assert "3:27 PM" in calls_str

    @patch("src.widgets.clock_widget.datetime")
    def test_renders_abbreviated_date_format(self, mock_datetime):
        """Date should be abbreviated to fit narrow column."""
        mock_datetime.now.return_value = datetime(2025, 1, 19, 15, 27)  # Monday

        clock = ClockWidget()
        display = Mock()

        clock.render(display, x_offset=0, y_offset=0)

        calls_str = str(display.draw_text.call_args_list)

        # Should render "MONDAY" and "JAN 19", not full format
        assert "SUNDAY" in calls_str
        assert "JAN 19" in calls_str
        assert "January 19, 2025" not in calls_str

    @patch("src.widgets.clock_widget.datetime")
    def test_uses_grayscale_hierarchy(self, mock_datetime):
        """Should use different grayscale values for visual hierarchy."""
        mock_datetime.now.return_value = datetime(2025, 1, 19, 15, 27)

        clock = ClockWidget()
        display = Mock()

        clock.render(display, x_offset=0, y_offset=0)

        # Extract colors from all calls
        colors_used = [
            call.kwargs.get("color") for call in display.draw_text.call_args_list
        ]

        # Should have 3 different colors: day, date, time
        unique_colors = set(colors_used)
        assert len(unique_colors) == 3, f"Expected 3 colors, got {unique_colors}"

        # Verify specific hierarchy
        assert "#808080" in colors_used  # Medium gray for day
        assert "#555555" in colors_used  # Dark gray for date
        assert "#000000" in colors_used  # Black for time

    def test_respects_position_offsets(self):
        """Widget should render at correct position with offsets."""
        clock = ClockWidget()
        display = Mock()

        clock.render(display, x_offset=100, y_offset=50)

        # All draw calls should include the offsets
        for call in display.draw_text.call_args_list:
            x_pos = call.kwargs.get("x_pos")
            y_pos = call.kwargs.get("y_pos")
            assert x_pos >= 100  # Should include x_offset (15 padding + 100)
            assert y_pos >= 50  # Should include y_offset (20+ padding + 50)

    @patch("src.widgets.clock_widget.datetime")
    def test_hourly_format_shows_hour_only(self, mock_datetime):
        """Hourly format should show hour and AM/PM without minutes."""
        mock_datetime.now.return_value = datetime(2025, 1, 19, 15, 27)

        clock = ClockWidget(hourly_format=True)
        display = Mock()

        clock.render(display, x_offset=0, y_offset=0)

        calls_str = str(display.draw_text.call_args_list)
        # Should show "3 PM" not "3:27 PM"
        assert "3 PM" in calls_str
        assert "3:27 PM" not in calls_str

    @patch("src.widgets.clock_widget.datetime")
    def test_standard_format_shows_minutes(self, mock_datetime):
        """Standard format should show hour:minutes AM/PM."""
        mock_datetime.now.return_value = datetime(2025, 1, 19, 15, 27)

        clock = ClockWidget(hourly_format=False)
        display = Mock()

        clock.render(display, x_offset=0, y_offset=0)

        calls_str = str(display.draw_text.call_args_list)
        # Should show "3:27 PM" with minutes
        assert "3:27 PM" in calls_str
