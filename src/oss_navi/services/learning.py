"""Learning service for csdiy.wiki, LeetCode, and Codeforces integration."""

import asyncio
import re
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
from oss_navi.utils.scraping import Scraper, ScrapingConfig

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

# Data source URLs
CSDIY_SITEMAP_URL = "https://csdiy.wiki/sitemap.xml"
LEETCODE_API_URL = "https://leetcode.com/api/problems/algorithms/"
CODEFORCES_API_URL = "https://codeforces.com/api/problemset.problems"


def _parse_difficulty(diff_str: str | None) -> Difficulty:
    """Parse difficulty string to Difficulty enum."""
    if not diff_str:
        return Difficulty.INTERMEDIATE
    diff_lower = diff_str.lower()
    if diff_lower in ("easy", "beginner", "basic"):
        return Difficulty.BEGINNER
    if diff_lower in ("hard", "advanced", "expert"):
        return Difficulty.ADVANCED
    return Difficulty.INTERMEDIATE


def _parse_codeforces_rating(rating: int | None) -> Difficulty:
    """Parse Codeforces rating to Difficulty enum."""
    if rating is None:
        return Difficulty.INTERMEDIATE
    if rating <= 1200:
        return Difficulty.BEGINNER
    if rating >= 1800:
        return Difficulty.ADVANCED
    return Difficulty.INTERMEDIATE


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
        self._scraper = Scraper(ScrapingConfig(rate_limit=GITHUB_RATE_LIMIT))

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
        if courses:
            write_json(CSDIY_CACHE, [c.model_dump(mode="json") for c in courses])

        return courses

    def _scrape_csdiy(self) -> list[Course]:
        """Scrape csdiy.wiki for course data.

        Parses the sitemap to find course pages.
        """
        courses: list[Course] = []

        try:
            # Fetch the sitemap
            content = self._scraper.fetch_text(CSDIY_SITEMAP_URL)
            if not content:
                return self._get_fallback_csdiy_courses()

            # Parse the sitemap to extract course URLs
            courses = self._parse_csdiy_sitemap(content)

            if not courses:
                return self._get_fallback_csdiy_courses()

            return courses

        except Exception:
            return self._get_fallback_csdiy_courses()

    def _parse_csdiy_sitemap(self, content: str) -> list[Course]:
        """Parse csdiy sitemap XML to extract courses."""
        courses: list[Course] = []

        # Extract URLs from sitemap
        urls = re.findall(r'<loc>([^<]+)</loc>', content)

        # Topic categories in Chinese to English mapping
        topic_mapping = {
            "编程入门": "programming",
            "数据结构与算法": "algorithms",
            "体系结构": "computer-architecture",
            "操作系统": "operating-systems",
            "计算机网络": "networking",
            "数据库": "databases",
            "分布式系统": "distributed-systems",
            "人工智能": "artificial-intelligence",
            "机器学习": "machine-learning",
            "深度学习": "deep-learning",
            "计算机视觉": "computer-vision",
            "自然语言处理": "natural-language-processing",
            "Web开发": "web-development",
            "编译原理": "compilers",
            "密码学": "cryptography",
            "安全": "security",
            "数学基础": "mathematics",
            "并行与分布式系统": "parallel-computing",
            "必学工具": "tools",
        }

        for i, url in enumerate(urls[1:], start=1):  # Skip the first URL (homepage)
            # Parse the URL to extract topic and course name
            # Format: https://csdiy.wiki/Category/CourseName/
            parts = url.rstrip("/").split("/")[-2:]
            if len(parts) >= 2:
                category_encoded, course_encoded = parts
            else:
                continue

            # URL decode
            from urllib.parse import unquote
            category = unquote(category_encoded)
            course_name = unquote(course_encoded)

            # Skip non-course pages (home, guides, etc.)
            skip_categories = ["CS学习规划", "使用指南", "后记", "好书推荐", ""]
            skip_course_names = ["CS学习规划", "使用指南", "后记", "好书推荐"]
            if category in skip_categories or course_name in skip_course_names:
                continue

            # Skip category pages (where course_name matches category)
            if course_name == category or not course_encoded:
                continue

            # Determine topic
            topics: list[str] = []
            for cn_topic, en_topic in topic_mapping.items():
                if cn_topic in category:
                    topics.append(en_topic)

            # Determine difficulty from course name
            difficulty = Difficulty.INTERMEDIATE
            course_lower = course_name.lower()
            if any(word in course_lower for word in ["intro", "beginner", "basic", "50", "61a", "61b"]):
                difficulty = Difficulty.BEGINNER
            elif any(word in course_lower for word in ["advanced", "graduate", "6.8", "6.9", "149", "186"]):
                difficulty = Difficulty.ADVANCED

            # Clean up course name
            course_name = course_name.replace("-", " ").replace("_", " ")
            if not course_name:
                continue

            course = Course(
                resource_id=f"csdiy-{i:03d}",
                title=course_name,
                url=url,
                source="csdiy",
                topics=topics or ["general"],
                difficulty=difficulty,
                institution="",  # Will be filled when parsing individual pages
                course_code=course_encoded,
                prerequisites=[],
            )
            courses.append(course)

        return courses[:200]  # Limit to 200 courses

    def _get_fallback_csdiy_courses(self) -> list[Course]:
        """Return fallback courses if scraping fails."""
        return [
            Course(
                resource_id="csdiy-001",
                title="MIT 6.006: Introduction to Algorithms",
                url="https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
                source="csdiy",
                topics=["algorithms", "data-structures"],
                difficulty=Difficulty.BEGINNER,
                institution="MIT",
                course_code="6.006",
                prerequisites=[],
            ),
            Course(
                resource_id="csdiy-002",
                title="MIT 6.824: Distributed Systems",
                url="https://pdos.csail.mit.edu/6.824/",
                source="csdiy",
                topics=["distributed-systems", "systems"],
                difficulty=Difficulty.ADVANCED,
                institution="MIT",
                course_code="6.824",
                prerequisites=[],
            ),
            Course(
                resource_id="csdiy-003",
                title="CS61A: Structure and Interpretation of Computer Programs",
                url="https://cs61a.org/",
                source="csdiy",
                topics=["programming", "functional-programming"],
                difficulty=Difficulty.BEGINNER,
                institution="UC Berkeley",
                course_code="CS61A",
                prerequisites=[],
            ),
            Course(
                resource_id="csdiy-004",
                title="CS61B: Data Structures",
                url="https://sp24.datastructur.es/",
                source="csdiy",
                topics=["data-structures", "algorithms"],
                difficulty=Difficulty.BEGINNER,
                institution="UC Berkeley",
                course_code="CS61B",
                prerequisites=["CS61A"],
            ),
            Course(
                resource_id="csdiy-005",
                title="MIT 6.S081: Operating System Engineering",
                url="https://pdos.csail.mit.edu/6.S081/2021/",
                source="csdiy",
                topics=["operating-systems", "systems"],
                difficulty=Difficulty.ADVANCED,
                institution="MIT",
                course_code="6.S081",
                prerequisites=["6.006"],
            ),
        ]

    # ========== LeetCode ==========

    def load_leetcode_problems(self, force: bool = False) -> list[PracticeProblem]:
        """Load LeetCode problems from cache or LeetCode API.

        Args:
            force: Force re-fetch even if cached

        Returns:
            List of PracticeProblem objects
        """
        cached = read_json(LEETCODE_CACHE)
        if cached and not force:
            return [PracticeProblem(**p) for p in cached]

        # Load from LeetCode API
        problems = self._load_leetcode_from_api()

        # Cache the results
        if problems:
            write_json(LEETCODE_CACHE, [p.model_dump(mode="json") for p in problems])

        return problems

    def _load_leetcode_from_api(self) -> list[PracticeProblem]:
        """Load LeetCode problems from the LeetCode API."""
        problems: list[PracticeProblem] = []

        try:
            # Fetch from LeetCode API
            data = self._scraper.fetch_json(LEETCODE_API_URL)

            if not data:
                return self._get_fallback_leetcode_problems()

            # Parse the API response
            stat_status_pairs = data.get("stat_status_pairs", [])

            for i, item in enumerate(stat_status_pairs[:500]):  # Limit to 500 problems
                problem = self._parse_leetcode_api_item(item, i)
                if problem:
                    problems.append(problem)

            if not problems:
                return self._get_fallback_leetcode_problems()

            return problems

        except Exception:
            return self._get_fallback_leetcode_problems()

    def _parse_leetcode_api_item(self, item: dict, index: int) -> PracticeProblem | None:
        """Parse a LeetCode problem item from the API response."""
        try:
            stat = item.get("stat", {})
            title = stat.get("question__title", "")
            title_slug = stat.get("question__title_slug", "")

            if not title or not title_slug:
                return None

            # Parse difficulty
            difficulty_level = item.get("difficulty", {}).get("level", 2)
            if difficulty_level == 1:
                difficulty = Difficulty.BEGINNER
            elif difficulty_level == 3:
                difficulty = Difficulty.ADVANCED
            else:
                difficulty = Difficulty.INTERMEDIATE

            # Parse acceptance rate
            total_acs = stat.get("total_acs", 0)
            total_submitted = stat.get("total_submitted", 1)
            acceptance_rate = total_acs / total_submitted if total_submitted > 0 else 0.0

            # Parse tags
            tags = item.get("tags", [])
            topics: list[str] = []
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get("name", "")
                    if tag_name:
                        topics.append(tag_name.lower().replace(" ", "-"))
                elif isinstance(tag, str):
                    topics.append(tag.lower().replace(" ", "-"))

            return PracticeProblem(
                resource_id=f"lc-{index:04d}",
                title=title,
                url=f"https://leetcode.com/problems/{title_slug}/",
                source="leetcode",
                topics=topics or ["general"],
                difficulty=difficulty,
                problem_id=title_slug,
                acceptance_rate=round(acceptance_rate, 2),
            )
        except Exception:
            return None

    def _get_fallback_leetcode_problems(self) -> list[PracticeProblem]:
        """Return fallback LeetCode problems if dataset fails."""
        return [
            PracticeProblem(
                resource_id="lc-0001",
                title="Two Sum",
                url="https://leetcode.com/problems/two-sum/",
                source="leetcode",
                topics=["array", "hash-table"],
                difficulty=Difficulty.BEGINNER,
                problem_id="two-sum",
                acceptance_rate=0.49,
            ),
            PracticeProblem(
                resource_id="lc-0002",
                title="Add Two Numbers",
                url="https://leetcode.com/problems/add-two-numbers/",
                source="leetcode",
                topics=["linked-list", "math"],
                difficulty=Difficulty.INTERMEDIATE,
                problem_id="add-two-numbers",
                acceptance_rate=0.40,
            ),
            PracticeProblem(
                resource_id="lc-0003",
                title="Longest Substring Without Repeating Characters",
                url="https://leetcode.com/problems/longest-substring-without-repeating-characters/",
                source="leetcode",
                topics=["hash-table", "string", "sliding-window"],
                difficulty=Difficulty.INTERMEDIATE,
                problem_id="longest-substring-without-repeating-characters",
                acceptance_rate=0.33,
            ),
            PracticeProblem(
                resource_id="lc-0004",
                title="Median of Two Sorted Arrays",
                url="https://leetcode.com/problems/median-of-two-sorted-arrays/",
                source="leetcode",
                topics=["array", "binary-search", "divide-and-conquer"],
                difficulty=Difficulty.ADVANCED,
                problem_id="median-of-two-sorted-arrays",
                acceptance_rate=0.35,
            ),
            PracticeProblem(
                resource_id="lc-0005",
                title="Valid Parentheses",
                url="https://leetcode.com/problems/valid-parentheses/",
                source="leetcode",
                topics=["string", "stack"],
                difficulty=Difficulty.BEGINNER,
                problem_id="valid-parentheses",
                acceptance_rate=0.40,
            ),
            PracticeProblem(
                resource_id="lc-0006",
                title="Merge Two Sorted Lists",
                url="https://leetcode.com/problems/merge-two-sorted-lists/",
                source="leetcode",
                topics=["linked-list", "recursion"],
                difficulty=Difficulty.BEGINNER,
                problem_id="merge-two-sorted-lists",
                acceptance_rate=0.61,
            ),
            PracticeProblem(
                resource_id="lc-0007",
                title="Best Time to Buy and Sell Stock",
                url="https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
                source="leetcode",
                topics=["array", "dynamic-programming"],
                difficulty=Difficulty.BEGINNER,
                problem_id="best-time-to-buy-and-sell-stock",
                acceptance_rate=0.53,
            ),
            PracticeProblem(
                resource_id="lc-0008",
                title="Binary Search",
                url="https://leetcode.com/problems/binary-search/",
                source="leetcode",
                topics=["array", "binary-search"],
                difficulty=Difficulty.BEGINNER,
                problem_id="binary-search",
                acceptance_rate=0.56,
            ),
            PracticeProblem(
                resource_id="lc-0009",
                title="Maximum Subarray",
                url="https://leetcode.com/problems/maximum-subarray/",
                source="leetcode",
                topics=["array", "divide-and-conquer", "dynamic-programming"],
                difficulty=Difficulty.INTERMEDIATE,
                problem_id="maximum-subarray",
                acceptance_rate=0.49,
            ),
            PracticeProblem(
                resource_id="lc-0010",
                title="Binary Tree Level Order Traversal",
                url="https://leetcode.com/problems/binary-tree-level-order-traversal/",
                source="leetcode",
                topics=["tree", "breadth-first-search", "binary-tree"],
                difficulty=Difficulty.INTERMEDIATE,
                problem_id="binary-tree-level-order-traversal",
                acceptance_rate=0.63,
            ),
        ]

    # ========== Codeforces ==========

    def load_codeforces_problems(self, force: bool = False) -> list[PracticeProblem]:
        """Load Codeforces problems from cache or Codeforces API.

        Args:
            force: Force re-fetch even if cached

        Returns:
            List of PracticeProblem objects
        """
        cached = read_json(CODEFORCES_CACHE)
        if cached and not force:
            return [PracticeProblem(**p) for p in cached]

        # Load from Codeforces API
        problems = self._load_codeforces_from_api()

        # Cache the results
        if problems:
            write_json(CODEFORCES_CACHE, [p.model_dump(mode="json") for p in problems])

        return problems

    def _load_codeforces_from_api(self) -> list[PracticeProblem]:
        """Load Codeforces problems from the Codeforces API."""
        problems: list[PracticeProblem] = []

        try:
            # Use a scraper with lower rate limit for Codeforces API
            scraper = Scraper(ScrapingConfig(rate_limit=CODEFORCES_RATE_LIMIT))
            data = scraper.fetch_json(CODEFORCES_API_URL)

            if not data or data.get("status") != "OK":
                return self._get_fallback_codeforces_problems()

            result = data.get("result", {})
            problem_list = result.get("problems", [])

            for i, prob in enumerate(problem_list[:500]):  # Limit to 500 problems
                problem = self._parse_codeforces_item(prob, i)
                if problem:
                    problems.append(problem)

            if not problems:
                return self._get_fallback_codeforces_problems()

            return problems

        except Exception:
            return self._get_fallback_codeforces_problems()

    def _parse_codeforces_item(self, item: dict, index: int) -> PracticeProblem | None:
        """Parse a Codeforces problem item from the API."""
        try:
            contest_id = item.get("contestId")
            index_letter = item.get("index", "")
            name = item.get("name", "")

            if not contest_id or not name:
                return None

            problem_id = f"{contest_id}{index_letter}"
            url = f"https://codeforces.com/problemset/problem/{contest_id}/{index_letter}"

            # Parse rating to difficulty
            rating = item.get("rating")
            difficulty = _parse_codeforces_rating(rating)

            # Parse tags
            tags = item.get("tags", [])
            topics: list[str] = []
            for tag in tags:
                if isinstance(tag, str):
                    topics.append(tag.lower().replace(" ", "-"))

            return PracticeProblem(
                resource_id=f"cf-{index:04d}",
                title=name,
                url=url,
                source="codeforces",
                topics=topics or ["general"],
                difficulty=difficulty,
                problem_id=problem_id,
                rating=rating,
            )
        except Exception:
            return None

    def _get_fallback_codeforces_problems(self) -> list[PracticeProblem]:
        """Return fallback Codeforces problems if API fails."""
        return [
            PracticeProblem(
                resource_id="cf-0001",
                title="Watermelon",
                url="https://codeforces.com/problemset/problem/4/A",
                source="codeforces",
                topics=["math"],
                difficulty=Difficulty.BEGINNER,
                problem_id="4A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0002",
                title="Way Too Long Words",
                url="https://codeforces.com/problemset/problem/71/A",
                source="codeforces",
                topics=["strings"],
                difficulty=Difficulty.BEGINNER,
                problem_id="71A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0003",
                title="Team",
                url="https://codeforces.com/problemset/problem/231/A",
                source="codeforces",
                topics=["implementation"],
                difficulty=Difficulty.BEGINNER,
                problem_id="231A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0004",
                title="Next Round",
                url="https://codeforces.com/problemset/problem/158/A",
                source="codeforces",
                topics=["implementation"],
                difficulty=Difficulty.BEGINNER,
                problem_id="158A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0005",
                title="String Task",
                url="https://codeforces.com/problemset/problem/118/A",
                source="codeforces",
                topics=["strings"],
                difficulty=Difficulty.BEGINNER,
                problem_id="118A",
                rating=1000,
            ),
            PracticeProblem(
                resource_id="cf-0006",
                title="Bit++",
                url="https://codeforces.com/problemset/problem/282/A",
                source="codeforces",
                topics=["implementation"],
                difficulty=Difficulty.BEGINNER,
                problem_id="282A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0007",
                title="Beautiful Matrix",
                url="https://codeforces.com/problemset/problem/263/A",
                source="codeforces",
                topics=["implementation"],
                difficulty=Difficulty.BEGINNER,
                problem_id="263A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0008",
                title="Petya and Strings",
                url="https://codeforces.com/problemset/problem/112/A",
                source="codeforces",
                topics=["strings"],
                difficulty=Difficulty.BEGINNER,
                problem_id="112A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0009",
                title="Soldier and Bananas",
                url="https://codeforces.com/problemset/problem/546/A",
                source="codeforces",
                topics=["math"],
                difficulty=Difficulty.BEGINNER,
                problem_id="546A",
                rating=800,
            ),
            PracticeProblem(
                resource_id="cf-0010",
                title="Nearly Lucky Number",
                url="https://codeforces.com/problemset/problem/110/A",
                source="codeforces",
                topics=["implementation"],
                difficulty=Difficulty.BEGINNER,
                problem_id="110A",
                rating=800,
            ),
        ]

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
