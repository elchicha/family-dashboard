import pytest
from src.widgets.weather_widget import WeatherWidget


class TestWeatherWidget:

    @pytest.fixture
    def mock_display(self, mocker):
        return mocker.Mock()

    @pytest.fixture
    def mock_weather_service(self, mocker):
        return mocker.Mock()

    def test_weather_widget_displays_temperature_and_condition(
        self, mock_display, mock_weather_service
    ):
        """Widget should render temperature and weather condition"""
        mock_weather_service.get_current_weather.return_value = {
            "temperature": 22.5,
            "condition": "sunny",
            "city": "London",
        }

        widget = WeatherWidget(
            display=mock_display, weather_service=mock_weather_service, city="London"
        )

        widget.render()
        mock_weather_service.get_current_weather.assert_called_once_with(city="London")

        assert mock_display.draw_text.called

        calls_str = str(mock_display.draw_text.call_args_list)
        assert "22.5" in calls_str or "22" in calls_str
        assert "sunny" in calls_str

    def test_weather_widget_uses_position_offsets(
        self, mock_display, mock_weather_service
    ):
        """Widget should offset positions when x_offset/y_offset provided"""
        mock_weather_service.get_current_weather.return_value = {
            "temperature": 22,
            "condition": "sunny",
            "city": "London",
        }

        widget = WeatherWidget(mock_display, mock_weather_service, city="London")

        # Render with offset
        widget.render(x_offset=400, y_offset=0)

        calls = mock_display.draw_text.call_args_list
        # Extract positions from keyword arguments
        positions = [(call.kwargs["x_pos"], call.kwargs["y_pos"]) for call in calls]

        # All positions should be offset
        x_positions = [pos[0] for pos in positions]
        assert all(
            x >= 400 for x in x_positions
        ), f"X positions not offset: {x_positions}"
