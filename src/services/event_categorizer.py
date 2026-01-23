"""Smart event categorization for glanceable display."""
from enum import Enum
from typing import Dict


class EventCategory(Enum):
    """Event categories for smart display grouping."""
    SCHEDULE = "schedule"  # Bell schedules, day types (B1, G2)
    FAMILY_EVENT = "family"  # School events, performances, parent nights
    ONGOING = "ongoing"  # Multi-day events like read-a-thons
    NO_SCHOOL = "no_school"  # Holidays, breaks
    DEADLINE = "deadline"  # Registration deadlines, payment due
    PERSONAL = "personal"  # Individual appointments


class EventCategorizer:
    """Categorize events for cognitive-load-reduced display."""

    # Keywords for each category
    SCHEDULE_KEYWORDS = [
        'b1', 'b2', 'g1', 'g2', 'a day', 'b day',
        'early dismissal', 'late start', 'minimum day'
    ]

    NO_SCHOOL_KEYWORDS = [
        'no school', 'holiday', 'break', 'closed',
        'winter break', 'spring break', 'vacation'
    ]

    FAMILY_EVENT_KEYWORDS = [
        'night', 'meeting', 'parent', 'showcase', 'performance',
        'interview', 'conference', 'open house', 'back to school',
        'orientation', 'info session', 'tour'
    ]

    DEADLINE_KEYWORDS = [
        'deadline', 'due', 'registration', 'sign up',
        'last day', 'closes', 'ends'
    ]

    ONGOING_KEYWORDS = [
        'fair', 'week', 'thon', 'drive', 'fundraiser'
    ]

    @classmethod
    def categorize(cls, event: Dict) -> EventCategory:
        """
        Categorize an event based on its properties.

        Args:
            event: Event dict with 'summary', 'time', etc.

        Returns:
            EventCategory enum value
        """
        summary_lower = event['summary'].lower()
        time_str = event.get('time', '')

        # No school days - highest priority
        if cls._matches_keywords(summary_lower, cls.NO_SCHOOL_KEYWORDS):
            return EventCategory.NO_SCHOOL

        # Schedule markers (B1, G2, etc.)
        if cls._matches_keywords(summary_lower, cls.SCHEDULE_KEYWORDS):
            return EventCategory.SCHEDULE

        # All-day ongoing events
        if time_str == "All Day" and cls._matches_keywords(summary_lower, cls.ONGOING_KEYWORDS):
            return EventCategory.ONGOING

        # Deadlines
        if cls._matches_keywords(summary_lower, cls.DEADLINE_KEYWORDS):
            return EventCategory.DEADLINE

        # Family events
        if cls._matches_keywords(summary_lower, cls.FAMILY_EVENT_KEYWORDS):
            return EventCategory.FAMILY_EVENT

        # Default to personal
        return EventCategory.PERSONAL

    @staticmethod
    def _matches_keywords(text: str, keywords: list) -> bool:
        """Check if text contains any of the keywords."""
        return any(keyword in text for keyword in keywords)

    @classmethod
    def get_category_priority(cls, category: EventCategory) -> int:
        """
        Get display priority for category (lower = higher priority).

        Returns:
            Priority number (0 = highest)
        """
        priority_map = {
            EventCategory.NO_SCHOOL: 0,
            EventCategory.SCHEDULE: 1,
            EventCategory.FAMILY_EVENT: 2,
            EventCategory.DEADLINE: 3,
            EventCategory.ONGOING: 4,
            EventCategory.PERSONAL: 5,
        }
        return priority_map.get(category, 999)