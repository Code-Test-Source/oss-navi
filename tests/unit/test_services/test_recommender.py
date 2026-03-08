"""Tests for recommender service."""

import pytest

from oss_navi.models.preferences import (
    BlockingRule,
    BlockType,
    LanguageProfile,
    LanguageType,
    SkillLevel,
    UserPreferences,
)
from oss_navi.models.recommendation import RecommendationMode
from oss_navi.services.recommender import RecommenderService, create_recommender_service


class TestRecommenderService:
    """Tests for RecommenderService."""

    @pytest.fixture
    def user_prefs(self) -> UserPreferences:
        """Create test user preferences."""
        return UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED),
                LanguageProfile(language="rust", type=LanguageType.LEARNING, skill_level=SkillLevel.BEGINNER),
            ],
        )

    @pytest.fixture
    def cached_tasks(self) -> list[dict]:
        """Create test cached tasks."""
        return [
            {
                "owner": "python",
                "name": "cpython",
                "language": "Python",
                "stars": 60000,
                "good_first_issue_count": 50,
            },
            {
                "owner": "rust-lang",
                "name": "rust",
                "language": "Rust",
                "stars": 90000,
                "good_first_issue_count": 100,
            },
            {
                "owner": "nodejs",
                "name": "node",
                "language": "JavaScript",
                "stars": 100000,
                "good_first_issue_count": 30,
            },
        ]

    def test_create_fast_recommender(self) -> None:
        """Test creating a fast mode recommender."""
        service = RecommenderService(mode=RecommendationMode.FAST)
        assert service.mode == RecommendationMode.FAST

    def test_create_normal_recommender(self) -> None:
        """Test creating a normal mode recommender."""
        service = RecommenderService(mode=RecommendationMode.NORMAL)
        # May be downgraded to fast if dependencies missing
        assert service.mode in [RecommendationMode.NORMAL, RecommendationMode.FAST]

    def test_get_mode_config(self) -> None:
        """Test get_mode_config method."""
        service = RecommenderService(mode=RecommendationMode.FAST)
        config = service.get_mode_config()
        assert config.mode == RecommendationMode.FAST

    def test_recommend(self, user_prefs: UserPreferences, cached_tasks: list[dict]) -> None:
        """Test recommend method."""
        service = RecommenderService(mode=RecommendationMode.FAST)
        recommendations = service.recommend(user_prefs, cached_tasks)
        assert len(recommendations) > 0
        assert all(r.relevance_score >= 1 for r in recommendations)

    def test_recommend_with_rejected(
        self, user_prefs: UserPreferences, cached_tasks: list[dict]
    ) -> None:
        """Test recommend with rejected IDs."""
        service = RecommenderService(mode=RecommendationMode.FAST)
        rejected = {"python/cpython"}
        recommendations = service.recommend(user_prefs, cached_tasks, rejected)
        # Python project should be excluded
        for rec in recommendations:
            assert rec.project_name != "python/cpython"

    def test_recommend_with_blocking_rules(
        self, cached_tasks: list[dict]
    ) -> None:
        """Test recommend respects blocking rules."""
        prefs = UserPreferences(
            languages=[LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED)],
            blocking_rules=[
                BlockingRule(block_type=BlockType.LANGUAGE, value="rust"),
            ],
        )
        service = RecommenderService(mode=RecommendationMode.FAST)
        recommendations = service.recommend(prefs, cached_tasks)
        for rec in recommendations:
            assert rec.language.lower() != "rust"

    def test_compute_relevance_score(self, user_prefs: UserPreferences) -> None:
        """Test compute_relevance_score method."""
        service = RecommenderService(mode=RecommendationMode.FAST)

        project = {
            "owner": "python",
            "name": "cpython",
            "language": "Python",
            "stars": 60000,
            "good_first_issue_count": 50,
        }
        score, reasoning = service.compute_relevance_score(project, user_prefs)
        assert 1 <= score <= 10
        assert "primary" in reasoning.lower() or "popular" in reasoning.lower()

    def test_compute_relevance_score_secondary(
        self, cached_tasks: list[dict]
    ) -> None:
        """Test relevance score for secondary language."""
        prefs = UserPreferences(
            languages=[LanguageProfile(language="rust", type=LanguageType.SECONDARY, skill_level=SkillLevel.INTERMEDIATE)],
        )
        service = RecommenderService(mode=RecommendationMode.FAST)

        project = {
            "owner": "rust-lang",
            "name": "rust",
            "language": "Rust",
            "stars": 90000,
            "good_first_issue_count": 100,
        }
        score, _ = service.compute_relevance_score(project, prefs)
        assert score >= 5  # Base score + secondary match + stars

    def test_compute_skill_gaps(self, user_prefs: UserPreferences) -> None:
        """Test _compute_skill_gaps method."""
        from oss_navi.models.recommendation import Recommendation

        service = RecommenderService(mode=RecommendationMode.FAST)

        # Recommendation in a language the user doesn't know
        rec = Recommendation(
            recommendation_id="rec-1",
            project_name="golang/go",
            project_url="https://github.com/golang/go",
            language="Go",
            relevance_score=7,
            reasoning="Test",
            algorithm_source="content_based",
            mode=RecommendationMode.FAST,
        )
        gaps = service._compute_skill_gaps(rec, user_prefs)
        assert "Learn Go" in gaps

    def test_create_recommender_service_factory(self) -> None:
        """Test create_recommender_service factory function."""
        service = create_recommender_service(mode="fast", max_recommendations=5)
        assert service.mode == RecommendationMode.FAST
        assert service.config.max_recommendations == 5

    def test_recommend_empty_tasks(self, user_prefs: UserPreferences) -> None:
        """Test recommend with empty tasks."""
        service = RecommenderService(mode=RecommendationMode.FAST)
        recommendations = service.recommend(user_prefs, [])
        assert recommendations == []

    def test_recommend_no_language_prefs(self, cached_tasks: list[dict]) -> None:
        """Test recommend with no language preferences."""
        prefs = UserPreferences()  # No languages
        service = RecommenderService(mode=RecommendationMode.FAST)
        recommendations = service.recommend(prefs, cached_tasks)
        # Should still return recommendations
        assert isinstance(recommendations, list)
