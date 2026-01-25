from datetime import timedelta, date
from io import BytesIO
import yaml

from flask import Flask, send_file

from src.display.png_display import PNGDisplay
from src.layout.two_column_layout import TwoColumnLayout
from src.widgets.calendar_widget import CalendarWidget
from src.services.calendar_service import CalendarService
from src.services.cached_calendar_service import CachedCalendarService
from src.widgets.date_widget import DateWidget

app = Flask(__name__)


def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("ERROR: config.yaml not found!")
        print("Please copy config.example.yaml to config.yaml and fill in your details")
        exit(1)


class MergedCalendarService:
    """Service that merges events from multiple calendar services."""

    def __init__(self, services: list):
        self.services = services

    def get_events(self, start_date=None, end_date=None):
        """Get events from all services and merge them."""
        all_events = []
        for service in self.services:
            try:
                events = service.get_events(start_date=start_date, end_date=end_date)
                all_events.extend(events)
            except Exception as e:
                print(f"Warning: Failed to fetch from a calendar service: {e}")

        # Sort by date and time
        return sorted(all_events, key=lambda e: (e["date"], e["time"]))

    def clear_cache(self):
        """Clear cache for all services."""
        for service in self.services:
            if hasattr(service, "clear_cache"):
                service.clear_cache()


# Load configuration
config = load_config()

# Initialize calendar services from config
calendar_services = []
for cal_config in config["calendars"]["sources"]:
    if cal_config.get("enabled", True):
        base_service = CalendarService(
            url=cal_config["url"],
            source_name=cal_config.get(
                "short_name", cal_config.get("name", "Unknown")
            ),  # Pass the name
        )
        cached_service = CachedCalendarService(
            service=base_service,
            cache_duration_minutes=config["calendars"]["cache_duration_minutes"],
        )
        calendar_services.append(cached_service)
        print(f"✓ Loaded calendar: {cal_config['name']}")

# Create merged calendar service
calendar_service = MergedCalendarService(calendar_services)


@app.route("/render/<display_id>")
def render_display(display_id: str):
    display = PNGDisplay(
        width=config["display"]["width"], height=config["display"]["height"]
    )
    display.clear()

    layout = TwoColumnLayout(
        width=config["display"]["width"],
        height=config["display"]["height"],
        left_ratio=0.7,
        widget_spacing=10,
        debug=True,
    )

    if display_id == "kitchen":
        date_widget = DateWidget()
        layout.add_widget(date_widget, column="right")

        calendar_widget = CalendarWidget(
            calendar_service, view_mode=config["calendars"]["view_mode"]
        )
        layout.add_widget(calendar_widget, column="left")

    layout.render(display)
    png_bytes = display.get_image_bytes()

    return send_file(
        BytesIO(png_bytes),
        mimetype="image/png",
        as_attachment=False,
        download_name=f"{display_id}.png",
    )


@app.route("/")
def index():
    """Simple index page with available displays"""
    calendar_names = [
        cal["name"]
        for cal in config["calendars"]["sources"]
        if cal.get("enabled", True)
    ]
    calendars_list = "<br>".join([f"   - {name}" for name in calendar_names])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Family Dashboard Server</title>
        <style>
            body {{ font-family: sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .display {{ 
                margin: 20px 0; 
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            img {{ 
                max-width: 100%; 
                border: 2px solid #333;
                margin-top: 10px;
                width: 800px;
                height: 480px;
            }}
            .admin-links {{
                margin-top: 30px;
                padding: 15px;
                background: #f0f0f0;
                border-radius: 5px;
            }}
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

        <div class="admin-links">
            <h3>🛠️ Admin Tools</h3>
            <ul>
                <li><a href="/debug/calendar">View Raw Calendar Events</a></li>
                <li><a href="/admin/clear-cache">Clear Calendar Cache</a></li>
            </ul>
        </div>

        <p><em>Refresh page to see updated content (calendar cached for {config['calendars']['cache_duration_minutes']} minutes)</em></p>
        <p><em>Active calendars ({len(calendar_names)}):</em><br>{calendars_list}</p>
    </body>
    </html>
    """


@app.route("/debug/calendar")
def debug_calendar():
    """Debug endpoint to view raw calendar events"""
    today = date.today()
    end_date = today + timedelta(days=2)

    events = calendar_service.get_events(
        start_date=today,
        end_date=end_date,
    )

    html = "<h1>📅 Calendar Debug (All Sources)</h1>"
    html += f"<p>Fetching events from {today} to {end_date}</p>"
    html += f"<p><strong>Found {len(events)} events from all calendars:</strong></p>"
    html += "<ul style='font-family: monospace;'>"

    for event in events:
        html += f"<li>{event['date'].strftime('%Y-%m-%d')} {event['time']} - <strong>{event['summary']}</strong>"
        if event.get("location"):
            html += f" @ {event['location']}"
        html += "</li>"

    html += "</ul>"
    html += "<p><a href='/admin/clear-cache'>Clear cache and refresh</a> | <a href='/'>← Back</a></p>"

    return html


@app.route("/admin/clear-cache")
def clear_cache():
    """Admin endpoint to manually clear the calendar cache"""
    calendar_service.clear_cache()
    return """
    <h1>🗑️ Cache Cleared</h1>
    <p>All calendar caches have been cleared. Next request will fetch fresh data.</p>
    <p><a href='/debug/calendar'>View calendar</a> | <a href='/'>← Back to home</a></p>
    """


if __name__ == "__main__":
    print("🚀 Starting Family Dashboard Server...")
    print("📍 Server running at http://localhost:5000")
    print(f"📅 Loaded {len(calendar_services)} calendar(s):")
    for cal_config in config["calendars"]["sources"]:
        if cal_config.get("enabled", True):
            print(f"   - {cal_config['name']}")
    print(f"   (Cached for {config['calendars']['cache_duration_minutes']} minutes)")
    print("🔍 Debug calendar at http://localhost:5000/debug/calendar")
    print("🗑️  Clear cache at http://localhost:5000/admin/clear-cache")
    print("🔄 Press Ctrl+C to stop")
    app.run(debug=True, host="0.0.0.0", port=5000)
else:
    print("✅ Flask app loaded successfully")
