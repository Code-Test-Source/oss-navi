"""Tests for analysis models."""


from oss_navi.models.analysis import (
    AnalysisRequest,
    AnalysisSummary,
    CodeAnalysis,
    ContributionArea,
    KeyFile,
)
from oss_navi.models.learning import Difficulty


class TestKeyFile:
    """Tests for KeyFile model."""

    def test_create_key_file(self) -> None:
        """Test creating a KeyFile instance."""
        kf = KeyFile(
            path="src/main.py",
            purpose="Main entry point",
            lines_of_code=100,
        )
        assert kf.path == "src/main.py"
        assert kf.purpose == "Main entry point"
        assert kf.lines_of_code == 100

    def test_key_file_optional_loc(self) -> None:
        """Test KeyFile without lines_of_code."""
        kf = KeyFile(
            path="README.md",
            purpose="Documentation",
        )
        assert kf.lines_of_code is None


class TestContributionArea:
    """Tests for ContributionArea model."""

    def test_create_contribution_area(self) -> None:
        """Test creating a ContributionArea instance."""
        area = ContributionArea(
            area="API endpoints",
            description="REST API implementation",
            difficulty=Difficulty.INTERMEDIATE,
            good_for_beginners=False,
            suggested_issues=["bug", "enhancement"],
            key_files=["src/api/"],
        )
        assert area.area == "API endpoints"
        assert area.good_for_beginners is False

    def test_contribution_area_defaults(self) -> None:
        """Test ContributionArea defaults."""
        area = ContributionArea(
            area="Tests",
            difficulty=Difficulty.BEGINNER,
        )
        assert area.good_for_beginners is False
        assert area.suggested_issues == []
        assert area.key_files == []


class TestCodeAnalysis:
    """Tests for CodeAnalysis model."""

    def test_create_code_analysis(self) -> None:
        """Test creating a CodeAnalysis instance."""
        analysis = CodeAnalysis(
            repository="owner/repo",
            architecture_overview="Microservices architecture",
            key_files=[
                KeyFile(path="src/main.py", purpose="Entry point"),
            ],
            tech_stack=["Python", "FastAPI"],
        )
        assert analysis.repository == "owner/repo"
        assert len(analysis.key_files) == 1
        assert "Python" in analysis.tech_stack

    def test_code_analysis_auto_id(self) -> None:
        """Test that analysis_id is auto-generated."""
        analysis = CodeAnalysis(
            repository="owner/repo",
            architecture_overview="Test",
        )
        assert len(analysis.analysis_id) == 8

    def test_to_markdown(self) -> None:
        """Test to_markdown conversion."""
        analysis = CodeAnalysis(
            repository="owner/repo",
            architecture_overview="Test architecture",
            tech_stack=["Python"],
            prerequisites=["Python 3.11+"],
            key_files=[
                KeyFile(path="main.py", purpose="Entry"),
            ],
            contribution_areas=[
                ContributionArea(
                    area="API",
                    difficulty=Difficulty.BEGINNER,
                    good_for_beginners=True,
                    suggested_issues=["bug"],
                ),
            ],
            code_reading_hints=["Start from main.py"],
        )
        md = analysis.to_markdown()
        assert "# Code Analysis: owner/repo" in md
        assert "## Architecture Overview" in md
        assert "## Tech Stack" in md
        assert "## Prerequisites" in md
        assert "## Key Files" in md
        assert "## Contribution Areas" in md
        assert "## Code Reading Hints" in md

    def test_to_markdown_empty_lists(self) -> None:
        """Test to_markdown with empty lists."""
        analysis = CodeAnalysis(
            repository="owner/repo",
            architecture_overview="Test",
        )
        md = analysis.to_markdown()
        assert "Not analyzed" in md  # For empty tech_stack


class TestAnalysisRequest:
    """Tests for AnalysisRequest model."""

    def test_create_analysis_request(self) -> None:
        """Test creating an AnalysisRequest."""
        request = AnalysisRequest(
            repository="owner/repo",
            focus_areas=["API", "Tests"],
            skill_level=Difficulty.ADVANCED,
        )
        assert request.repository == "owner/repo"
        assert request.focus_areas == ["API", "Tests"]
        assert request.skill_level == Difficulty.ADVANCED

    def test_analysis_request_defaults(self) -> None:
        """Test AnalysisRequest defaults."""
        request = AnalysisRequest(repository="owner/repo")
        assert request.focus_areas is None
        assert request.skill_level == Difficulty.INTERMEDIATE


class TestAnalysisSummary:
    """Tests for AnalysisSummary model."""

    def test_create_analysis_summary(self) -> None:
        """Test creating an AnalysisSummary."""
        summary = AnalysisSummary(
            repository="owner/repo",
            stars=1000,
            language="Python",
            key_areas=["API", "Tests"],
            beginner_friendly=True,
            analysis_id="abc12345",
        )
        assert summary.stars == 1000
        assert summary.beginner_friendly is True

    def test_to_markdown(self) -> None:
        """Test to_markdown conversion."""
        summary = AnalysisSummary(
            repository="owner/repo",
            stars=5000,
            language="Python",
            key_areas=["API", "Tests", "Docs"],
            beginner_friendly=True,
            analysis_id="abc12345",
        )
        md = summary.to_markdown()
        assert "### owner/repo" in md
        assert "Language: Python" in md
        assert "5,000" in md
        assert "Beginner-friendly" in md
