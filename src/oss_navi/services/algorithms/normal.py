"""Normal mode recommender using enhanced content-based filtering."""

from typing import TYPE_CHECKING

from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.services.algorithms.base import BaseRecommender, RecommenderConfig
from oss_navi.services.algorithms.content_based import ContentBasedRecommender

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences


class NormalRecommender(BaseRecommender):
    """Normal recommendation mode using enhanced content-based filtering.

    Characteristics:
    - Time: <60 seconds
    - Memory: <100MB
    - Requires: numpy (optional)
    - Better quality than fast mode with advanced scoring

    Uses enhanced content-based filtering with:
    - Multi-factor relevance scoring
    - Project similarity clustering
    - User preference learning
    """

    def __init__(self, config: RecommenderConfig | None = None):
        """Initialize the normal recommender.

        Args:
            config: Optional configuration for the recommender
        """
        super().__init__(config)
        self._content_based = ContentBasedRecommender(config)

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
        """Generate recommendations using enhanced content-based filtering.

        Applies advanced scoring and project similarity analysis
        for improved recommendation quality over fast mode.

        Args:
            user_preferences: User's language settings and blocking rules
            cached_tasks: List of cached OSS tasks/projects
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations sorted by relevance score
        """
        # Get content-based recommendations
        content_recs = self._content_based.recommend(
            user_preferences, cached_tasks, rejected_ids
        )

        # Enhance with similarity analysis
        enhanced_recs = self._enhance_with_similarity(
            content_recs, user_preferences, cached_tasks
        )

        return enhanced_recs

    def _enhance_with_similarity(
        self,
        content_recs: list[Recommendation],
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
    ) -> list[Recommendation]:
        """Enhance recommendations with project similarity analysis.

        Args:
            content_recs: Initial content-based recommendations
            user_preferences: User preferences
            cached_tasks: Cached tasks data

        Returns:
            Enhanced recommendations with similarity-adjusted scores
        """
        if not content_recs:
            return content_recs

        # Build project features for similarity analysis
        project_features = self._build_project_features(cached_tasks)

        # Get user's preferred languages for similarity boost
        user_langs = [lang.lower() for lang in user_preferences.get_all_languages()]
        user_domains = {d.domain.lower() for d in user_preferences.domain_interests}

        # Adjust scores based on similarity to user preferences
        for rec in content_recs:
            # Compute similarity score
            similarity = self._compute_similarity_score(
                rec.project_name, user_langs, user_domains, project_features
            )

            # Blend content score with similarity
            original_score = rec.relevance_score
            blended_score = int(original_score * 0.7 + similarity * 0.3 * 10) / 10
            rec.relevance_score = max(1, min(10, round(blended_score)))

            # Update confidence based on similarity
            if rec.confidence_score is not None:
                rec.confidence_score = (
                    rec.confidence_score * 0.7 + similarity * 0.3
                )

            # Update algorithm source
            rec.algorithm_source = "enhanced_content_based"

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
            # Handle nested repository structure
            repo = task.get("repository", task)
            name = repo.get("name", f"{repo.get('owner', '')}/{repo.get('name', '')}")

            lang = repo.get("language") or ""
            feature_set = {
                "language": lang.lower() if lang else "",
                "topics": {topic.lower() for topic in repo.get("topics") or []},
                "stars_bucket": self._star_bucket(repo.get("stars") or 0),
                "has_issues": task.get("good_first_issue_count", 0) > 0,
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
        user_langs: list[str],
        user_domains: set[str],
        project_features: dict,
    ) -> float:
        """Compute similarity score for a project (0-1 scale).

        Args:
            project_name: Name of the project
            user_langs: User's preferred languages
            user_domains: User's domain interests
            project_features: Project feature dictionary

        Returns:
            Similarity score (0-1)
        """
        if project_name not in project_features:
            return 0.5

        features = project_features[project_name]
        score = 0.5

        # Language match bonus
        if features["language"] in user_langs:
            score += 0.3

        # Topic/domain match bonus
        topic_overlap = len(features["topics"] & user_domains)
        if topic_overlap > 0:
            score += min(0.2, topic_overlap * 0.05)

        # Good first issues bonus
        if features["has_issues"]:
            score += 0.05

        return min(1.0, score)
