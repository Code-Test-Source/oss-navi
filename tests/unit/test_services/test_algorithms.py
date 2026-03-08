"""Tests for recommendation algorithms."""

import pytest

from oss_navi.models.preferences import (
    BlockingRule,
    BlockType,
    LanguageProfile,
    LanguageType,
    SkillLevel,
    UserPreferences,
)
from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.services.algorithms.apriori import (
    AprioriMiner,
    TransactionDatabase,
    find_frequent_itemsets,
    generate_association_rules,
)
from oss_navi.services.algorithms.base import RecommenderConfig
from oss_navi.services.algorithms.fast import FastRecommender


class TestRecommenderConfig:
    """Tests for RecommenderConfig."""

    def test_create_config(self) -> None:
        """Test creating a RecommenderConfig."""
        config = RecommenderConfig(
            max_recommendations=5,
            min_score=2,
            include_learning_resources=False,
        )
        assert config.max_recommendations == 5
        assert config.min_score == 2

    def test_config_defaults(self) -> None:
        """Test RecommenderConfig defaults."""
        config = RecommenderConfig()
        assert config.max_recommendations == 10
        assert config.min_score == 1
        assert config.include_learning_resources is True


class TestFastRecommender:
    """Tests for FastRecommender."""

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

    def test_recommender_name(self) -> None:
        """Test name property."""
        recommender = FastRecommender()
        assert recommender.name == "fast"

    def test_recommender_mode(self) -> None:
        """Test mode property."""
        recommender = FastRecommender()
        assert recommender.mode == RecommendationMode.FAST

    def test_recommend(self, user_prefs: UserPreferences, cached_tasks: list[dict]) -> None:
        """Test recommend method."""
        recommender = FastRecommender()
        recommendations = recommender.recommend(user_prefs, cached_tasks)
        assert len(recommendations) > 0
        assert all(isinstance(r, Recommendation) for r in recommendations)

    def test_recommend_respects_max(
        self, user_prefs: UserPreferences, cached_tasks: list[dict]
    ) -> None:
        """Test recommend respects max_recommendations."""
        config = RecommenderConfig(max_recommendations=2)
        recommender = FastRecommender(config=config)
        recommendations = recommender.recommend(user_prefs, cached_tasks)
        assert len(recommendations) <= 2

    def test_recommend_with_rejected(
        self, user_prefs: UserPreferences, cached_tasks: list[dict]
    ) -> None:
        """Test recommend with rejected IDs."""
        recommender = FastRecommender()
        rejected = {"python/cpython"}
        recommendations = recommender.recommend(user_prefs, cached_tasks, rejected)
        for rec in recommendations:
            assert rec.project_name != "python/cpython"

    def test_recommend_with_blocking_rules(self, cached_tasks: list[dict]) -> None:
        """Test recommend respects blocking rules."""
        prefs = UserPreferences(
            languages=[LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED)],
            blocking_rules=[
                BlockingRule(block_type=BlockType.LANGUAGE, value="rust"),
            ],
        )
        recommender = FastRecommender()
        recommendations = recommender.recommend(prefs, cached_tasks)
        for rec in recommendations:
            assert rec.language.lower() != "rust"

    def test_recommend_no_language_match(self, cached_tasks: list[dict]) -> None:
        """Test recommend when no language matches (round 2)."""
        prefs = UserPreferences(
            languages=[LanguageProfile(language="go", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED)],
        )
        recommender = FastRecommender()
        recommendations = recommender.recommend(prefs, cached_tasks)
        # Should fall back to adjacent or popular
        assert isinstance(recommendations, list)

    def test_compute_language_match(self, user_prefs: UserPreferences) -> None:
        """Test compute_language_match method."""
        recommender = FastRecommender()

        # Primary match
        is_match, match_type = recommender.compute_language_match(
            {"language": "Python"}, user_prefs
        )
        assert is_match is True
        assert match_type == "primary"

        # Learning match
        is_match, match_type = recommender.compute_language_match(
            {"language": "Rust"}, user_prefs
        )
        assert is_match is True
        assert match_type == "learning"

        # No match
        is_match, match_type = recommender.compute_language_match(
            {"language": "Java"}, user_prefs
        )
        assert is_match is False
        assert match_type == "none"

    def test_compute_relevance_score(self, user_prefs: UserPreferences) -> None:
        """Test compute_relevance_score method."""
        recommender = FastRecommender()
        project = {
            "language": "Python",
            "stars": 60000,
            "good_first_issue_count": 50,
        }
        score = recommender.compute_relevance_score(project, user_prefs)
        assert 1 <= score <= 10

    def test_filter_by_blocking_rules(
        self, user_prefs: UserPreferences, cached_tasks: list[dict]
    ) -> None:
        """Test filter_by_blocking_rules method."""
        prefs_with_block = UserPreferences(
            languages=user_prefs.languages,
            blocking_rules=[
                BlockingRule(block_type=BlockType.LANGUAGE, value="javascript"),
            ],
        )
        recommender = FastRecommender()
        filtered = recommender.filter_by_blocking_rules(cached_tasks, prefs_with_block)
        for task in filtered:
            assert task.get("language", "").lower() != "javascript"

    def test_filter_by_rejected(self, cached_tasks: list[dict]) -> None:
        """Test filter_by_rejected method."""
        recommender = FastRecommender()
        rejected = {"python/cpython"}
        filtered = recommender.filter_by_rejected(cached_tasks, rejected)
        assert len(filtered) == 2


class TestAprioriMiner:
    """Tests for AprioriMiner."""

    @pytest.fixture
    def transactions(self) -> list[set[str]]:
        """Create test transactions."""
        return [
            {"python", "django", "web"},
            {"python", "flask", "web"},
            {"python", "django"},
            {"javascript", "react", "web"},
            {"javascript", "vue", "web"},
            {"rust", "systems"},
            {"python", "fastapi", "web"},
            {"python", "django", "api"},
        ]

    def test_find_frequent_itemsets(self, transactions: list[set[str]]) -> None:
        """Test find_frequent_itemsets function."""
        itemsets = find_frequent_itemsets(transactions, min_support=0.3)
        # Python appears in 5/8 = 0.625 transactions
        python_itemset = frozenset(["python"])
        assert python_itemset in itemsets

    def test_find_frequent_itemsets_empty(self) -> None:
        """Test find_frequent_itemsets with empty transactions."""
        itemsets = find_frequent_itemsets([])
        assert itemsets == {}

    def test_generate_association_rules(self, transactions: list[set[str]]) -> None:
        """Test generate_association_rules function."""
        itemsets = find_frequent_itemsets(transactions, min_support=0.3)
        rules = generate_association_rules(itemsets, transactions, min_confidence=0.5)
        assert isinstance(rules, list)

    def test_apriori_miner_mine_patterns(self, transactions: list[set[str]]) -> None:
        """Test AprioriMiner.mine_patterns method."""
        miner = AprioriMiner(min_support=0.3, min_confidence=0.5)
        patterns = miner.mine_patterns(transactions)
        assert isinstance(patterns, list)

    def test_apriori_miner_get_recommendations(
        self, transactions: list[set[str]]
    ) -> None:
        """Test AprioriMiner.get_recommendations_for_skills method."""
        miner = AprioriMiner(min_support=0.3, min_confidence=0.5)
        miner.mine_patterns(transactions)
        recommendations = miner.get_recommendations_for_skills(["python"])
        assert isinstance(recommendations, list)

    def test_transaction_database(self) -> None:
        """Test TransactionDatabase model."""
        db = TransactionDatabase()
        db.add_transaction({"a", "b", "c"})
        assert len(db.transactions) == 1
        db.clear()
        assert len(db.transactions) == 0


class TestContentBasedRecommender:
    """Tests for ContentBasedRecommender."""

    @pytest.fixture
    def user_prefs(self) -> UserPreferences:
        """Create test user preferences."""
        return UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED),
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
        ]

    def test_content_based_recommend(
        self, user_prefs: UserPreferences, cached_tasks: list[dict]
    ) -> None:
        """Test ContentBasedRecommender.recommend method."""
        from oss_navi.services.algorithms.content_based import ContentBasedRecommender

        recommender = ContentBasedRecommender()
        recommendations = recommender.recommend(user_prefs, cached_tasks)
        assert len(recommendations) > 0
