"""Main recommendation orchestration service."""

from typing import TYPE_CHECKING

from oss_navi.models.preferences import UserPreferences
from oss_navi.models.recommendation import (
    ModeConfig,
    Recommendation,
    RecommendationMode,
    check_mode_availability,
    get_mode_config,
)
from oss_navi.services.algorithms.base import RecommenderConfig
from oss_navi.services.algorithms.fast import FastRecommender
from oss_navi.services.algorithms.normal import NormalRecommender
from oss_navi.services.algorithms.thinking import ThinkingRecommender

if TYPE_CHECKING:
    pass


class RecommenderService:
    """Main service for generating intelligent project recommendations.

    Handles:
    - Mode-based algorithm selection
    - Two-round language matching
    - Relevance score computation
    - Skill gap analysis
    """

    def __init__(
        self,
        mode: RecommendationMode = RecommendationMode.NORMAL,
        config: RecommenderConfig | None = None,
    ):
        """Initialize the recommender service.

        Args:
            mode: Recommendation mode (fast, normal, thinking)
            config: Optional recommender configuration
        """
        self.mode = self._validate_mode(mode)
        self.config = config or RecommenderConfig()
        self._recommender = self._create_recommender()

    def _validate_mode(self, mode: RecommendationMode) -> RecommendationMode:
        """Validate and potentially downgrade mode if dependencies missing.

        Args:
            mode: Requested recommendation mode

        Returns:
            Valid mode (may be downgraded if dependencies unavailable)
        """
        is_available, missing = check_mode_availability(mode)

        if is_available:
            return mode

        # Downgrade mode based on missing dependencies
        if mode == RecommendationMode.THINKING:
            # Try normal mode
            is_normal_available, _ = check_mode_availability(RecommendationMode.NORMAL)
            if is_normal_available:
                return RecommendationMode.NORMAL
            # Fall back to fast mode (always available)
            return RecommendationMode.FAST

        if mode == RecommendationMode.NORMAL:
            # Fall back to fast mode
            return RecommendationMode.FAST

        return mode

    def _create_recommender(self):
        """Create the appropriate recommender for current mode."""
        if self.mode == RecommendationMode.FAST:
            return FastRecommender(self.config)
        elif self.mode == RecommendationMode.NORMAL:
            return NormalRecommender(self.config)
        elif self.mode == RecommendationMode.THINKING:
            return ThinkingRecommender(self.config)
        else:
            return FastRecommender(self.config)

    def get_mode_config(self) -> ModeConfig:
        """Get configuration for current mode."""
        return get_mode_config(self.mode)

    def recommend(
        self,
        user_preferences: UserPreferences,
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Generate recommendations based on user preferences.

        Implements two-round language matching:
        1. Round 1: Find projects matching user's languages
        2. Round 2: If no matches, find adjacent technology projects

        Args:
            user_preferences: User's language settings and blocking rules
            cached_tasks: List of cached OSS tasks/projects
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations sorted by relevance score
        """
        # Filter tasks by blocking rules first
        filtered_tasks = [
            t for t in cached_tasks
            if not user_preferences.is_blocked(t)
        ]

        # Generate recommendations
        recommendations = self._recommender.recommend(
            user_preferences, filtered_tasks, rejected_ids
        )

        # Add skill gap analysis
        for rec in recommendations:
            rec.skill_gap_analysis = self._compute_skill_gaps(
                rec, user_preferences
            )

        return recommendations

    def _compute_skill_gaps(
        self,
        recommendation: Recommendation,
        user_preferences: UserPreferences,
    ) -> list[str]:
        """Compute skill gaps for a recommendation.

        Identifies skills the user will develop by contributing to this project.

        Args:
            recommendation: The recommendation
            user_preferences: User's current skills

        Returns:
            List of skills the user will develop
        """
        skill_gaps = []

        # Get user's languages
        user_languages = {lang.lower() for lang in user_preferences.get_all_languages()}

        # Language skill gap
        rec_language = recommendation.language.lower()
        if rec_language not in user_languages:
            skill_gaps.append(f"Learn {recommendation.language}")

        # Check for skill level gap
        user_skill = user_preferences.get_language_skill(recommendation.language)
        if user_skill:
            if user_skill.value == "beginner":
                skill_gaps.append("Build foundational skills")
            elif user_skill.value == "intermediate":
                skill_gaps.append("Advance to expert-level patterns")

        # Add domain-specific skills based on project topics
        # This would be enhanced with actual topic data
        if recommendation.is_great_project:
            skill_gaps.append("Contribute to a high-impact project")

        return skill_gaps

    def compute_relevance_score(
        self,
        project: dict,
        user_preferences: UserPreferences,
    ) -> tuple[int, str]:
        """Compute relevance score and reasoning for a project.

        Args:
            project: Project dictionary
            user_preferences: User preferences

        Returns:
            Tuple of (score, reasoning)
        """
        score = 5  # Base score
        reasons = []

        # Language match
        is_match, match_type = self._compute_language_match(project, user_preferences)
        if is_match:
            if match_type == "primary":
                score += 3
                reasons.append("matches your primary language")
            elif match_type == "secondary":
                score += 2
                reasons.append("matches a secondary language")
            elif match_type == "learning":
                score += 1
                reasons.append("good for learning")

        # Stars/popularity
        stars = project.get("stars", 0)
        if stars >= 10000:
            score += 2
            reasons.append("highly popular")
        elif stars >= 1000:
            score += 1
            reasons.append("popular project")

        # Good first issues
        if project.get("good_first_issue_count", 0) > 0:
            score += 1
            reasons.append("has good first issues")

        # Clamp score
        score = max(1, min(10, score))

        # Build reasoning string
        reasoning = "This project " + ", ".join(reasons) if reasons else "General recommendation"

        return score, reasoning

    def _compute_language_match(
        self,
        project: dict,
        user_preferences: UserPreferences,
    ) -> tuple[bool, str]:
        """Compute language match for a project.

        Args:
            project: Project dictionary
            user_preferences: User preferences

        Returns:
            Tuple of (is_match, match_type)
        """
        project_lang = project.get("language", "").lower()

        if not project_lang:
            return False, "none"

        # Check primary languages
        for lang in user_preferences.get_primary_languages():
            if lang.lower() == project_lang:
                return True, "primary"

        # Check secondary languages
        for lang in user_preferences.get_secondary_languages():
            if lang.lower() == project_lang:
                return True, "secondary"

        # Check learning languages
        for lang in user_preferences.get_learning_languages():
            if lang.lower() == project_lang:
                return True, "learning"

        return False, "none"


def create_recommender_service(
    mode: str = "normal",
    max_recommendations: int = 10,
) -> RecommenderService:
    """Factory function to create a recommender service.

    Args:
        mode: Recommendation mode ("fast", "normal", "thinking")
        max_recommendations: Maximum number of recommendations

    Returns:
        Configured RecommenderService instance
    """
    # Map string to enum
    mode_map = {
        "fast": RecommendationMode.FAST,
        "normal": RecommendationMode.NORMAL,
        "thinking": RecommendationMode.THINKING,
    }

    rec_mode = mode_map.get(mode.lower(), RecommendationMode.NORMAL)
    config = RecommenderConfig(max_recommendations=max_recommendations)

    return RecommenderService(mode=rec_mode, config=config)
