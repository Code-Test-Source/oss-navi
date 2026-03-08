"""Learning service for csdiy.wiki, LeetCode, and Codeforces integration."""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from oss_navi.models.learning import (
    Course,
    Difficulty,
    LearningPath,
    LearningResource,
    PracticeProblem,
)
from oss_navi.models.preferences import SkillLevel
from oss_navi.utils.cache import read_json, write_json
from oss_navi.utils.paths import CACHE_DIR

if TYPE_CHECKING:
    from oss_navi.models.preferences import UserPreferences

# Cache files
CSDIY_CACHE = CACHE_DIR / "csdiy.json"
LEETCODE_CACHE = CACHE_DIR / "leetcode.json"
CODEFORCES_CACHE = CACHE_DIR / "codeforces.json"

# Rate limits (seconds between requests)
GITHUB_RATE_LIMIT = 1.0
LEETCODE_RATE_LIMIT = 2.0
CODEFORCES_RATE_LIMIT = 0.2  # 5 requests per second


class LearningService:
    """Service for fetching and caching learning resources.

    Uses third-party datasets as primary data sources to avoid API rate limits.
    API calls are reserved for verification only.
    """

    def __init__(self, cache_dir: Path | None = None):
        """Initialize learning service.

        Args:
            cache_dir: Directory for caching data (default: ~/.oss-navi/cache/)
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ========== csdiy.wiki ==========

    def load_csdiy_courses(self, force: bool = False) -> list[Course]:
        """Load csdiy.wiki courses from cache or scrape.

        Args:
            force: Force re-scrape even if cached

        Returns:
            List of Course objects
        """
        cached = read_json(CSDIY_CACHE)
        if cached and not force:
            return [Course(**c) for c in cached]

        # Scrape csdiy.wiki
        courses = self._scrape_csdiy()

        # Cache the results
        write_json(CSDIY_CACHE, [c.model_dump(mode="json") for c in courses])

        return courses

    def _scrape_csdiy(self) -> list[Course]:
        """Scrape csdiy.wiki for course data.

        Uses rate-limited requests with user agent rotation.
        """
        import uuid

        # For now, return sample courses
        # Full implementation would scrape https://csdiy.wiki/
        sample_courses = [
            Course(
                resource_id=str(uuid.uuid4())[:8],
                title="MIT 6.006 - Introduction to Algorithms",
                url="https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
                source="csdiy",
                topics=["algorithms", "data-structures"],
                difficulty=Difficulty.INTERMEDIATE,
                institution="MIT",
                course_code="6.006",
                prerequisites=[],
            ),
            Course(
                resource_id=str(uuid.uuid4())[:8],
                title="MIT 6.824 - Distributed Systems",
                url="https://pdos.csail.mit.edu/6.824/",
                source="csdiy",
                topics=["distributed-systems", "concurrency"],
                difficulty=Difficulty.ADVANCED,
                institution="MIT",
                course_code="6.824",
                prerequisites=["6.006"],
            ),
            Course(
                resource_id=str(uuid.uuid4())[:8],
                title="CS61A - Structure and Interpretation of Computer Programs",
                url="https://cs61a.org/",
                source="csdiy",
                topics=["programming", "functional-programming"],
                difficulty=Difficulty.BEGINNER,
                institution="UC Berkeley",
                course_code="CS61A",
                prerequisites=[],
            ),
        ]
        return sample_courses

    # ========== LeetCode ==========

    def load_leetcode_problems(self, force: bool = False) -> list[PracticeProblem]:
        """Load LeetCode problems from cache or third-party dataset.

        Primary source: https://github.com/neenza/leetcode-problems

        Args:
            force: Force re-fetch even if cached

        Returns:
            List of PracticeProblem objects
        """
        cached = read_json(LEETCODE_CACHE)
        if cached and not force:
            return [PracticeProblem(**p) for p in cached]

        # Load from third-party dataset
        problems = self._load_leetcode_from_dataset()

        # Cache the results
        write_json(LEETCODE_CACHE, [p.model_dump(mode="json") for p in problems])

        return problems

    def _load_leetcode_from_dataset(self) -> list[PracticeProblem]:
        """Load LeetCode problems from neenza/leetcode-problems dataset.

        This uses a GitHub-hosted dataset, not the LeetCode API.
        """
        import uuid

        # For now, return sample problems
        # Full implementation would load from https://github.com/neenza/leetcode-problems
        sample_problems = [
            PracticeProblem(
                resource_id=str(uuid.uuid4())[:8],
                title="Two Sum",
                url="https://leetcode.com/problems/two-sum/",
                source="leetcode",
                topics=["array", "hash-table"],
                difficulty=Difficulty.BEGINNER,
                problem_id="two-sum",
                acceptance_rate=0.49,
            ),
            PracticeProblem(
                resource_id=str(uuid.uuid4())[:8],
                title="Add Two Numbers",
                url="https://leetcode.com/problems/add-two-numbers/",
                source="leetcode",
                topics=["linked-list", "math"],
                difficulty=Difficulty.INTERMEDIATE,
                problem_id="add-two-numbers",
                acceptance_rate=0.40,
            ),
            PracticeProblem(
                resource_id=str(uuid.uuid4())[:8],
                title="Median of Two Sorted Arrays",
                url="https://leetcode.com/problems/median-of-two-sorted-arrays/",
                source="leetcode",
                topics=["array", "binary-search", "divide-and-conquer"],
                difficulty=Difficulty.ADVANCED,
                problem_id="median-of-two-sorted-arrays",
                acceptance_rate=0.35,
            ),
        ]
        return sample_problems

    # ========== Codeforces ==========

    def load_codeforces_problems(self, force: bool = False) -> list[PracticeProblem]:
        """Load Codeforces problems from cache or third-party dataset.

        Primary sources:
        - Kaggle: lborgav/codeforces-problems
        - HuggingFace: DenCT/codeforces-problems-7k

        Args:
            force: Force re-fetch even if cached

        Returns:
            List of PracticeProblem objects
        """
        cached = read_json(CODEFORCES_CACHE)
        if cached and not force:
            return [PracticeProblem(**p) for p in cached]

        # Load from third-party dataset
        problems = self._load_codeforces_from_dataset()

        # Cache the results
        write_json(CODEFORCES_CACHE, [p.model_dump(mode="json") for p in problems])

        return problems

    def _load_codeforces_from_dataset(self) -> list[PracticeProblem]:
        """Load Codeforces problems from Kaggle/HuggingFace dataset."""
        import uuid

        # For now, return sample problems
        sample_problems = [
            PracticeProblem(
                resource_id=str(uuid.uuid4())[:8],
                title="Watermelon",
                url="https://codeforces.com/problemset/problem/4/A",
                source="codeforces",
                topics=["math"],
                difficulty=Difficulty.BEGINNER,
                problem_id="4A",
                rating=800,
            ),
            PracticeProblem(
                resource_id=str(uuid.uuid4())[:8],
                title="Way Too Long Words",
                url="https://codeforces.com/problemset/problem/71/A",
                source="codeforces",
                topics=["strings"],
                difficulty=Difficulty.BEGINNER,
                problem_id="71A",
                rating=800,
            ),
            PracticeProblem(
                resource_id=str(uuid.uuid4())[:8],
                title="Team",
                url="https://codeforces.com/problemset/problem/231/A",
                source="codeforces",
                topics=["implementation"],
                difficulty=Difficulty.BEGINNER,
                problem_id="231A",
                rating=800,
            ),
        ]
        return sample_problems

    # ========== Automatic Learning Resource Matching ==========

    def get_learning_resources_for_user(
        self,
        user_preferences: "UserPreferences",
        skill_gaps: list[str] | None = None,
    ) -> LearningPath:
        """Get learning resources automatically matched to user's skill level.

        LeetCode/Codeforces problems appear automatically based on skill level.
        Additional resources suggested for skill gaps.

        Args:
            user_preferences: User's preferences with skill levels
            skill_gaps: Optional list of skill gaps to address

        Returns:
            LearningPath with matched resources
        """
        # Load resources
        leetcode_problems = self.load_leetcode_problems()
        codeforces_problems = self.load_codeforces_problems()
        courses = self.load_csdiy_courses()

        # Determine difficulty based on skill level
        primary_languages = user_preferences.get_primary_languages()
        skill_level = SkillLevel.INTERMEDIATE
        for lp in user_preferences.languages:
            if lp.language in primary_languages:
                skill_level = lp.skill_level
                break

        # Map skill level to difficulty
        if skill_level == SkillLevel.BEGINNER:
            target_difficulties = [Difficulty.BEGINNER]
        elif skill_level == SkillLevel.ADVANCED:
            target_difficulties = [Difficulty.INTERMEDIATE, Difficulty.ADVANCED]
        else:
            target_difficulties = [Difficulty.BEGINNER, Difficulty.INTERMEDIATE]

        # Filter problems by difficulty
        matched_problems: list[PracticeProblem] = []
        for prob in leetcode_problems + codeforces_problems:
            if prob.difficulty in target_difficulties:
                matched_problems.append(prob)

        # Filter courses by difficulty
        matched_courses = [
            c for c in courses
            if c.difficulty in target_difficulties
        ]

        # If skill gaps provided, prioritize matching resources
        if skill_gaps:
            skill_lower = [s.lower() for s in skill_gaps]
            matched_problems = [
                p for p in matched_problems
                if any(t.lower() in skill_lower for t in p.topics)
            ][:10]
            matched_courses = [
                c for c in matched_courses
                if any(t.lower() in skill_lower for t in c.topics)
            ][:5]

        # Build learning path
        resources: list[LearningResource] = []
        resources.extend(matched_courses[:3])
        resources.extend(matched_problems[:10])

        return LearningPath(
            title="Recommended Learning Resources",
            description="Automatically suggested based on your skill level",
            target_skills=skill_gaps or [lp.language for lp in user_preferences.languages],
            resources=resources,
        )

    def get_practice_problems_for_skill(
        self,
        skill: str,
        difficulty: Difficulty = Difficulty.INTERMEDIATE,
        limit: int = 5,
    ) -> list[PracticeProblem]:
        """Get practice problems for a specific skill/topic.

        Args:
            skill: Skill or topic to practice
            difficulty: Target difficulty
            limit: Maximum number of problems

        Returns:
            List of matching PracticeProblem objects
        """
        leetcode_problems = self.load_leetcode_problems()
        codeforces_problems = self.load_codeforces_problems()

        skill_lower = skill.lower()
        all_problems = leetcode_problems + codeforces_problems

        # Filter by topic and difficulty
        matched = [
            p for p in all_problems
            if p.difficulty == difficulty
            and any(skill_lower in t.lower() for t in p.topics)
        ]

        return matched[:limit]


# Rate-limited API verification (for when explicitly requested)
async def verify_leetcode_problem(problem_id: str) -> dict | None:
    """Verify a specific LeetCode problem via API.

    Rate-limited to 1 request per 2 seconds.
    Only use for verification after user selects a recommendation.

    Args:
        problem_id: LeetCode problem slug

    Returns:
        Problem data or None if not found
    """
    await asyncio.sleep(LEETCODE_RATE_LIMIT)

    try:
        async with httpx.AsyncClient():
            # This would call the LeetCode GraphQL API
            # For now, return None to indicate no verification
            return None
    except Exception:
        return None


async def verify_codeforces_problem(problem_id: str) -> dict | None:
    """Verify a specific Codeforces problem via API.

    Rate-limited to 5 requests per second.
    Only use for verification after user selects a recommendation.

    Args:
        problem_id: Codeforces problem ID

    Returns:
        Problem data or None if not found
    """
    await asyncio.sleep(CODEFORCES_RATE_LIMIT)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://codeforces.com/api/problemset.problems",
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    # Search for problem
                    for prob in data.get("result", {}).get("problems", []):
                        if str(prob.get("contestId")) + prob.get("index") == problem_id:
                            return prob
            return None
    except Exception:
        return None
