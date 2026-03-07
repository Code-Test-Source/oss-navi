"""Tests for GreatProject model."""


from oss_navi.models.task import GreatProject


class TestGreatProject:
    """Tests for GreatProject model validation."""

    def test_great_project_creation_minimal(self) -> None:
        """Test creating GreatProject with required fields only."""
        project = GreatProject(
            name="python/cpython",
            url="https://github.com/python/cpython",
            stars=60000,
            language="Python",
            why_great="Reference implementation of Python with excellent code quality",
            architecture_overview="Modular design with clear separation of interpreter components",
            key_patterns=["object-oriented design", "C extensions"],
            contribution_areas=["standard library", "documentation", "tests"],
            relevance_reason="Matches your Python expertise",
        )
        assert project.name == "python/cpython"
        assert project.stars == 60000
        assert project.language == "Python"

    def test_great_project_with_all_fields(self) -> None:
        """Test creating GreatProject with all optional fields."""
        project = GreatProject(
            name="rust-lang/rust",
            url="https://github.com/rust-lang/rust",
            stars=90000,
            language="Rust",
            why_great="Modern systems language with innovative borrow checker",
            architecture_overview="Compiler pipeline with LLVM backend",
            key_patterns=["ownership system", "zero-cost abstractions", "trait system"],
            contribution_areas=["compiler", "standard library", "documentation"],
            relevance_reason="Great for learning systems programming",
        )
        assert project.name == "rust-lang/rust"
        assert "ownership system" in project.key_patterns

    def test_great_project_key_patterns_list(self) -> None:
        """Test that key_patterns is a list."""
        project = GreatProject(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=1000,
            language="Python",
            why_great="Test project",
            architecture_overview="Test architecture",
            key_patterns=["pattern1", "pattern2", "pattern3"],
            contribution_areas=["area1"],
            relevance_reason="Test relevance",
        )
        assert len(project.key_patterns) == 3
        assert "pattern1" in project.key_patterns

    def test_great_project_contribution_areas_list(self) -> None:
        """Test that contribution_areas is a list."""
        project = GreatProject(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=1000,
            language="TypeScript",
            why_great="Test project",
            architecture_overview="Test architecture",
            key_patterns=["pattern1"],
            contribution_areas=["docs", "tests", "core"],
            relevance_reason="Test relevance",
        )
        assert len(project.contribution_areas) == 3

    def test_great_project_url_validation(self) -> None:
        """Test that URL must be a valid GitHub URL."""
        project = GreatProject(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=1000,
            language="Go",
            why_great="Test project",
            architecture_overview="Test architecture",
            key_patterns=["pattern1"],
            contribution_areas=["docs"],
            relevance_reason="Test relevance",
        )
        assert project.url.startswith("https://github.com/")

    def test_great_project_stars_positive(self) -> None:
        """Test that stars must be non-negative."""
        project = GreatProject(
            name="owner/repo",
            url="https://github.com/owner/repo",
            stars=0,
            language="Python",
            why_great="Test project",
            architecture_overview="Test architecture",
            key_patterns=[],
            contribution_areas=[],
            relevance_reason="Test relevance",
        )
        assert project.stars == 0
