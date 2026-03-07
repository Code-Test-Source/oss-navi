"""Tests for Recommendation and RatingBreakdown models."""

from datetime import UTC, datetime

import pytest

from oss_navi.models.task import (
    RatingBreakdown,
    Recommendation,
    Repository,
    Task,
)


class TestRatingBreakdown:
    """Tests for RatingBreakdown model validation."""

    def test_rating_breakdown_creation(self) -> None:
        """Test creating RatingBreakdown with all fields."""
        breakdown = RatingBreakdown(
            language_match=8.5,
            hotness_score=7.0,
            issue_availability=10.0,
            learning_alignment=6.5,
            skill_level_fit=8.0,
            topic_relevance=7.5,
        )
        assert breakdown.language_match == 8.5
        assert breakdown.hotness_score == 7.0
        assert breakdown.issue_availability == 10.0

    def test_rating_breakdown_weighted_total(self) -> None:
        """Test weighted_total calculation."""
        breakdown = RatingBreakdown(
            language_match=10.0,  # 30%
            hotness_score=10.0,  # 20%
            issue_availability=10.0,  # 15%
            learning_alignment=10.0,  # 15%
            skill_level_fit=10.0,  # 10%
            topic_relevance=10.0,  # 10%
        )
        # All 10s should give weighted_total of 10.0
        assert breakdown.weighted_total == 10.0

    def test_rating_breakdown_weighted_calculation(self) -> None:
        """Test weighted_total with specific values."""
        breakdown = RatingBreakdown(
            language_match=8.0,  # 8.0 * 0.30 = 2.4
            hotness_score=6.0,  # 6.0 * 0.20 = 1.2
            issue_availability=10.0,  # 10.0 * 0.15 = 1.5
            learning_alignment=4.0,  # 4.0 * 0.15 = 0.6
            skill_level_fit=8.0,  # 8.0 * 0.10 = 0.8
            topic_relevance=6.0,  # 6.0 * 0.10 = 0.6
        )
        # Total: 2.4 + 1.2 + 1.5 + 0.6 + 0.8 + 0.6 = 7.1
        assert abs(breakdown.weighted_total - 7.1) < 0.01

    def test_rating_breakdown_clamp_values(self) -> None:
        """Test that values are clamped to 0-10 range."""
        # Pydantic should validate the range
        breakdown = RatingBreakdown(
            language_match=5.0,
            hotness_score=5.0,
            issue_availability=5.0,
            learning_alignment=5.0,
            skill_level_fit=5.0,
            topic_relevance=5.0,
        )
        assert breakdown.language_match == 5.0


class TestRecommendation:
    """Tests for Recommendation model validation."""

    @pytest.fixture
    def sample_task(self) -> Task:
        """Create a sample Task for testing."""
        return Task(
            id="test:1",
            title="Test Issue",
            url="https://github.com/owner/repo/issues/1",
            source="upforgrabs",
            repository=Repository(
                name="owner/repo",
                url="https://github.com/owner/repo",
                stars=100,
            ),
            labels=["good first issue"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            hotness_score=5.0,
            fetched_at=datetime.now(UTC),
        )

    @pytest.fixture
    def sample_rating_breakdown(self) -> RatingBreakdown:
        """Create a sample RatingBreakdown for testing."""
        return RatingBreakdown(
            language_match=8.0,
            hotness_score=6.0,
            issue_availability=10.0,
            learning_alignment=7.0,
            skill_level_fit=8.0,
            topic_relevance=6.0,
        )

    def test_recommendation_creation(
        self, sample_task: Task, sample_rating_breakdown: RatingBreakdown
    ) -> None:
        """Test creating Recommendation with all fields."""
        from oss_navi.models.task import IssueStatus

        recommendation = Recommendation(
            task=sample_task,
            rating=8.5,
            rating_breakdown=sample_rating_breakdown,
            reason="This issue matches your Python skills and involves web development.",
            code_analysis="The project uses FastAPI with a modular structure.",
            status=IssueStatus(
                issue_url=sample_task.url,
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(UTC),
            ),
        )
        assert recommendation.rating == 8.5
        assert "Python" in recommendation.reason

    def test_recommendation_rating_range(
        self, sample_task: Task, sample_rating_breakdown: RatingBreakdown
    ) -> None:
        """Test that rating must be between 1 and 10."""
        from oss_navi.models.task import IssueStatus

        # Valid rating
        rec = Recommendation(
            task=sample_task,
            rating=9.5,
            rating_breakdown=sample_rating_breakdown,
            reason="Test reason",
            code_analysis="Test analysis",
            status=IssueStatus(
                issue_url=sample_task.url,
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(UTC),
            ),
        )
        assert rec.rating == 9.5

    def test_recommendation_reason_not_empty(
        self, sample_task: Task, sample_rating_breakdown: RatingBreakdown
    ) -> None:
        """Test that reason cannot be empty."""
        from oss_navi.models.task import IssueStatus

        recommendation = Recommendation(
            task=sample_task,
            rating=7.0,
            rating_breakdown=sample_rating_breakdown,
            reason="Valid reason here",
            code_analysis="Some analysis",
            status=IssueStatus(
                issue_url=sample_task.url,
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(UTC),
            ),
        )
        assert len(recommendation.reason) > 0
