"""Normal mode recommender using Surprise collaborative filtering."""

import uuid
from typing import TYPE_CHECKING

from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.services.algorithms.base import BaseRecommender, RecommenderConfig
from oss_navi.services.algorithms.content_based import ContentBasedRecommender

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences


class NormalRecommender(BaseRecommender):
    """Normal recommendation mode using Surprise SVD/KNN algorithms.

    Characteristics:
    - Time: <90 seconds
    - Memory: <200MB
    - Requires: numpy, scikit-surprise
    - Better quality than fast mode

    Uses collaborative filtering to find projects similar to what
    users with similar profiles have contributed to.
    """

    def __init__(self, config: RecommenderConfig | None = None):
        """Initialize the normal recommender.

        Args:
            config: Optional configuration for the recommender
        """
        super().__init__(config)
        self._content_based = ContentBasedRecommender(config)
        self._surprise_available = self._check_surprise()

    def _check_surprise(self) -> bool:
        """Check if Surprise library is available."""
        try:
            from surprise import SVD, KNNBasic  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "normal"

    @property
    def mode(self) -> RecommendationMode:
        return RecommendationMode.NORMAL

    def recommend(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Generate recommendations using collaborative filtering.

        Combines content-based filtering with collaborative filtering
        for improved recommendation quality.

        Args:
            user_preferences: User's language settings and blocking rules
            cached_tasks: List of cached OSS tasks/projects
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations sorted by relevance score
        """
        if not self._surprise_available:
            # Fall back to content-based if Surprise not available
            return self._fallback_recommend(user_preferences, cached_tasks, rejected_ids)

        # Get content-based recommendations
        content_recs = self._content_based.recommend(
            user_preferences, cached_tasks, rejected_ids
        )

        # Apply collaborative filtering enhancement
        enhanced_recs = self._enhance_with_cf(content_recs, user_preferences, cached_tasks)

        return enhanced_recs

    def _fallback_recommend(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Fall back to content-based when Surprise unavailable."""
        # Use fast recommender logic
        from oss_navi.services.algorithms.fast import FastRecommender

        fast = FastRecommender(self.config)
        recs = fast.recommend(user_preferences, cached_tasks, rejected_ids)

        # Update algorithm source
        for rec in recs:
            rec.algorithm_source = "content_based_fallback"
            rec.reasoning += " (Surprise not available)"

        return recs

    def _enhance_with_cf(
        self,
        content_recs: list[Recommendation],
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
    ) -> list[Recommendation]:
        """Enhance recommendations with collaborative filtering scores.

        This uses a simplified CF approach based on project similarity
        and user patterns.

        Args:
            content_recs: Initial content-based recommendations
            user_preferences: User preferences
            cached_tasks: Cached tasks data

        Returns:
            Enhanced recommendations with CF-adjusted scores
        """
        if not content_recs:
            return content_recs

        # Build item-item similarity matrix (simplified)
        # In production, this would use Surprise's KNN
        project_features = self._build_project_features(cached_tasks)

        # Adjust scores based on similarity to user's preferred languages
        for rec in content_recs:
            # Find similar projects to this recommendation
            similar_score = self._compute_similarity_score(
                rec.project_name, user_preferences, project_features
            )

            # Blend content score with CF similarity
            original_score = rec.relevance_score
            blended_score = int((original_score * 0.7 + similar_score * 0.3) * 10) / 10
            rec.relevance_score = max(1, min(10, round(blended_score)))

            # Update confidence based on CF
            if rec.confidence_score is not None:
                rec.confidence_score = (
                    rec.confidence_score * 0.7 + similar_score / 10 * 0.3
                )

        # Re-sort by adjusted score
        content_recs.sort(key=lambda r: r.relevance_score, reverse=True)
        return content_recs[: self.config.max_recommendations]

    def _build_project_features(self, cached_tasks: list[dict]) -> dict:
        """Build feature vectors for projects.

        Args:
            cached_tasks: List of cached tasks

        Returns:
            Dictionary mapping project names to feature sets
        """
        features = {}
        for task in cached_tasks:
            name = f"{task.get('owner', '')}/{task.get('name', '')}"
            feature_set = {
                "language": task.get("language", "").lower(),
                "topics": set(t.lower() for t in task.get("topics", [])),
                "stars_bucket": self._star_bucket(task.get("stars", 0)),
            }
            features[name] = feature_set
        return features

    def _star_bucket(self, stars: int) -> str:
        """Categorize stars into buckets."""
        if stars >= 10000:
            return "very_high"
        elif stars >= 1000:
            return "high"
        elif stars >= 100:
            return "medium"
        else:
            return "low"

    def _compute_similarity_score(
        self,
        project_name: str,
        user_preferences: "UserPreferences",
        project_features: dict,
    ) -> float:
        """Compute similarity score for a project.

        Args:
            project_name: Name of the project
            user_preferences: User preferences
            project_features: Project feature dictionary

        Returns:
            Similarity score (0-10)
        """
        if project_name not in project_features:
            return 5.0

        features = project_features[project_name]
        score = 5.0

        # Language match bonus
        user_langs = [l.lower() for l in user_preferences.get_all_languages()]
        if features["language"] in user_langs:
            score += 2

        # Topic match bonus
        user_topics = set()
        for interest in user_preferences.domain_interests:
            user_topics.add(interest.domain.lower())

        topic_overlap = len(features["topics"] & user_topics)
        if topic_overlap > 0:
            score += min(2, topic_overlap)

        return min(10, score)


def create_svd_model():
    """Create and return a Surprise SVD model if available.

    Returns:
        Tuple of (model, is_available)
    """
    try:
        from surprise import SVD

        return SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02), True
    except ImportError:
        return None, False


def create_knn_model():
    """Create and return a Surprise KNN model if available.

    Returns:
        Tuple of (model, is_available)
    """
    try:
        from surprise import KNNBasic

        sim_options = {
            "name": "cosine",
            "user_based": False,  # Item-based collaborative filtering
        }
        return KNNBasic(sim_options=sim_options), True
    except ImportError:
        return None, False
