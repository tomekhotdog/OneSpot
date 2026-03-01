"""Computation helper for availability records."""

from datetime import date

from backend.models import Availability, AvailabilityType

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def get_available_hours(avail: Availability, query_date: date) -> tuple[int, int] | None:
    """Return (start_hour, end_hour) if this availability covers the date, or None."""
    if avail.paused:
        return None

    if avail.type == AvailabilityType.ONE_OFF:
        if avail.date == query_date.isoformat():
            return (avail.start_hour, avail.end_hour)
        return None

    if avail.type == AvailabilityType.RECURRING:
        if query_date.isoformat() in avail.exclusions:
            return None
        day_name = DAY_NAMES[query_date.weekday()]
        day_hours = avail.pattern.get(day_name) if avail.pattern else None
        if day_hours is None:
            return None
        return (day_hours.start, day_hours.end)

    return None
