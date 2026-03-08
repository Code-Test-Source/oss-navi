"""Tests for learning models."""


from oss_navi.models.learning import (
    Course,
    Difficulty,
    LearningPath,
    LearningResource,
    PracticeProblem,
    ResourceType,
)


class TestResourceType:
    """Tests for ResourceType enum."""

    def test_resource_type_values(self) -> None:
        """Test ResourceType enum values."""
        assert ResourceType.COURSE.value == "course"
        assert ResourceType.PRACTICE_PROBLEM.value == "practice_problem"
        assert ResourceType.TUTORIAL.value == "tutorial"
        assert ResourceType.DOCUMENTATION.value == "documentation"


class TestDifficulty:
    """Tests for Difficulty enum."""

    def test_difficulty_values(self) -> None:
        """Test Difficulty enum values."""
        assert Difficulty.BEGINNER.value == "beginner"
        assert Difficulty.INTERMEDIATE.value == "intermediate"
        assert Difficulty.ADVANCED.value == "advanced"


class TestLearningResource:
    """Tests for LearningResource model."""

    def test_create_learning_resource(self) -> None:
        """Test creating a LearningResource."""
        resource = LearningResource(
            resource_type=ResourceType.TUTORIAL,
            title="Python Tutorial",
            url="https://example.com/tutorial",
            source="example",
            topics=["python", "basics"],
            difficulty=Difficulty.BEGINNER,
            description="A beginner tutorial",
        )
        assert resource.title == "Python Tutorial"
        assert resource.resource_type == ResourceType.TUTORIAL

    def test_to_markdown(self) -> None:
        """Test to_markdown method."""
        resource = LearningResource(
            resource_type=ResourceType.TUTORIAL,
            title="Python Tutorial",
            url="https://example.com/tutorial",
            source="example",
            topics=["python"],
            difficulty=Difficulty.BEGINNER,
            description="Learn Python basics",
        )
        md = resource.to_markdown()
        assert "Python Tutorial" in md
        assert "example" in md
        assert "beginner" in md
        assert "Learn Python basics" in md


class TestCourse:
    """Tests for Course model."""

    def test_create_course(self) -> None:
        """Test creating a Course."""
        course = Course(
            title="MIT 6.006",
            url="https://ocw.mit.edu/6.006",
            source="csdiy",
            topics=["algorithms"],
            difficulty=Difficulty.INTERMEDIATE,
            institution="MIT",
            course_code="6.006",
            prerequisites=["6.001"],
        )
        assert course.institution == "MIT"
        assert course.course_code == "6.006"
        assert course.resource_type == ResourceType.COURSE

    def test_to_markdown(self) -> None:
        """Test to_markdown method."""
        course = Course(
            title="MIT 6.006",
            url="https://ocw.mit.edu/6.006",
            source="csdiy",
            topics=["algorithms", "data-structures"],
            difficulty=Difficulty.INTERMEDIATE,
            institution="MIT",
            course_code="6.006",
            prerequisites=["6.001"],
            description="Introduction to Algorithms",
        )
        md = course.to_markdown()
        assert "### MIT 6.006" in md
        assert "MIT" in md
        assert "6.006" in md
        assert "intermediate" in md
        assert "algorithms" in md.lower()


class TestPracticeProblem:
    """Tests for PracticeProblem model."""

    def test_create_practice_problem(self) -> None:
        """Test creating a PracticeProblem."""
        problem = PracticeProblem(
            title="Two Sum",
            url="https://leetcode.com/problems/two-sum",
            source="leetcode",
            topics=["array", "hash-table"],
            difficulty=Difficulty.BEGINNER,
            problem_id="two-sum",
            acceptance_rate=0.49,
        )
        assert problem.title == "Two Sum"
        assert problem.acceptance_rate == 0.49
        assert problem.resource_type == ResourceType.PRACTICE_PROBLEM

    def test_get_leetcode_url(self) -> None:
        """Test get_leetcode_url method."""
        problem = PracticeProblem(
            title="Two Sum",
            url="https://example.com",
            source="leetcode",
            topics=["array"],
            difficulty=Difficulty.BEGINNER,
            problem_id="two-sum",
        )
        url = problem.get_leetcode_url()
        assert "leetcode.com/problems/two-sum" in url

    def test_get_codeforces_url(self) -> None:
        """Test get_codeforces_url method."""
        problem = PracticeProblem(
            title="Watermelon",
            url="https://example.com",
            source="codeforces",
            topics=["math"],
            difficulty=Difficulty.BEGINNER,
            problem_id="4A",
            rating=800,
        )
        url = problem.get_codeforces_url()
        assert "codeforces.com" in url

    def test_to_markdown_with_acceptance_rate(self) -> None:
        """Test to_markdown with acceptance rate."""
        problem = PracticeProblem(
            title="Two Sum",
            url="https://leetcode.com/problems/two-sum",
            source="leetcode",
            topics=["array"],
            difficulty=Difficulty.BEGINNER,
            problem_id="two-sum",
            acceptance_rate=0.49,
        )
        md = problem.to_markdown()
        assert "49.0%" in md

    def test_to_markdown_with_rating(self) -> None:
        """Test to_markdown with Codeforces rating."""
        problem = PracticeProblem(
            title="Watermelon",
            url="https://codeforces.com/problem",
            source="codeforces",
            topics=["math"],
            difficulty=Difficulty.BEGINNER,
            problem_id="4A",
            rating=800,
        )
        md = problem.to_markdown()
        assert "Rating: 800" in md


class TestLearningPath:
    """Tests for LearningPath model."""

    def test_create_learning_path(self) -> None:
        """Test creating a LearningPath."""
        path = LearningPath(
            title="Web Development Path",
            description="Learn web development",
            target_skills=["html", "css", "javascript"],
            estimated_hours=100,
        )
        assert path.title == "Web Development Path"
        assert path.estimated_hours == 100

    def test_to_markdown(self) -> None:
        """Test to_markdown method."""
        course = Course(
            title="MIT 6.006",
            url="https://ocw.mit.edu/6.006",
            source="csdiy",
            topics=["algorithms"],
            difficulty=Difficulty.INTERMEDIATE,
        )
        problem = PracticeProblem(
            title="Two Sum",
            url="https://leetcode.com/problems/two-sum",
            source="leetcode",
            topics=["array"],
            difficulty=Difficulty.BEGINNER,
            problem_id="two-sum",
        )
        path = LearningPath(
            title="Algorithms Path",
            description="Learn algorithms",
            target_skills=["algorithms", "problem-solving"],
            resources=[course, problem],
            estimated_hours=50,
        )
        md = path.to_markdown()
        assert "# Learning Path: Algorithms Path" in md
        assert "Target Skills" in md
        assert "50 hours" in md
        assert "## Courses" in md
        assert "## Practice Problems" in md
