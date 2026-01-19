from src.display.display_interface import DisplayInterface
from src.widgets.widget_interface import WidgetInterface


class WeatherWidget(WidgetInterface):

    def __init__(self, weather_service, city: str):
        self.weather_service = weather_service
        self.city = city
        self.height = 200

    def render(self, display: DisplayInterface, x_offset: int = 0, y_offset: int = 0):
        """Render weather at offset position"""
        weather = self.weather_service.get_current_weather(city=self.city)

        display.draw_text(
            x_pos=10 + x_offset,
            y_pos=10 + y_offset,
            text=f"{weather['temperature']}°C",
            font_size=48,
        )

        display.draw_text(
            x_pos=10 + x_offset,
            y_pos=70 + y_offset,
            text=weather["condition"],
            font_size=24,
        )
