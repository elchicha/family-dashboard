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
            display=mock_display, weather_service=mock_weather_service
        )

        widget.render(city="London")
        mock_weather_service.get_current_weather.assert_called_once_with(city="London")

        assert mock_display.draw_text.called
        calls_str = str(mock_display.draw_text.call_args_list)
        assert "22.5" in calls_str or "22" in calls_str
        assert "sunny" in calls_str
