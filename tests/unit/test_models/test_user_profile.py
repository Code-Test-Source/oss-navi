"""Unit tests for UserProfile model."""

from datetime import datetime, timezone

import pytest

from oss_navi.models.user_profile import Activity, Language, UserProfile


class TestLanguage:
    """Tests for Language model."""

    def test_create_language(self) -> None:
        """Test creating a Language with required fields."""
        lang = Language(name="Python", bytes=60000, percentage=0.6)
        assert lang.name == "Python"
        assert lang.percentage == 0.6
        assert lang.bytes == 60000

    def test_language_percentage_bounds(self) -> None:
        """Test that percentage must be between 0 and 1."""
        # Valid bounds
        lang = Language(name="Python", bytes=0, percentage=0.0)
        assert lang.percentage == 0.0

        lang = Language(name="Python", bytes=100, percentage=1.0)
        assert lang.percentage == 1.0


class TestActivity:
    """Tests for Activity model."""

    def test_create_activity(self) -> None:
        """Test creating an Activity with required fields."""
        activity = Activity(
            type="PushEvent",
            repo_name="owner/repo",
            created_at=datetime(2026, 3, 7, tzinfo=timezone.utc),
        )
        assert activity.repo_name == "owner/repo"
        assert activity.type == "PushEvent"


class TestUserProfile:
    """Tests for UserProfile model."""

    @pytest.fixture
    def sample_languages(self) -> dict[str, float]:
        """Create sample languages for testing."""
        return {
            "Python": 0.6,
            "TypeScript": 0.3,
            "Go": 0.1,
        }

    @pytest.fixture
    def sample_activities(self) -> list[Activity]:
        """Create sample activities for testing."""
        return [
            Activity(
                type="PushEvent",
                repo_name="owner/repo1",
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            ),
            Activity(
                type="PullRequestEvent",
                repo_name="owner/repo2",
                created_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
            ),
        ]

    def test_create_user_profile(self, sample_languages: dict[str, float]) -> None:
        """Test creating a UserProfile with required fields."""
        now = datetime.now(timezone.utc)
        profile = UserProfile(
            username="testuser",
            languages=sample_languages,
            public_repos=42,
            followers=10,
            following=5,
            fetched_at=now,
            expires_at=now,
        )
        assert profile.username == "testuser"
        assert len(profile.languages) == 3
        assert profile.public_repos == 42

    def test_user_profile_with_activities(
        self, sample_languages: dict[str, float], sample_activities: list[Activity]
    ) -> None:
        """Test creating a UserProfile with activities."""
        now = datetime.now(timezone.utc)
        profile = UserProfile(
            username="testuser",
            languages=sample_languages,
            public_repos=42,
            followers=10,
            following=5,
            recent_activity=sample_activities,
            fetched_at=now,
            expires_at=now,
        )
        assert len(profile.recent_activity) == 2

    def test_user_profile_serialization(self, sample_languages: dict[str, float]) -> None:
        """Test UserProfile serialization to dict."""
        now = datetime.now(timezone.utc)
        profile = UserProfile(
            username="testuser",
            languages=sample_languages,
            public_repos=42,
            followers=10,
            following=5,
            fetched_at=now,
            expires_at=now,
        )
        data = profile.model_dump()
        assert data["username"] == "testuser"
        assert len(data["languages"]) == 3
