from datetime import timedelta
from io import BytesIO

from PIL.ImageOps import grayscale
from flask import Flask, send_file

from src.display.png_display import PNGDisplay
from src.layout.three_column_layout import ThreeColumnLayout
from src.layout.two_column_layout import TwoColumnLayout
from src.widgets.clock_widget import ClockWidget
from src.widgets.calendar_widget import CalendarWidget

app = Flask(__name__)


class MockCalendarService:
    """Mock service that returns sample events."""

    def get_events(self):
        from datetime import datetime, timedelta

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        return [
            # TODAY
            {
                "summary": "Team Standup",
                "time": "09:00",
                "location": "Zoom - Room 3",
                "date": today,  # ← Added
                "uid": "1",
            },
            {
                "summary": "Dentist Appointment",
                "time": "14:30",
                "location": "123 Main St",
                "date": today,  # ← Added
                "uid": "2",
            },
            {
                "summary": "Dinner with Sarah",
                "time": "18:00",
                "location": "Downtown Restaurant",
                "date": today,  # ← Added
                "uid": "3",
            },
            # TOMORROW
            {
                "summary": "Client Meeting",
                "time": "10:00",
                "location": "Conference Room A",
                "date": today + timedelta(days=1),
                "uid": "4",
            },
            {
                "summary": "Grocery Shopping",
                "time": "16:00",
                "location": "Whole Foods",
                "date": today + timedelta(days=1),
                "uid": "5",
            },
            # DAY AFTER TOMORROW
            {
                "summary": "Morning Gym",
                "time": "07:00",
                "location": "LA Fitness",
                "date": today + timedelta(days=2),
                "uid": "6",
            },
            {
                "summary": "Team Lunch",
                "time": "12:30",
                "location": "Italian Place",
                "date": today + timedelta(days=2),
                "uid": "7",
            },
        ]

@app.route("/render/<display_id>")
def render_display(display_id: str):
    display = PNGDisplay(width=800, height=480)
    display.clear()

    layout = TwoColumnLayout(width=800, height=480, left_ratio=0.6, widget_spacing=15)

    if display_id == "kitchen":
        clock = ClockWidget()
        layout.add_widget(clock, column="right")
        calendar_service = MockCalendarService()
        layout.add_widget(
            CalendarWidget(calendar_service, view_mode="three_day"),  # ← Change to three_day
            column='left'
        )

        # TODO: Add more widgets

    layout.render(display)
    png_bytes = display.get_image_bytes()

    # Return as PNG response
    return send_file(
        BytesIO(png_bytes),
        mimetype="image/png",
        as_attachment=False,
        download_name=f"{display_id}.png",
    )


@app.route("/")
def index():
    """Simple index page with available displays"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Family Dashboard Server</title>
        <style>
            body { font-family: sans-serif; margin: 40px; }
            h1 { color: #333; }
            .display { 
                margin: 20px 0; 
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            img { 
                max-width: 100%; 
                border: 2px solid #333;
                margin-top: 10px;
                width: 1600px; 
                image-rendering: pixelated; 
            }
        </style>
    </head>
    <body>
        <h1>🏠 Family Dashboard Rendering Server</h1>
        <p>Available displays:</p>

        <div class="display">
            <h2>Kitchen Display</h2>
            <p><a href="/render/kitchen">View PNG</a></p>
            <img src="/render/kitchen" alt="Kitchen Dashboard">
        </div>

        <p><em>Refresh page to see updated content</em></p>
    </body>
    </html>
    """


if __name__ == "__main__":
    print("🚀 Starting Family Dashboard Server...")
    print("📍 Server running at http://localhost:5000")
    print("🔄 Press Ctrl+C to stop")
    app.run(debug=True, host="0.0.0.0", port=5000)
else:
    # Also print when imported (for debugging)
    print("✅ Flask app loaded successfully")
