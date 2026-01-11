import requests
from typing import Optional

class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ""

    def get_current_weather(self, city: str) -> Optional[dict]:
        """Fetch current weather for a city

        """
        try:
            response = requests.get(
                self.base_url,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric"
                }
            )
            response.raise_for_status()
            data = response.json()

            return {
                "temperature": data["main"]["temp"],
                "condition": data["weather"][0]["description"],
                "city": data["name"]
            }
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None