from datetime import datetime
from src.display.png_display import PNGDisplay
from src.widgets.calendar_widget import CalendarWidget
from src.widgets.weather_widget import WeatherWidget
from src.dashboard import Dashboard


def create_mock_calendar_service():
    """Mock calendar service with fake data"""

    class MockCalendarService:
        def get_todays_events(self):
            return [
                {"name": "Morning Standup", "time": "09:00"},
                {"name": "Client Meeting", "time": "10:30"},
                {"name": "Lunch with Team", "time": "12:00"},
                {"name": "Code Review", "time": "14:00"},
                {"name": "Deploy to Prod", "time": "16:00"},
            ]

    return MockCalendarService()


def create_mock_weather_service():
    """Mock weather service with fake data"""

    class MockWeatherService:
        def get_current_weather(self, city):
            return {"temperature": 22, "condition": "Sunny", "city": city}

    return MockWeatherService()


if __name__ == "__main__":
    # 7.3" E-Ink display specs: 800x480
    display = PNGDisplay(width=800, height=480, output_path="dashboard_7.3inch.png")

    # Draw header
    now = datetime.now()
    display.draw_text(x_pos=20, y_pos=15, text="Family Dashboard", font_size=24)
    display.draw_text(
        x_pos=520, y_pos=15, text=now.strftime("%a, %b %d  %I:%M %p"), font_size=20
    )

    # Draw section divider line (optional - shows layout)
    # Note: PNGDisplay would need a draw_line method for this
    display.draw_line(0, 60, 800, 60, color="black", width=2)

    # Create services
    calendar_service = create_mock_calendar_service()
    weather_service = create_mock_weather_service()

    # Create widgets with tighter layout
    calendar_widget = CalendarWidget(display, calendar_service)
    weather_widget = WeatherWidget(display, weather_service, city="London")

    # Create dashboard
    dashboard = Dashboard(display)

    # Position widgets for 800x480
    # Calendar: left half, below header
    dashboard.add_widget(calendar_widget, x_pos=20, y_pos=70)
    display.draw_line(400, 60, 400, 480, color="lightgray", width=1)
    # Weather: right half, below header
    dashboard.add_widget(weather_widget, x_pos=420, y_pos=70)

    # Render!
    dashboard.render()

    print('✅ 7.3" E-Ink dashboard rendered!')
    print("📄 Open dashboard_7.3inch.png to preview")
    print("📏 Resolution: 800x480 (actual E-Paper size)")
