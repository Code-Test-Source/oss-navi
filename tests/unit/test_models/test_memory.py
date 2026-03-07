"""Unit tests for LongTermMemory model."""

from datetime import datetime, timezone

import pytest

from oss_navi.models.memory import (
    GitHubProfileSummary,
    GreatProjectSummary,
    LongTermMemory,
    PastRecommendation,
    SkillSnapshot,
)


class TestPastRecommendation:
    """Tests for PastRecommendation model."""

    def test_create_past_recommendation(self) -> None:
        """Test creating a PastRecommendation with required fields."""
        rec = PastRecommendation(
            project="python/cpython",
            issue_url="https://github.com/python/cpython/issues/123",
            date=datetime(2026, 3, 7, tzinfo=timezone.utc),
        )
        assert rec.project == "python/cpython"
        assert rec.issue_url == "https://github.com/python/cpython/issues/123"

    def test_past_recommendation_optional_fields(self) -> None:
        """Test PastRecommendation with optional fields."""
        rec = PastRecommendation(
            project="pallets/click",
            issue_url="https://github.com/pallets/click/issues/456",
            date=datetime(2026, 3, 7, tzinfo=timezone.utc),
            reason="CLI library",
            status="viewed",
        )
        assert rec.reason == "CLI library"
        assert rec.status == "viewed"


class TestSkillSnapshot:
    """Tests for SkillSnapshot model."""

    def test_create_skill_snapshot(self) -> None:
        """Test creating a SkillSnapshot."""
        snapshot = SkillSnapshot(
            date=datetime(2026, 3, 7, tzinfo=timezone.utc),
            languages={"Python": 0.6, "TypeScript": 0.3},
            top_repos=["owner/repo1", "owner/repo2"],
            focus_areas=["web", "cli"],
        )
        assert snapshot.languages["Python"] == 0.6
        assert "owner/repo1" in snapshot.top_repos
        assert "web" in snapshot.focus_areas

    def test_skill_snapshot_defaults(self) -> None:
        """Test SkillSnapshot with default values."""
        snapshot = SkillSnapshot(date=datetime(2026, 3, 7, tzinfo=timezone.utc))
        assert snapshot.languages == {}
        assert snapshot.top_repos == []
        assert snapshot.focus_areas == []


class TestLongTermMemory:
    """Tests for LongTermMemory model."""

    @pytest.fixture
    def sample_recommendations(self) -> list[PastRecommendation]:
        """Create sample recommendations."""
        return [
            PastRecommendation(
                project="python/cpython",
                issue_url="https://github.com/python/cpython/issues/1",
                date=datetime(2026, 3, 1, tzinfo=timezone.utc),
                reason="Learn Python internals",
            ),
            PastRecommendation(
                project="pallets/click",
                issue_url="https://github.com/pallets/click/issues/2",
                date=datetime(2026, 3, 5, tzinfo=timezone.utc),
                reason="CLI library",
            ),
        ]

    @pytest.fixture
    def sample_skill_snapshot(self) -> SkillSnapshot:
        """Create a sample skill snapshot."""
        return SkillSnapshot(
            date=datetime(2026, 3, 7, tzinfo=timezone.utc),
            languages={"Python": 0.8},
            top_repos=["owner/repo1"],
            focus_areas=["web"],
        )

    def test_create_long_term_memory(
        self, sample_recommendations: list[PastRecommendation], sample_skill_snapshot: SkillSnapshot
    ) -> None:
        """Test creating LongTermMemory with all fields."""
        memory = LongTermMemory(
            past_recommendations=sample_recommendations,
            skill_history=[sample_skill_snapshot],
        )
        assert len(memory.past_recommendations) == 2
        assert len(memory.skill_history) == 1

    def test_long_term_memory_defaults(self) -> None:
        """Test LongTermMemory with defaults."""
        memory = LongTermMemory()
        assert memory.past_recommendations == []
        assert memory.skill_history == []

    def test_long_term_memory_serialization(
        self, sample_recommendations: list[PastRecommendation]
    ) -> None:
        """Test LongTermMemory serialization."""
        memory = LongTermMemory(past_recommendations=sample_recommendations)
        data = memory.model_dump()

        assert "past_recommendations" in data
        assert len(data["past_recommendations"]) == 2

    def test_add_recommendation(self) -> None:
        """Test adding a recommendation."""
        memory = LongTermMemory()
        rec = PastRecommendation(
            project="test/repo",
            issue_url="https://github.com/test/repo/issues/1",
            date=datetime(2026, 3, 7, tzinfo=timezone.utc),
        )
        memory.add_recommendation(rec)
        assert len(memory.past_recommendations) == 1

    def test_add_skill_snapshot(self) -> None:
        """Test adding a skill snapshot."""
        memory = LongTermMemory()
        snapshot = SkillSnapshot(date=datetime(2026, 3, 7, tzinfo=timezone.utc))
        memory.add_skill_snapshot(snapshot)
        assert len(memory.skill_history) == 1

    def test_add_learning_goal(self) -> None:
        """Test adding a learning goal."""
        memory = LongTermMemory()
        memory.add_learning_goal("Learn Rust")
        assert "Learn Rust" in memory.learning_goals

        # Should not add duplicate
        memory.add_learning_goal("Learn Rust")
        assert len(memory.learning_goals) == 1


class TestGitHubProfileSummary:
    """Tests for GitHubProfileSummary model (T120)."""

    def test_create_github_profile_summary(self) -> None:
        """Test creating a GitHubProfileSummary."""
        summary = GitHubProfileSummary(
            username="testuser",
            primary_languages={"Python": 0.6, "TypeScript": 0.4},
            total_repos=42,
            last_fetched=datetime(2026, 3, 7, tzinfo=timezone.utc),
        )
        assert summary.username == "testuser"
        assert summary.primary_languages["Python"] == 0.6
        assert summary.total_repos == 42

    def test_github_profile_summary_languages(self) -> None:
        """Test GitHubProfileSummary language distribution."""
        summary = GitHubProfileSummary(
            username="developer",
            primary_languages={"Rust": 0.5, "Go": 0.3, "Python": 0.2},
            total_repos=10,
            last_fetched=datetime.now(timezone.utc),
        )
        assert len(summary.primary_languages) == 3
        assert summary.primary_languages["Rust"] == 0.5


class TestLongTermMemoryNewFields:
    """Tests for new LongTermMemory fields (T121, T122)."""

    def test_long_term_memory_github_profile_field(self) -> None:
        """Test LongTermMemory with github_profile field."""
        profile_summary = GitHubProfileSummary(
            username="testuser",
            primary_languages={"Python": 0.7},
            total_repos=25,
            last_fetched=datetime.now(timezone.utc),
        )
        memory = LongTermMemory(github_profile=profile_summary)
        assert memory.github_profile is not None
        assert memory.github_profile.username == "testuser"
        assert memory.github_profile.total_repos == 25

    def test_long_term_memory_analysis_count_field(self) -> None:
        """Test LongTermMemory with analysis_count field."""
        memory = LongTermMemory()
        assert memory.analysis_count == 0

        # Simulate incrementing analysis count
        memory.analysis_count = 1
        assert memory.analysis_count == 1

    def test_long_term_memory_last_analysis_date_field(self) -> None:
        """Test LongTermMemory with last_analysis_date field."""
        memory = LongTermMemory()
        assert memory.last_analysis_date is None

        now = datetime.now(timezone.utc)
        memory.last_analysis_date = now
        assert memory.last_analysis_date == now

    def test_long_term_memory_version_3(self) -> None:
        """Test LongTermMemory version is 3."""
        memory = LongTermMemory()
        assert memory.version == 3

    def test_long_term_memory_full_serialization(self) -> None:
        """Test LongTermMemory serialization with all new fields."""
        profile_summary = GitHubProfileSummary(
            username="testuser",
            primary_languages={"Python": 0.8},
            total_repos=50,
            last_fetched=datetime(2026, 3, 7, tzinfo=timezone.utc),
        )
        memory = LongTermMemory(
            github_profile=profile_summary,
            last_analysis_date=datetime(2026, 3, 8, tzinfo=timezone.utc),
            analysis_count=5,
        )
        data = memory.model_dump()

        assert data["version"] == 3
        assert data["github_profile"]["username"] == "testuser"
        assert data["analysis_count"] == 5
        assert data["last_analysis_date"] is not None
