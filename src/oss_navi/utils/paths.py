"""Path constants and directory management for OSS-Navi."""

import os
from pathlib import Path


def get_oss_navi_home() -> Path:
    """Get the OSS-Navi home directory from environment or default."""
    home = os.environ.get("OSS_NAVI_HOME")
    if home:
        return Path(home)
    return Path.home() / ".oss-navi"


# Primary paths
OSS_NAVI_HOME: Path = get_oss_navi_home()
CACHE_DIR: Path = OSS_NAVI_HOME / "cache"
STATE_DIR: Path = OSS_NAVI_HOME / "state"
TEMP_DIR: Path = OSS_NAVI_HOME / "temp"

# Subdirectories
REPORTS_DIR: Path = STATE_DIR / "reports"

# File paths
CONFIG_FILE: Path = STATE_DIR / "config.json"
TOKEN_FILE: Path = OSS_NAVI_HOME / ".token"
MEMORY_FILE: Path = STATE_DIR / "memory.json"
CACHE_METADATA_FILE: Path = CACHE_DIR / "metadata.json"

# Cache files
GITHUB_PROFILE_CACHE: Path = CACHE_DIR / "github_profile.json"
UPFORGRABS_TASKS_CACHE: Path = CACHE_DIR / "upforgrabs_tasks.json"
GOODFIRSTISSUE_TASKS_CACHE: Path = CACHE_DIR / "goodfirstissue_tasks.json"


def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    OSS_NAVI_HOME.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    STATE_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)


def get_report_path(report_id: str) -> Path:
    """Get the path for a report file by ID."""
    return REPORTS_DIR / f"report_{report_id}.md"


def get_current_report_path() -> Path:
    """Get the path for the current (temporary) report."""
    return TEMP_DIR / "current_report.md"
