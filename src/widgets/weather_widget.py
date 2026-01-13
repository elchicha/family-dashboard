from src.display.display_interface import DisplayInterface
from src.services.weather_service import WeatherService


class WeatherWidget:

    def __init__(self, display: DisplayInterface, weather_service: WeatherService):
        self.display = display
        self.weather_service = weather_service

    def render(self, city: str):
        weather = self.weather_service.get_current_weather(city=city)
        self.display.draw_text(0, 10, weather["temperature"])
        self.display.draw_text(0, 10, weather["condition"])
