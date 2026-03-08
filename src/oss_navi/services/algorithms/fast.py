"""Fast mode recommender using content-based filtering only."""

from typing import TYPE_CHECKING

from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.services.algorithms.base import BaseRecommender, RecommenderConfig
from oss_navi.services.algorithms.content_based import ContentBasedRecommender

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences


class FastRecommender(BaseRecommender):
    """Fast recommendation mode using only content-based filtering.

    Characteristics:
    - Time: <30 seconds
    - Memory: <50MB
    - No external ML dependencies
    - Suitable for quick exploration and CI/CD

    Uses pure content-based matching on:
    - Language preferences
    - Project popularity
    - Topic/domain matching
    - Good first issue availability
    """

    def __init__(self, config: RecommenderConfig | None = None):
        """Initialize the fast recommender.

        Args:
            config: Optional configuration for the recommender
        """
        super().__init__(config)
        self._content_based = ContentBasedRecommender(config)

    @property
    def name(self) -> str:
        return "fast"

    @property
    def mode(self) -> RecommendationMode:
        return RecommendationMode.FAST

    def recommend(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Generate fast recommendations using content-based filtering.

        This implements the two-round language matching:
        1. First round: Find projects matching user's languages
        2. Second round: If no matches, find adjacent technology projects

        Args:
            user_preferences: User's language settings and blocking rules
            cached_tasks: List of cached OSS tasks/projects
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations sorted by relevance score
        """
        all_recommendations = []

        # Round 1: Language matching
        language_recs = self._round_one_language_match(
            user_preferences, cached_tasks, rejected_ids
        )
        all_recommendations.extend(language_recs)

        # Round 2: If no language matches, find adjacent projects
        if not language_recs:
            adjacent_recs = self._round_two_adjacent(
                user_preferences, cached_tasks, rejected_ids
            )
            all_recommendations.extend(adjacent_recs)

        # Sort by score and limit
        all_recommendations.sort(key=lambda r: r.relevance_score, reverse=True)
        return all_recommendations[: self.config.max_recommendations]

    def _round_one_language_match(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """First round: Find projects matching user's languages.

        Args:
            user_preferences: User's language settings
            cached_tasks: List of cached tasks
            rejected_ids: Set of rejected project IDs

        Returns:
            List of language-matched recommendations
        """
        # Get user's languages (primary first, then secondary, then learning)
        languages = (
            user_preferences.get_primary_languages()
            + user_preferences.get_secondary_languages()
            + user_preferences.get_learning_languages()
        )

        if not languages:
            # No languages specified, use all candidates
            return self._content_based.recommend(
                user_preferences, cached_tasks, rejected_ids
            )

        # Filter projects by language
        language_tasks = []
        for task in cached_tasks:
            repo = task.get("repository", task)
            task_lang = (repo.get("language") or "").lower()
            if any(lang.lower() == task_lang for lang in languages):
                language_tasks.append(task)

        if not language_tasks:
            return []

        # Generate recommendations for language-matched projects
        return self._content_based.recommend(
            user_preferences, language_tasks, rejected_ids
        )

    def _round_two_adjacent(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Second round: Find adjacent technology projects.

        This is called when no language matches exist. It recommends
        projects in related/adjacent technologies and marks the
        user's languages as learning prerequisites.

        Args:
            user_preferences: User's language settings
            cached_tasks: List of cached tasks
            rejected_ids: Set of rejected project IDs

        Returns:
            List of adjacent project recommendations with prerequisites
        """
        # Get all user's languages as prerequisites
        user_languages = user_preferences.get_all_languages()

        # Map of language adjacencies (languages that share concepts)
        adjacent_map = {
            "python": ["go", "rust", "java"],
            "javascript": ["typescript", "node", "deno"],
            "typescript": ["javascript", "node"],
            "go": ["rust", "python", "c"],
            "rust": ["c", "cpp", "go"],
            "java": ["kotlin", "scala", "python"],
            "c": ["cpp", "rust", "go"],
            "cpp": ["c", "rust"],
            "ruby": ["python", "php"],
            "php": ["python", "ruby"],
        }

        # Find adjacent languages for user's languages
        adjacent_languages = set()
        for lang in user_languages:
            lang_lower = lang.lower()
            if lang_lower in adjacent_map:
                adjacent_languages.update(adjacent_map[lang_lower])

        # Remove user's own languages from adjacent
        user_langs_lower = {lang.lower() for lang in user_languages}
        adjacent_languages -= user_langs_lower

        if not adjacent_languages:
            # No adjacent languages found, recommend popular projects
            return self._recommend_popular(user_preferences, cached_tasks, rejected_ids)

        # Filter projects by adjacent languages
        adjacent_tasks = []
        for task in cached_tasks:
            task_lang = (task.get("repository", task).get("language") or "").lower()
            if task_lang in adjacent_languages:
                adjacent_tasks.append(task)

        if not adjacent_tasks:
            return self._recommend_popular(user_preferences, cached_tasks, rejected_ids)

        # Generate recommendations with learning prerequisites
        recommendations = self._content_based.recommend(
            user_preferences, adjacent_tasks, rejected_ids
        )

        # Add learning prerequisites to each recommendation
        for rec in recommendations:
            rec.learning_prerequisites = user_languages.copy()
            rec.reasoning = (
                f"No projects found for your languages. {rec.reasoning}"
            )

        return recommendations

    def _recommend_popular(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Recommend popular beginner-friendly projects.

        Fallback when no language or adjacent matches exist.

        Args:
            user_preferences: User's language settings
            cached_tasks: List of cached tasks
            rejected_ids: Set of rejected project IDs

        Returns:
            List of popular project recommendations
        """
        # Filter by blocking rules and rejected
        candidates = self._content_based.filter_by_blocking_rules(
            cached_tasks, user_preferences
        )
        candidates = self._content_based.filter_by_rejected(candidates, rejected_ids)

        # Sort by stars (popularity)
        candidates.sort(key=lambda t: t.get("repository", t).get("stars", 0), reverse=True)

        # Take top projects with good first issues
        popular = [
            t for t in candidates[:50]
            if t.get("good_first_issue_count", 0) > 0
        ][: self.config.max_recommendations]

        # Generate recommendations
        recommendations = []
        user_languages = user_preferences.get_all_languages()

        for project in popular:
            rec = self._content_based._create_recommendation(
                project,
                {
                    "score": 6,
                    "reasons": ["popular beginner-friendly project"],
                    "skill_gaps": [],
                    "match_type": "none",
                },
            )
            rec.learning_prerequisites = user_languages.copy()
            rec.reasoning = (
                "No matches for your languages. Popular project recommended."
            )
            recommendations.append(rec)

        return recommendations
