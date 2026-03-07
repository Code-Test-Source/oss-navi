"""Cache management with JSON storage and expiration handling."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from oss_navi.utils.paths import CACHE_METADATA_FILE

CACHE_EXPIRATION_HOURS = 24


def read_json(file_path: Path) -> dict | None:
    """Read JSON from a file, returning None if file doesn't exist or is invalid."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_json(file_path: Path, data: dict) -> None:
    """Write JSON to a file, creating parent directories if needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid (within 24-hour expiration)."""
    metadata = read_json(CACHE_METADATA_FILE)
    if not metadata or "caches" not in metadata:
        return False

    cache_info = metadata["caches"].get(cache_key)
    if not cache_info:
        return False

    expires_at_str = cache_info.get("expires_at")
    if not expires_at_str:
        return False

    try:
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        return datetime.now(UTC) < expires_at
    except (ValueError, TypeError):
        return False


def update_cache_metadata(cache_key: str, count: int | None = None) -> None:
    """Update cache metadata with current timestamp and expiration."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=CACHE_EXPIRATION_HOURS)

    metadata = read_json(CACHE_METADATA_FILE) or {"version": 1, "caches": {}}

    cache_info = {
        "fetched_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "is_valid": True,
    }
    if count is not None:
        cache_info["count"] = count

    metadata["caches"][cache_key] = cache_info
    write_json(CACHE_METADATA_FILE, metadata)


def get_cache_age_hours(cache_key: str) -> float | None:
    """Get the age of cached data in hours, or None if not cached."""
    metadata = read_json(CACHE_METADATA_FILE)
    if not metadata or "caches" not in metadata:
        return None

    cache_info = metadata["caches"].get(cache_key)
    if not cache_info:
        return None

    fetched_at_str = cache_info.get("fetched_at")
    if not fetched_at_str:
        return None

    try:
        fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        age = datetime.now(UTC) - fetched_at
        return age.total_seconds() / 3600
    except (ValueError, TypeError):
        return None


def clear_cache(cache_key: str | None = None) -> None:
    """Clear cache metadata for a specific key or all caches."""
    if cache_key is None:
        write_json(CACHE_METADATA_FILE, {"version": 1, "caches": {}})
    else:
        metadata = read_json(CACHE_METADATA_FILE) or {"version": 1, "caches": {}}
        metadata["caches"].pop(cache_key, None)
        write_json(CACHE_METADATA_FILE, metadata)
