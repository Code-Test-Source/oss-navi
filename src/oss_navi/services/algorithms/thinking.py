"""Thinking mode recommender using LightFM hybrid model and Apriori patterns."""

from typing import TYPE_CHECKING

from oss_navi.models.recommendation import Recommendation, RecommendationMode
from oss_navi.services.algorithms.apriori import AprioriMiner
from oss_navi.services.algorithms.base import BaseRecommender, RecommenderConfig
from oss_navi.services.algorithms.content_based import ContentBasedRecommender

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences


class ThinkingRecommender(BaseRecommender):
    """Thinking mode using LightFM hybrid + Apriori pattern mining.

    Characteristics:
    - Time: <180 seconds
    - Memory: <500MB
    - Requires: numpy, lightfm-next
    - Highest recommendation quality

    Combines:
    1. Content-based filtering (project attributes)
    2. Pattern mining (skill associations with Apriori)
    3. LightFM hybrid model (collaborative + content filtering)
    """

    def __init__(self, config: RecommenderConfig | None = None):
        """Initialize the thinking recommender.

        Args:
            config: Optional configuration for the recommender
        """
        super().__init__(config)
        self._content_based = ContentBasedRecommender(config)
        self._apriori = AprioriMiner(min_support=0.05, min_confidence=0.3)
        self._lightfm_available = self._check_lightfm()
        self._lightfm_model = None

    def _check_lightfm(self) -> bool:
        """Check if LightFM library is available."""
        try:
            from lightfm import LightFM  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "thinking"

    @property
    def mode(self) -> RecommendationMode:
        return RecommendationMode.THINKING

    def recommend(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Generate recommendations using hybrid approach.

        Combines multiple recommendation strategies:
        1. Content-based filtering
        2. Pattern-based recommendations (Apriori)
        3. LightFM hybrid model (if available)

        Args:
            user_preferences: User's language settings and blocking rules
            cached_tasks: List of cached OSS tasks/projects
            rejected_ids: Set of project IDs already rejected by user

        Returns:
            List of recommendations sorted by relevance score
        """
        # Get base content-based recommendations
        content_recs = self._content_based.recommend(
            user_preferences, cached_tasks, rejected_ids
        )

        # Enhance with pattern mining
        pattern_recs = self._get_pattern_recommendations(
            user_preferences, cached_tasks, rejected_ids
        )

        # Combine and deduplicate
        all_recs = self._combine_recommendations(content_recs, pattern_recs)

        # Apply LightFM enhancement if available
        if self._lightfm_available:
            all_recs = self._enhance_with_lightfm(
                all_recs, user_preferences, cached_tasks
            )

        # Sort by score and limit
        all_recs.sort(key=lambda r: r.relevance_score, reverse=True)
        return all_recs[: self.config.max_recommendations]

    def _get_pattern_recommendations(
        self,
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
        rejected_ids: set[str] | None = None,
    ) -> list[Recommendation]:
        """Get recommendations based on mined patterns.

        Uses Apriori to find skill-project associations.

        Args:
            user_preferences: User's language settings
            cached_tasks: Cached tasks
            rejected_ids: Rejected project IDs

        Returns:
            List of pattern-based recommendations
        """
        # Build transactions from cached tasks
        transactions = self._build_transactions(cached_tasks)

        # Mine patterns (stored in apriori for later use)
        self._apriori.mine_patterns(transactions)

        # Get user skills
        user_skills = user_preferences.get_all_languages()

        # Get pattern-based recommendations
        pattern_suggestions = self._apriori.get_recommendations_for_skills(
            user_skills, top_n=10
        )

        # Convert to recommendations
        recommendations = []
        for suggested_items, confidence in pattern_suggestions:
            # Find projects matching suggested items
            for item in suggested_items:
                matching_projects = self._find_projects_by_tech(
                    item, cached_tasks, user_preferences, rejected_ids
                )
                for project in matching_projects[:2]:  # Limit per suggestion
                    rec = self._create_pattern_recommendation(
                        project, item, confidence, user_skills
                    )
                    recommendations.append(rec)

        return recommendations

    def _build_transactions(self, cached_tasks: list[dict]) -> list[set[str]]:
        """Build transaction database from cached tasks.

        Each transaction represents a project with its associated skills/topics.

        Args:
            cached_tasks: List of cached tasks

        Returns:
            List of transactions (sets of items)
        """
        transactions = []

        for task in cached_tasks:
            items = set()
            repo = task.get("repository", task)

            # Add language
            lang = repo.get("language")
            if lang:
                items.add(lang.lower())

            # Add topics
            for topic in repo.get("topics") or []:
                items.add(topic.lower())

            # Add project name as item
            project_name = repo.get("name", f"{repo.get('owner', '')}/{repo.get('name', '')}")
            items.add(f"project:{project_name}")

            transactions.append(items)

        return transactions

    def _find_projects_by_tech(
        self,
        tech: str,
        cached_tasks: list[dict],
        user_preferences: "UserPreferences",
        rejected_ids: set[str] | None = None,
    ) -> list[dict]:
        """Find projects using a specific technology.

        Args:
            tech: Technology to search for
            cached_tasks: Cached tasks
            user_preferences: User preferences
            rejected_ids: Rejected project IDs

        Returns:
            List of matching projects
        """
        matches = []
        tech_lower = tech.lower()

        for task in cached_tasks:
            repo = task.get("repository", task)

            # Check language
            lang = repo.get("language") or ""
            if lang.lower() == tech_lower:
                matches.append(task)
                continue

            # Check topics
            topics = [t.lower() for t in repo.get("topics") or []]
            if tech_lower in topics:
                matches.append(task)

        # Filter by blocking rules
        matches = [
            m for m in matches
            if not user_preferences.is_blocked(m)
        ]

        # Filter by rejected
        if rejected_ids:
            matches = [
                m for m in matches
                if (m.get("repository", m).get("name", "")).lower()
                not in rejected_ids
            ]

        # Sort by stars
        matches.sort(key=lambda t: t.get("repository", t).get("stars") or 0, reverse=True)

        return matches[:5]  # Limit results

    def _create_pattern_recommendation(
        self,
        project: dict,
        suggested_tech: str,
        confidence: float,
        user_skills: list[str],
    ) -> Recommendation:
        """Create a recommendation from pattern mining.

        Args:
            project: Project dictionary (may have nested 'repository' key)
            suggested_tech: Technology suggested by pattern
            confidence: Pattern confidence
            user_skills: User's current skills

        Returns:
            Recommendation object
        """
        import uuid

        repo = project.get("repository", project)
        project_name = repo.get("name", f"{repo.get('owner', '')}/{repo.get('name', '')}")

        return Recommendation(
            recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
            project_name=project_name,
            project_url=repo.get("url", f"https://github.com/{project_name}"),
            language=repo.get("language") or "Unknown",
            relevance_score=min(10, int(confidence * 15)),  # Scale confidence to score
            reasoning=f"Recommended based on pattern: users with {', '.join(user_skills)} "
            f"often contribute to {suggested_tech} projects",
            skill_gap_analysis=[suggested_tech],
            learning_prerequisites=[],
            issue_url=project.get("url"),
            issue_title=project.get("title"),
            stars=repo.get("stars") or 0,
            is_great_project=project.get("is_great", False),
            algorithm_source="apriori_pattern",
            mode=self.mode,
            confidence_score=confidence,
        )

    def _combine_recommendations(
        self,
        content_recs: list[Recommendation],
        pattern_recs: list[Recommendation],
    ) -> list[Recommendation]:
        """Combine content-based and pattern-based recommendations.

        Deduplicates by project name, keeping higher score.

        Args:
            content_recs: Content-based recommendations
            pattern_recs: Pattern-based recommendations

        Returns:
            Combined and deduplicated recommendations
        """
        # Index by project name
        seen = {}

        for rec in content_recs + pattern_recs:
            key = rec.project_name.lower()
            if key not in seen or rec.relevance_score > seen[key].relevance_score:
                seen[key] = rec

        return list(seen.values())

    def _enhance_with_lightfm(
        self,
        recommendations: list[Recommendation],
        user_preferences: "UserPreferences",
        cached_tasks: list[dict],
    ) -> list[Recommendation]:
        """Enhance recommendations using LightFM model.

        Uses LightFM for hybrid collaborative + content-based filtering.

        Args:
            recommendations: Current recommendations
            user_preferences: User preferences
            cached_tasks: Cached tasks

        Returns:
            Enhanced recommendations
        """
        try:
            import numpy as np
            import scipy.sparse as sp
            from lightfm import LightFM
            from lightfm.data import Dataset
        except ImportError:
            return recommendations

        if not recommendations:
            return recommendations

        # Build user feature vector
        user_features = self._build_user_features(user_preferences)

        # Create LightFM dataset
        dataset = Dataset()
        all_languages = set()
        all_topics = set()

        for task in cached_tasks:
            repo = task.get("repository", task)
            lang = repo.get("language")
            if lang:
                all_languages.add(lang.lower())
            for topic in repo.get("topics") or []:
                all_topics.add(topic.lower())

        # Build item names
        item_names = []
        for task in cached_tasks:
            repo = task.get("repository", task)
            name = repo.get("name", f"{repo.get('owner', '')}/{repo.get('name', '')}")
            item_names.append(name)

        # Fit dataset
        dataset.fit(
            users=[0],  # Single user
            items=item_names,
            user_features=list(user_features.keys()),
            item_features=list(all_languages | all_topics),
        )

        # Build feature matrices
        user_features_matrix = dataset.build_user_features(
            [(0, user_features)], normalize=True
        )

        item_features_list = []
        for task in cached_tasks:
            repo = task.get("repository", task)
            name = repo.get("name", f"{repo.get('owner', '')}/{repo.get('name', '')}")
            features = set()
            lang = repo.get("language")
            if lang:
                features.add(lang.lower())
            for topic in repo.get("topics") or []:
                features.add(topic.lower())
            item_features_list.append((name, features))

        item_features_matrix = dataset.build_item_features(
            item_features_list, normalize=True
        )

        # Create or reuse model
        if self._lightfm_model is None:
            self._lightfm_model = LightFM(
                no_components=30,
                learning_rate=0.05,
                loss="warp",  # Weighted Approximate-Rank Pairwise
            )
            # Build a minimal implicit-feedback interactions matrix (1 user × N items)
            # so LightFM can initialise its latent factors from item features alone.
            num_items = len(item_names)
            interactions_matrix = sp.csr_matrix(
                np.zeros((1, num_items), dtype=np.float32)
            )
            self._lightfm_model.fit_partial(
                interactions=interactions_matrix,
                user_features=user_features_matrix,
                item_features=item_features_matrix,
                epochs=10,
                verbose=False,
            )

        # Predict scores for recommendations
        name_to_idx = {name: i for i, name in enumerate(item_names)}

        for rec in recommendations:
            if rec.project_name in name_to_idx:
                item_idx = name_to_idx[rec.project_name]
                try:
                    score = self._lightfm_model.predict(
                        0, np.array([item_idx]),
                        user_features=user_features_matrix,
                        item_features=item_features_matrix,
                    )[0]

                    # Normalize LightFM score to 0-10 range
                    normalized_score = max(1, min(10, int((score + 1) * 5)))

                    # Blend with original score
                    blended = int(rec.relevance_score * 0.5 + normalized_score * 0.5)
                    rec.relevance_score = max(1, min(10, blended))

                    # Update algorithm source
                    rec.algorithm_source = "lightfm_hybrid"

                except Exception:
                    pass

        return recommendations

    def _build_user_features(self, user_preferences: "UserPreferences") -> dict:
        """Build feature vector for user.

        Args:
            user_preferences: User preferences

        Returns:
            User feature dictionary
        """
        features = {}

        # Add language features
        for lang in user_preferences.get_all_languages():
            features[lang.lower()] = 1.0

        # Add domain features
        for domain in user_preferences.domain_interests:
            features[domain.domain.lower()] = domain.interest_level / 10.0

        # Add skill level features
        for lp in user_preferences.languages:
            level_map = {"beginner": 0.3, "intermediate": 0.6, "advanced": 1.0}
            skill_feature = f"skill_{lp.language.lower()}"
            features[skill_feature] = level_map.get(lp.skill_level.value, 0.5)

        return features


def create_lightfm_model():
    """Create and return a LightFM model if available.

    Returns:
        Tuple of (model, is_available)
    """
    try:
        from lightfm import LightFM

        return LightFM(
            no_components=30,
            learning_rate=0.05,
            loss="warp",  # Weighted Approximate-Rank Pairwise
        ), True
    except ImportError:
        return None, False
