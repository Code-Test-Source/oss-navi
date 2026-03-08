"""Tests for learning service."""

from pathlib import Path
from unittest.mock import patch

import pytest

from oss_navi.models.learning import Difficulty, LearningPath, PracticeProblem
from oss_navi.models.preferences import LanguageProfile, LanguageType, SkillLevel, UserPreferences
from oss_navi.services.learning import LearningService


class TestLearningService:
    """Tests for LearningService."""

    @pytest.fixture
    def learning_service(self, tmp_path: Path) -> LearningService:
        """Create a LearningService with temp cache directory."""
        return LearningService(cache_dir=tmp_path)

    @pytest.fixture
    def user_prefs(self) -> UserPreferences:
        """Create test user preferences."""
        return UserPreferences(
            languages=[
                LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.BEGINNER),
            ],
        )

    def test_load_csdiy_courses(self, learning_service: LearningService) -> None:
        """Test load_csdiy_courses method."""
        courses = learning_service.load_csdiy_courses()
        assert len(courses) > 0
        assert all(c.source == "csdiy" for c in courses)

    def test_load_csdiy_courses_from_cache(
        self, learning_service: LearningService
    ) -> None:
        """Test loading csdiy courses from cache."""
        # First call creates cache
        courses1 = learning_service.load_csdiy_courses()

        # Second call should use cache
        with patch.object(
            learning_service, "_scrape_csdiy", wraps=learning_service._scrape_csdiy
        ) as mock_scrape:
            courses2 = learning_service.load_csdiy_courses()
            mock_scrape.assert_not_called()
            assert len(courses2) == len(courses1)

    def test_load_leetcode_problems(self, learning_service: LearningService) -> None:
        """Test load_leetcode_problems method."""
        problems = learning_service.load_leetcode_problems()
        assert len(problems) > 0
        assert all(p.source == "leetcode" for p in problems)

    def test_load_codeforces_problems(self, learning_service: LearningService) -> None:
        """Test load_codeforces_problems method."""
        problems = learning_service.load_codeforces_problems()
        assert len(problems) > 0
        assert all(p.source == "codeforces" for p in problems)

    def test_get_learning_resources_for_user(
        self, learning_service: LearningService, user_prefs: UserPreferences
    ) -> None:
        """Test get_learning_resources_for_user method."""
        path = learning_service.get_learning_resources_for_user(user_prefs)
        assert isinstance(path, LearningPath)
        assert len(path.resources) > 0
        assert "python" in path.target_skills

    def test_get_learning_resources_with_skill_gaps(
        self, learning_service: LearningService, user_prefs: UserPreferences
    ) -> None:
        """Test get_learning_resources_for_user with skill gaps."""
        skill_gaps = ["algorithms", "data-structures"]
        path = learning_service.get_learning_resources_for_user(
            user_prefs, skill_gaps=skill_gaps
        )
        assert path.title == "Recommended Learning Resources"

    def test_get_practice_problems_for_skill(
        self, learning_service: LearningService
    ) -> None:
        """Test get_practice_problems_for_skill method."""
        problems = learning_service.get_practice_problems_for_skill(
            skill="array",
            difficulty=Difficulty.BEGINNER,
            limit=3,
        )
        assert len(problems) <= 3
        assert all(isinstance(p, PracticeProblem) for p in problems)

    def test_get_practice_problems_advanced(
        self, learning_service: LearningService
    ) -> None:
        """Test get_practice_problems_for_skill with advanced difficulty."""
        problems = learning_service.get_practice_problems_for_skill(
            skill="math",
            difficulty=Difficulty.ADVANCED,
            limit=5,
        )
        assert all(p.difficulty == Difficulty.ADVANCED for p in problems)

    def test_resources_match_user_skill_level(
        self, learning_service: LearningService
    ) -> None:
        """Test that resources match user's skill level."""
        # Beginner user
        beginner_prefs = UserPreferences(
            languages=[LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.BEGINNER)],
        )
        path = learning_service.get_learning_resources_for_user(beginner_prefs)
        beginner_problems = [
            r for r in path.resources
            if hasattr(r, "difficulty") and r.difficulty == Difficulty.BEGINNER
        ]
        # Should have beginner problems
        assert len(beginner_problems) > 0

        # Advanced user
        advanced_prefs = UserPreferences(
            languages=[LanguageProfile(language="python", type=LanguageType.PRIMARY, skill_level=SkillLevel.ADVANCED)],
        )
        path = learning_service.get_learning_resources_for_user(advanced_prefs)
        # Should include intermediate/advanced resources
        difficulties = {r.difficulty for r in path.resources if hasattr(r, "difficulty")}
        assert Difficulty.INTERMEDIATE in difficulties or Difficulty.ADVANCED in difficulties

    def test_force_reload(self, learning_service: LearningService) -> None:
        """Test force reload of cached data."""
        # Load once
        learning_service.load_csdiy_courses()

        # Force reload should re-scrape
        with patch.object(
            learning_service, "_scrape_csdiy", wraps=learning_service._scrape_csdiy
        ) as mock_scrape:
            learning_service.load_csdiy_courses(force=True)
            mock_scrape.assert_called_once()
