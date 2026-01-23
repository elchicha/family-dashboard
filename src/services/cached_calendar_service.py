"""Cached wrapper for CalendarService to reduce API calls."""
from datetime import datetime, timedelta, date
from typing import Optional
import threading


class CachedCalendarService:
    """
    Wrapper that caches calendar events for a configurable duration.
    Thread-safe for concurrent requests.
    """

    def __init__(self, service, cache_duration_minutes: int = 5):
        """
        Initialize cached calendar service.

        Args:
            service: CalendarService instance to wrap
            cache_duration_minutes: How long to cache results (default: 5 minutes)
        """
        self.service = service
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.cache = None
        self.cache_time = None
        self.cache_key = None  # Track what date range was cached
        self.lock = threading.Lock()

    def get_events(
            self,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> list[dict]:
        """
        Get events with caching.

        Args:
            start_date: Start date (defaults to today)
            end_date: End date (defaults to today)

        Returns:
            List of event dictionaries
        """
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date

        cache_key = (start_date, end_date)

        with self.lock:
            now = datetime.now()

            # Check if cache is valid
            cache_expired = (
                    self.cache is None
                    or self.cache_time is None
                    or (now - self.cache_time) > self.cache_duration
                    or self.cache_key != cache_key
            )

            if cache_expired:
                print(f"🔄 Fetching calendar events for {start_date} to {end_date}...")
                self.cache = self.service.get_events(start_date, end_date)
                self.cache_time = now
                self.cache_key = cache_key
                print(f"✅ Cached {len(self.cache)} events at {now.strftime('%H:%M:%S')}")
            else:
                age = (now - self.cache_time).total_seconds()
                print(f"💾 Using cached events (age: {age:.0f}s)")

            return self.cache

    def clear_cache(self):
        """Manually clear the cache."""
        with self.lock:
            self.cache = None
            self.cache_time = None
            self.cache_key = None
            print("🗑️  Cache cleared")