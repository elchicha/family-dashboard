from datetime import timedelta, date
from io import BytesIO

from flask import Flask, send_file

from src.display.png_display import PNGDisplay
from src.layout.two_column_layout import TwoColumnLayout
from src.widgets.clock_widget import ClockWidget
from src.widgets.calendar_widget import CalendarWidget
from src.services.calendar_service import CalendarService
from src.services.cached_calendar_service import CachedCalendarService

app = Flask(__name__)

# Initialize calendar service with caching (5-minute cache)
base_service = CalendarService(
    url="https://calendar.google.com/calendar/ical/jk4klsjkfeqummcgak6colmkso%40group.calendar.google.com/public/basic.ics"
)
calendar_service = CachedCalendarService(
    service=base_service,
    cache_duration_minutes=5  # Cache for 5 minutes
)


@app.route("/render/<display_id>")
def render_display(display_id: str):
    display = PNGDisplay(width=800, height=480)
    display.clear()

    layout = TwoColumnLayout(width=800, height=480, left_ratio=0.6, widget_spacing=15)

    if display_id == "kitchen":
        clock = ClockWidget()
        layout.add_widget(clock, column="right")

        # Use cached calendar service with three-day view
        layout.add_widget(
            CalendarWidget(calendar_service, view_mode="three_day"),
            column='left'
        )

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
            .admin-links {
                margin-top: 30px;
                padding: 15px;
                background: #f0f0f0;
                border-radius: 5px;
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

        <div class="admin-links">
            <h3>🛠️ Admin Tools</h3>
            <ul>
                <li><a href="/debug/calendar">View Raw Calendar Events</a></li>
                <li><a href="/admin/clear-cache">Clear Calendar Cache</a></li>
            </ul>
        </div>

        <p><em>Refresh page to see updated content (calendar cached for 5 minutes)</em></p>
    </body>
    </html>
    """


@app.route("/debug/calendar")
def debug_calendar():
    """Debug endpoint to view raw calendar events"""
    today = date.today()
    events = calendar_service.get_events(
        start_date=today,
        end_date=today + timedelta(days=30),
    )

    html = "<h1>📅 Calendar Debug</h1>"
    html += f"<p>Fetching events from {today} to {today + timedelta(days=2)}</p>"
    html += f"<p><strong>Found {len(events)} events:</strong></p>"
    html += "<ul style='font-family: monospace;'>"

    for event in events:
        html += f"<li>{event['date'].strftime('%Y-%m-%d')} {event['time']} - <strong>{event['summary']}</strong>"
        if event.get('location'):
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
    <p>Calendar cache has been cleared. Next request will fetch fresh data.</p>
    <p><a href='/debug/calendar'>View calendar</a> | <a href='/'>← Back to home</a></p>
    """


if __name__ == "__main__":
    print("🚀 Starting Family Dashboard Server...")
    print("📍 Server running at http://localhost:5000")
    print("📅 Using Arroyo School Calendar (cached for 5 minutes)")
    print("🔍 Debug calendar at http://localhost:5000/debug/calendar")
    print("🗑️  Clear cache at http://localhost:5000/admin/clear-cache")
    print("🔄 Press Ctrl+C to stop")
    app.run(debug=True, host="0.0.0.0", port=5000)
else:
    print("✅ Flask app loaded successfully")