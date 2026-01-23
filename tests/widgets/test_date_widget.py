"""Tests for DateWidget."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.widgets.date_widget import DateWidget


class TestDateWidget:
    """Test suite for DateWidget."""

    def test_initialization(self):
        """Test widget initializes with correct properties."""
        widget = DateWidget()

        assert widget.height == 150
        assert isinstance(widget, DateWidget)

    @patch('src.widgets.date_widget.datetime')
    def test_render_displays_day_of_week(self, mock_datetime):
        """Test that day of week is rendered prominently."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)  # Thursday
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Assert
        calls = mock_display.draw_text.call_args_list

        # First call should be day of week
        first_call = calls[0]
        assert first_call.kwargs['text'] == "FRIDAY"
        assert first_call.kwargs['font_size'] == 32
        assert first_call.kwargs['color'] == "#000000"
        assert first_call.kwargs['x_pos'] == 20  # 0 + 20 padding
        assert first_call.kwargs['y_pos'] == 20  # 0 + 20 padding

    @patch('src.widgets.date_widget.datetime')
    def test_render_displays_full_date(self, mock_datetime):
        """Test that full date is rendered clearly."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Assert
        calls = mock_display.draw_text.call_args_list

        # Second call should be full date
        second_call = calls[1]
        assert second_call.kwargs['text'] == "JANUARY 23"
        assert second_call.kwargs['font_size'] == 24
        assert second_call.kwargs['color'] == "#333333"
        assert second_call.kwargs['x_pos'] == 20  # 0 + 20 padding
        assert second_call.kwargs['y_pos'] == 60  # 20 + 40 spacing

    @patch('src.widgets.date_widget.datetime')
    def test_render_displays_year(self, mock_datetime):
        """Test that year is rendered subtly."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Assert
        calls = mock_display.draw_text.call_args_list

        # Third call should be year
        third_call = calls[2]
        assert third_call.kwargs['text'] == "2026"
        assert third_call.kwargs['font_size'] == 16
        assert third_call.kwargs['color'] == "#888888"
        assert third_call.kwargs['x_pos'] == 20  # 0 + 20 padding
        assert third_call.kwargs['y_pos'] == 92  # 60 + 32 spacing

    @patch('src.widgets.date_widget.datetime')
    def test_render_respects_offsets(self, mock_datetime):
        """Test that widget respects x and y offsets."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=100, y_offset=50)

        # Assert
        calls = mock_display.draw_text.call_args_list

        # Check first call includes offsets
        first_call = calls[0]
        assert first_call.kwargs['x_pos'] == 120  # 100 + 20 padding
        assert first_call.kwargs['y_pos'] == 70   # 50 + 20 padding

    @patch('src.widgets.date_widget.datetime')
    def test_render_uses_vertical_spacing(self, mock_datetime):
        """Test that elements are properly spaced vertically."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Assert
        calls = mock_display.draw_text.call_args_list

        # Check vertical spacing between elements
        day_y = calls[0].kwargs['y_pos']
        date_y = calls[1].kwargs['y_pos']
        year_y = calls[2].kwargs['y_pos']

        assert date_y > day_y  # Date below day
        assert year_y > date_y  # Year below date
        assert (date_y - day_y) == 40  # Consistent spacing
        assert (year_y - date_y) == 32  # Consistent spacing

    @patch('src.widgets.date_widget.datetime')
    def test_render_makes_exactly_three_draw_calls(self, mock_datetime):
        """Test that render makes exactly three text draw calls."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Assert
        assert mock_display.draw_text.call_count == 3

    @patch('src.widgets.date_widget.datetime')
    def test_text_is_uppercase(self, mock_datetime):
        """Test that day and date are rendered in uppercase."""
        # Arrange
        mock_datetime.now.return_value = datetime(2026, 1, 23, 14, 30)
        widget = DateWidget()
        mock_display = Mock()

        # Act
        widget.render(mock_display, x_offset=0, y_offset=0)

        # Assert
        calls = mock_display.draw_text.call_args_list

        # Day should be uppercase
        assert calls[0].kwargs['text'] == "FRIDAY"
        assert calls[0].kwargs['text'].isupper()

        # Date should be uppercase
        assert calls[1].kwargs['text'] == "JANUARY 23"
        assert calls[1].kwargs['text'].isupper()