"""Pytest configuration and fixtures for OSS-Navi tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_home() -> Generator[Path, None, None]:
    """Create a temporary directory to use as OSS_NAVI_HOME."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_home_env(temp_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set OSS_NAVI_HOME environment variable to a temp directory."""
    monkeypatch.setenv("OSS_NAVI_HOME", str(temp_home))
    return temp_home


@pytest.fixture
def sample_user_profile() -> dict:
    """Sample GitHub user profile data for testing."""
    return {
        "username": "testuser",
        "name": "Test User",
        "bio": "Test bio",
        "public_repos": 42,
        "followers": 100,
        "following": 50,
        "languages": {"Python": 0.6, "TypeScript": 0.3, "Go": 0.1},
        "recent_activity": [],
        "top_repos": [],
        "fetched_at": "2026-03-07T10:00:00Z",
        "expires_at": "2026-03-08T10:00:00Z",
    }


@pytest.fixture
def sample_task() -> dict:
    """Sample task data for testing."""
    return {
        "id": "upforgrabs:12345",
        "title": "Fix bug in authentication",
        "description": "A bug in the auth module...",
        "url": "https://github.com/owner/repo/issues/12345",
        "source": "upforgrabs",
        "repository": {
            "name": "owner/repo",
            "url": "https://github.com/owner/repo",
            "stars": 1000,
            "language": "Python",
            "description": "A sample repository",
            "topics": ["python", "api"],
            "is_archived": False,
            "last_updated": "2026-03-01T00:00:00Z",
        },
        "labels": ["good first issue", "help wanted"],
        "created_at": "2026-03-01T00:00:00Z",
        "updated_at": "2026-03-05T00:00:00Z",
        "hotness_score": 33.33,
        "fetched_at": "2026-03-07T10:00:00Z",
    }


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration data for testing."""
    return {
        "github_username": "testuser",
        "blog_repo_path": "/home/user/blog",
        "filters": {
            "min_stars": 50,
            "max_age_days": 90,
            "limit": 100,
        },
        "created_at": "2026-03-07T10:00:00Z",
        "updated_at": "2026-03-07T10:00:00Z",
    }
