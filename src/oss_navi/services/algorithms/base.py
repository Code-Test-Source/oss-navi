"""Abstract base class for recommendation algorithms."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

from oss_navi.models.recommendation import Recommendation, RecommendationMode

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences


class RecommenderConfig(BaseModel):
    """Configuration for a recommender algorithm."""

    max_recommendations: int = 10
    min_score: int = 1
    include_learning_resources: bool = True


class BaseRecommender(ABC):
    """Abstract base class for all recommendation algorithms.

    Each concrete implementation provides recommendations based on different
    algorithms and trade-offs between speed, accuracy, and resource usage.
    """

    def __init__(self, config: RecommenderConfig | None = None):
        """Initialize the recommender with optional configuration.

        Args:
            config: Optional configuration for the recommender
        """
        self.config = config or RecommenderConfig()

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this recommender algorithm."""
        pass

    @property
    @abstractmethod
    def mode(self) -> RecommendationMode:
        """Get the recommendation mode this algorithm belongs to."""
        pass

    @abstractmethod
    def recommend(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Generate recommendations based on user preferences and cached tasks.

        Args:
            user_preferences: User's language settings, skill levels, and blocking rules
            cached_tasks: List of cached OSS tasks/projects from sync
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations, sorted by relevance score (highest first)
        """
        pass

    def filter_by_blocking_rules(
        self,
        projects: list[dict],
        user_preferences: "UserPreferences",
    ) -> list[dict]:
        """Remove projects that match user's blocking rules.

        Args:
            projects: List of project dictionaries to filter
            user_preferences: User preferences containing blocking rules

        Returns:
            Filtered list of projects
        """
        return [p for p in projects if not user_preferences.is_blocked(p)]

    def filter_by_rejected(
        self,
        projects: list[dict],
        rejected_ids: set[str] | None,
    ) -> list[dict]:
        """Remove projects that were already rejected by the user.

        Args:
            projects: List of project dictionaries to filter
            rejected_ids: Set of project IDs to exclude

        Returns:
            Filtered list of projects
        """
        if not rejected_ids:
            return projects

        def get_project_id(project: dict) -> str:
            return f"{project.get('owner', '')}/{project.get('name', '')}".lower()

        return [p for p in projects if get_project_id(p) not in rejected_ids]

    def compute_language_match(
        self,
        project: dict,
        user_preferences: "UserPreferences",
    ) -> tuple[bool, str]:
        """Check if project language matches user preferences.

        Args:
            project: Project dictionary with 'language' key
            user_preferences: User preferences with language settings

        Returns:
            Tuple of (is_match, match_type) where match_type is
            'primary', 'secondary', 'learning', or 'none'
        """
        project_lang = project.get("language", "").lower()
        all_languages = user_preferences.get_all_languages()

        if not project_lang:
            return False, "none"

        for lang in user_preferences.get_primary_languages():
            if lang.lower() == project_lang:
                return True, "primary"

        for lang in user_preferences.get_secondary_languages():
            if lang.lower() == project_lang:
                return True, "secondary"

        for lang in user_preferences.get_learning_languages():
            if lang.lower() == project_lang:
                return True, "learning"

        return False, "none"

    def compute_relevance_score(
        self,
        project: dict,
        user_preferences: "UserPreferences",
        base_score: int = 5,
    ) -> int:
        """Compute relevance score for a project.

        Args:
            project: Project dictionary
            user_preferences: User preferences
            base_score: Starting score before adjustments

        Returns:
            Relevance score from 1-10
        """
        score = base_score

        # Language match bonus
        is_match, match_type = self.compute_language_match(project, user_preferences)
        if is_match:
            if match_type == "primary":
                score += 3
            elif match_type == "secondary":
                score += 2
            elif match_type == "learning":
                score += 1

        # Stars bonus (popularity)
        stars = project.get("stars", 0)
        if stars >= 10000:
            score += 2
        elif stars >= 1000:
            score += 1

        # Good first issues bonus
        if project.get("good_first_issue_count", 0) > 0:
            score += 1

        # Clamp to 1-10 range
        return max(1, min(10, score))
