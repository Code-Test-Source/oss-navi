"""Datetime utilities for consistent time handling."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info.

    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string.

    Args:
        dt: Datetime to convert

    Returns:
        ISO 8601 formatted string
    """
    return dt.isoformat()


def from_iso(s: str) -> datetime:
    """Parse ISO 8601 string to datetime.

    Args:
        s: ISO 8601 formatted string

    Returns:
        Parsed datetime
    """
    return datetime.fromisoformat(s)
