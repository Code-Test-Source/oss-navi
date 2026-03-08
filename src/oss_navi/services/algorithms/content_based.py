"""Content-based filtering algorithm for recommendations."""

import uuid
from typing import TYPE_CHECKING

from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.services.algorithms.base import BaseRecommender

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences


class ContentBasedRecommender(BaseRecommender):
    """Content-based filtering using project attributes and user preferences.

    This algorithm recommends projects based on:
    - Language matching (primary, secondary, learning)
    - Project popularity (stars)
    - Domain/topic matching
    - Good first issue availability

    No ML libraries required - pure Python implementation.
    """

    @property
    def name(self) -> str:
        return "content_based"

    @property
    def mode(self) -> RecommendationMode:
        return RecommendationMode.FAST

    def recommend(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Generate content-based recommendations.

        Args:
            user_preferences: User's language settings and blocking rules
            cached_tasks: List of cached OSS tasks/projects
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations sorted by relevance score
        """
        # Filter out blocked and rejected projects
        candidates = self.filter_by_blocking_rules(cached_tasks, user_preferences)
        candidates = self.filter_by_rejected(candidates, rejected_ids)

        # Score and rank projects
        scored_projects = []
        for project in candidates:
            score_data = self._score_project(project, user_preferences)
            scored_projects.append((project, score_data))

        # Sort by score (descending)
        scored_projects.sort(key=lambda x: x[1]["score"], reverse=True)

        # Generate recommendations
        recommendations = []
        for project, score_data in scored_projects[: self.config.max_recommendations]:
            rec = self._create_recommendation(project, score_data)
            if rec.relevance_score >= self.config.min_score:
                recommendations.append(rec)

        return recommendations

    def _score_project(
        self,
        project: dict,
        user_preferences: "UserPreferences",
    ) -> dict:
        """Score a project based on content features.

        Args:
            project: Project dictionary
            user_preferences: User preferences

        Returns:
            Dictionary with score and reasoning components
        """
        score = 5  # Base score
        reasons = []
        skill_gaps = []

        # Language matching (most important)
        is_match, match_type = self.compute_language_match(project, user_preferences)
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
                skill_gaps.append(project.get("language", ""))
        else:
            # Language doesn't match - lower score
            score -= 2
            reasons.append("different language from your profile")

        # Popularity (stars)
        stars = project.get("stars", 0)
        if stars >= 10000:
            score += 2
            reasons.append("highly popular project")
        elif stars >= 1000:
            score += 1
            reasons.append("popular project")

        # Good first issues
        gfi_count = project.get("good_first_issue_count", 0)
        if gfi_count > 0:
            score += 1
            reasons.append(f"{gfi_count} good first issues available")

        # Skill level matching
        project_lang = project.get("language", "").lower()
        skill_level = user_preferences.get_language_skill(project_lang)
        if skill_level:
            # Check if project difficulty matches skill level
            if skill_level.value == "beginner" and stars >= 1000:
                score += 1
                reasons.append("beginner-friendly")
            elif skill_level.value == "advanced" and stars >= 100:
                score += 1
                reasons.append("challenging project")

        # Domain interest matching
        project_topics = [t.lower() for t in project.get("topics", [])]
        for domain_interest in user_preferences.domain_interests:
            if domain_interest.domain.lower() in project_topics:
                score += 1
                reasons.append(f"matches your interest in {domain_interest.domain}")

        # Clamp score to valid range
        score = max(1, min(10, score))

        return {
            "score": score,
            "reasons": reasons,
            "skill_gaps": skill_gaps,
            "match_type": match_type if is_match else "none",
        }

    def _create_recommendation(
        self,
        project: dict,
        score_data: dict,
    ) -> Recommendation:
        """Create a Recommendation object from project and score data.

        Args:
            project: Project dictionary
            score_data: Score data from _score_project

        Returns:
            Recommendation object
        """
        project_name = f"{project.get('owner', '')}/{project.get('name', '')}"

        # Build reasoning string
        if score_data["reasons"]:
            reasoning = "This project " + ", ".join(score_data["reasons"])
        else:
            reasoning = "General recommendation based on project quality"

        # Generate unique ID
        rec_id = str(uuid.uuid4())[:8]

        return Recommendation(
            recommendation_id=f"rec-{rec_id}",
            project_name=project_name,
            project_url=f"https://github.com/{project_name}",
            language=project.get("language", "Unknown"),
            relevance_score=score_data["score"],
            reasoning=reasoning,
            skill_gap_analysis=score_data["skill_gaps"],
            learning_prerequisites=[],
            issue_url=project.get("issue_url"),
            issue_title=project.get("issue_title"),
            stars=project.get("stars", 0),
            is_great_project=project.get("is_great", False),
            algorithm_source=self.name,
            mode=self.mode,
            confidence_score=score_data["score"] / 10.0,
        )
