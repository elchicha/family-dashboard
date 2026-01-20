
import pytest
from src.services.weather_service import WeatherService


class TestWeatherService:
    """Test weather data fetching"""

    @pytest.fixture
    def weather_service(self):
        """Fixture providing WeatherService instance"""
        return WeatherService(api_key="fake_test_key")

    def test_weather_service_can_be_instantiated(self):
        """WeatherService should be creatable with an API key"""
        service = WeatherService(api_key="test_key")
        assert service.api_key == "test_key"

    def test_weather_service_has_get_current_weather_method(self):
        """WeatherService should have a get_current_weather method"""
        service = WeatherService(api_key="test_key")

        # Method should exist and be callable
        assert hasattr(service, 'get_current_weather')
        assert callable(service.get_current_weather)

    def test_get_current_weather_accepts_city_parameter(self):
        """get_current_weather should accept a city name"""
        service = WeatherService(api_key="test_key")

        # Should not crash when called with a city
        # For now, it can return None - we just want it to accept the parameter
        result = service.get_current_weather(city="London")

        # We don't care what it returns yet, just that it doesn't crash
        assert result is not None or result is None  # This always passes, just testing the call works

    def test_get_current_weather_returns_temperature(self, weather_service, mocker):
        """Should fetch and parse weather data"""
        mock_json_data = {
            "main": {"temp": 15.5},
            "weather": [{"description": "cloudy"}],
            "name": "London"
        }
        mock_get = mocker.patch('src.services.weather_service.requests.get')
        mock_get.return_value.json.return_value = mock_json_data
        mock_get.return_value.status_code = 200

        weather = weather_service.get_current_weather(city="London")

        assert weather["temperature"] == 15.5
        assert weather["condition"] == "cloudy"
        assert weather["city"] == "London"

    def test_get_current_weather_handles_api_error(self, weather_service, mocker):
        """Should handle API failures gracefully"""
        # Patch where requests is USED
        mock_get = mocker.patch('src.services.weather_service.requests.get')
        mock_get.return_value.raise_for_status.side_effect = Exception("API Error")

        weather = weather_service.get_current_weather(city="InvalidCity")

        assert weather is None