"""Unit tests for Task and Repository models."""

from datetime import datetime, timezone

import pytest

from oss_navi.models.task import Repository, Task, calculate_hotness_score


class TestRepository:
    """Tests for Repository model."""

    def test_create_repository(self) -> None:
        """Test creating a Repository with required fields."""
        repo = Repository(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=100,
        )
        assert repo.name == "owner/repo"
        assert repo.stars == 100
        assert repo.language is None

    def test_repository_with_optional_fields(self) -> None:
        """Test creating a Repository with optional fields."""
        repo = Repository(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=500,
            language="Python",
            description="A test repository",
            topics=["web", "api"],
            is_archived=False,
        )
        assert repo.language == "Python"
        assert repo.description == "A test repository"
        assert "web" in repo.topics

    def test_repository_invalid_url(self) -> None:
        """Test that invalid URLs raise validation error."""
        with pytest.raises(ValueError):
            Repository(
                name="owner/repo",
                url="https://gitlab.com/owner/repo",
                stars=100,
            )

    def test_repository_negative_stars(self) -> None:
        """Test that negative stars raise validation error."""
        with pytest.raises(ValueError):
            Repository(
                name="owner/repo",
                url="https://github.com/owner/repo",
                stars=-1,
            )


class TestTask:
    """Tests for Task model."""

    @pytest.fixture
    def sample_repo(self) -> Repository:
        """Create a sample repository for testing."""
        return Repository(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=100,
            language="Python",
        )

    @pytest.fixture
    def sample_datetime(self) -> datetime:
        """Create a sample datetime for testing."""
        return datetime(2026, 3, 7, 12, 0, 0, tzinfo=timezone.utc)

    def test_create_task(self, sample_repo: Repository, sample_datetime: datetime) -> None:
        """Test creating a Task with required fields."""
        task = Task(
            id="upforgrabs:123",
            title="Fix bug in authentication",
            url="https://github.com/owner/repo/issues/123",
            source="upforgrabs",
            repository=sample_repo,
            labels=["good first issue"],
            created_at=sample_datetime,
            updated_at=sample_datetime,
            hotness_score=10.0,
            fetched_at=sample_datetime,
        )
        assert task.id == "upforgrabs:123"
        assert task.title == "Fix bug in authentication"
        assert task.source == "upforgrabs"

    def test_task_invalid_source(self, sample_repo: Repository, sample_datetime: datetime) -> None:
        """Test that invalid source raises validation error."""
        with pytest.raises(ValueError):
            Task(
                id="invalid:123",
                title="Test",
                url="https://github.com/owner/repo/issues/123",
                source="invalid_source",
                repository=sample_repo,
                labels=[],
                created_at=sample_datetime,
                updated_at=sample_datetime,
                hotness_score=1.0,
                fetched_at=sample_datetime,
            )

    def test_task_invalid_url(self, sample_repo: Repository, sample_datetime: datetime) -> None:
        """Test that invalid URL raises validation error."""
        with pytest.raises(ValueError):
            Task(
                id="upforgrabs:123",
                title="Test",
                url="https://gitlab.com/owner/repo/issues/123",
                source="upforgrabs",
                repository=sample_repo,
                labels=[],
                created_at=sample_datetime,
                updated_at=sample_datetime,
                hotness_score=1.0,
                fetched_at=sample_datetime,
            )


class TestCalculateHotnessScore:
    """Tests for hotness score calculation."""

    def test_calculate_hotness_score_basic(self) -> None:
        """Test basic hotness score calculation."""
        score = calculate_hotness_score(stars=100, age_in_days=10)
        assert score == 10.0

    def test_calculate_hotness_score_zero_age(self) -> None:
        """Test hotness score with zero age (should use 1)."""
        score = calculate_hotness_score(stars=100, age_in_days=0)
        assert score == 100.0

    def test_calculate_hotness_score_decimal(self) -> None:
        """Test hotness score with decimal result."""
        score = calculate_hotness_score(stars=100, age_in_days=3)
        assert score == 33.33

    def test_calculate_hotness_score_high_stars(self) -> None:
        """Test hotness score with high star count."""
        score = calculate_hotness_score(stars=10000, age_in_days=1)
        assert score == 10000.0
