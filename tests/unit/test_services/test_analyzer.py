"""Unit tests for analyzer service."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oss_navi.models.task import Repository, Task


class TestAnalyzer:
    """Tests for analyzer service."""

    @pytest.fixture
    def sample_tasks(self) -> list[Task]:
        """Create sample tasks for testing."""
        now = datetime.now(timezone.utc)
        return [
            Task(
                id="test:1",
                title="Fix bug",
                url="https://github.com/owner/repo/issues/1",
                source="upforgrabs",
                repository=Repository(
                    name="owner/repo",
                    url="https://github.com/owner/repo",
                    stars=100,
                    language="Python",
                ),
                labels=["good first issue"],
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
                hotness_score=10.0,
                fetched_at=now,
            ),
            Task(
                id="test:2",
                title="Add feature",
                url="https://github.com/owner/repo2/issues/2",
                source="goodfirstissues",
                repository=Repository(
                    name="owner/repo2",
                    url="https://github.com/owner/repo2",
                    stars=500,
                    language="Python",
                ),
                labels=["help wanted"],
                created_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
                updated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                hotness_score=12.5,
                fetched_at=now,
            ),
        ]

    @pytest.fixture
    def sample_profile(self) -> dict:
        """Create sample profile data for testing."""
        return {
            "username": "testuser",
            "languages": {"Python": 0.6, "TypeScript": 0.3, "Go": 0.1},
            "public_repos": 42,
            "top_repos": [
                {"name": "owner/repo1", "stars": 100},
                {"name": "owner/repo2", "stars": 50},
            ],
        }

    def test_filter_tasks_by_stars(self, sample_tasks: list[Task]) -> None:
        """Test filtering tasks by minimum star count."""
        from oss_navi.services.analyzer import filter_tasks_by_stars

        filtered = filter_tasks_by_stars(sample_tasks, min_stars=200)
        assert len(filtered) == 1
        assert filtered[0].repository.stars == 500

    def test_filter_tasks_by_recency(self, sample_tasks: list[Task]) -> None:
        """Test filtering tasks by recency (max age in days)."""
        from oss_navi.services.analyzer import filter_tasks_by_recency

        # Filter to tasks from last 30 days
        filtered = filter_tasks_by_recency(sample_tasks, max_age_days=30)
        # Both tasks are from March 2026, so both should be included
        assert len(filtered) >= 1

    def test_sort_tasks_by_hotness(self, sample_tasks: list[Task]) -> None:
        """Test sorting tasks by hotness score."""
        from oss_navi.services.analyzer import sort_tasks_by_hotness

        sorted_tasks = sort_tasks_by_hotness(sample_tasks)
        assert sorted_tasks[0].hotness_score >= sorted_tasks[-1].hotness_score

    def test_build_prompt(self, sample_profile: dict, sample_tasks: list[Task]) -> None:
        """Test building the analysis prompt."""
        from oss_navi.services.analyzer import build_prompt

        prompt = build_prompt(
            profile=sample_profile,
            tasks=sample_tasks,
            learning_focus="python",
        )
        assert "testuser" in prompt
        assert "Python" in prompt
        assert "python" in prompt.lower()

    @patch("subprocess.run")
    def test_invoke_claude_code_success(
        self, mock_run: MagicMock, sample_profile: dict, sample_tasks: list[Task]
    ) -> None:
        """Test successful Claude Code invocation."""
        from oss_navi.services.analyzer import invoke_claude_code

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="# Analysis Report\n\nRecommended: python/cpython",
            stderr="",
        )

        result = invoke_claude_code("Test prompt", timeout=60)
        assert "Analysis Report" in result

    @patch("subprocess.run")
    def test_invoke_claude_code_timeout(self, mock_run: MagicMock) -> None:
        """Test Claude Code timeout handling."""
        from oss_navi.services.analyzer import ClaudeCodeError, invoke_claude_code

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)

        with pytest.raises(ClaudeCodeError) as exc_info:
            invoke_claude_code("Test prompt", timeout=60)
        assert "timed out" in str(exc_info.value).lower()

    @patch("subprocess.run")
    def test_invoke_claude_code_not_found(self, mock_run: MagicMock) -> None:
        """Test Claude Code not found handling."""
        from oss_navi.services.analyzer import ClaudeCodeError, invoke_claude_code

        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(ClaudeCodeError) as exc_info:
            invoke_claude_code("Test prompt", timeout=60)
        assert "not found" in str(exc_info.value).lower() or "install" in str(exc_info.value).lower()

    def test_save_report(self, temp_home: Path) -> None:
        """Test saving report to temp directory."""
        from oss_navi.services.analyzer import save_report

        report_content = "# Test Report\n\nContent here."
        report_id = "20260307_100000"

        with patch("oss_navi.services.analyzer.TEMP_DIR", temp_home / "temp"):
            file_path = save_report(report_content, report_id)
            assert Path(file_path).exists()
            assert Path(file_path).read_text() == report_content

    @patch("oss_navi.services.analyzer.invoke_claude_code")
    def test_run_analysis_success(
        self, mock_invoke: MagicMock, sample_profile: dict, sample_tasks: list[Task]
    ) -> None:
        """Test successful run_analysis."""
        from oss_navi.services.analyzer import run_analysis

        mock_invoke.return_value = "# Analysis Report\n\nRecommended: python/cpython"

        with patch("oss_navi.services.analyzer.TEMP_DIR") as mock_temp:
            mock_temp.__truediv__ = lambda self, x: Path("/tmp") / x
            report = run_analysis(
                profile=sample_profile,
                tasks=sample_tasks,
                learning_focus="python",
            )
            assert report.content == "# Analysis Report\n\nRecommended: python/cpython"
            assert report.learning_focus == "python"

    def test_run_analysis_no_tasks(self, sample_profile: dict) -> None:
        """Test run_analysis with no matching tasks."""
        from oss_navi.services.analyzer import run_analysis

        # Create empty task list
        with pytest.raises(ValueError) as exc_info:
            run_analysis(
                profile=sample_profile,
                tasks=[],
            )
        assert "No matching tasks found" in str(exc_info.value)


class TestMemoryParsing:
    """Tests for memory parsing functions."""

    def test_parse_memory_update_found(self) -> None:
        """Test parsing memory update from report content."""
        from oss_navi.services.analyzer import parse_memory_update

        content = """# Analysis Report

## Skill Assessment
You have strong Python skills.

### 3. Top 1-2 Recommendations
- python/cpython

### 4. Long-term Memory Update
User is interested in learning async programming in Python. Focus on asyncio and aiohttp libraries.

## End
"""
        result = parse_memory_update(content)
        assert result is not None
        assert "async programming" in result
        assert "asyncio" in result

    def test_parse_memory_update_not_found(self) -> None:
        """Test parsing when memory update section is missing."""
        from oss_navi.services.analyzer import parse_memory_update

        content = """# Analysis Report

## Skill Assessment
You have strong Python skills.
"""
        result = parse_memory_update(content)
        assert result is None

    def test_parse_memory_update_empty(self) -> None:
        """Test parsing when memory update section is empty."""
        from oss_navi.services.analyzer import parse_memory_update

        content = """# Analysis Report

### 4. Long-term Memory Update

### 5. Next Steps
"""
        result = parse_memory_update(content)
        assert result is None

    def test_parse_recommendations_from_report(self) -> None:
        """Test parsing recommendations from report content."""
        from oss_navi.services.analyzer import parse_recommendations_from_report

        content = """# Analysis Report

### 3. Top 1-2 Recommendations

**Project 1: python/cpython**
- URL: https://github.com/python/cpython/issues/12345
- Great for learning CPython internals

**Project 2: pallets/click**
- URL: https://github.com/pallets/click/issues/42
- Good for CLI development

### 4. Long-term Memory Update
Focus on CLI tools.
"""
        recommendations = parse_recommendations_from_report(content)
        assert len(recommendations) == 2
        assert recommendations[0].project == "python/cpython"
        assert recommendations[0].issue_url == "https://github.com/python/cpython/issues/12345"
        assert recommendations[1].project == "pallets/click"

    def test_parse_recommendations_no_urls(self) -> None:
        """Test parsing recommendations when no GitHub URLs are present."""
        from oss_navi.services.analyzer import parse_recommendations_from_report

        content = """# Analysis Report

### 3. Top 1-2 Recommendations

No specific recommendations found.

### 4. Long-term Memory Update
Continue learning.
"""
        recommendations = parse_recommendations_from_report(content)
        assert len(recommendations) == 0

    def test_update_memory_from_report(self, tmp_path: Path) -> None:
        """Test updating memory from report content."""
        from oss_navi.services.analyzer import update_memory_from_report

        memory_file = tmp_path / "memory.json"

        with patch("oss_navi.services.analyzer.MEMORY_FILE", memory_file):
            content = """# Report

### 3. Top 1-2 Recommendations
https://github.com/python/cpython/issues/12345

### 4. Long-term Memory Update
Focus on async programming.
"""
            result = update_memory_from_report(content, learning_focus="rust")
            assert result is not None
            assert "Focus on async programming." in result.learning_goals
            assert "rust" in result.learning_goals
            assert len(result.past_recommendations) == 1
            assert result.past_recommendations[0].project == "python/cpython"

    def test_update_memory_preserves_existing(self, tmp_path: Path) -> None:
        """Test that updating memory preserves existing data."""
        from oss_navi.services.analyzer import update_memory_from_report
        from oss_navi.models.memory import LongTermMemory, PastRecommendation
        from datetime import datetime, timezone

        existing_memory = LongTermMemory(
            learning_goals=["existing goal"],
            past_recommendations=[
                PastRecommendation(
                    date=datetime.now(timezone.utc),
                    project="existing/repo",
                    issue_url="https://github.com/existing/repo/issues/1",
                )
            ],
        )

        memory_file = tmp_path / "memory.json"
        # Write existing memory to file so read_json can read it
        memory_file.write_text(existing_memory.model_dump_json())

        with patch("oss_navi.services.analyzer.MEMORY_FILE", memory_file):
            content = """# Report

### 4. Long-term Memory Update
New learning goal.
"""
            result = update_memory_from_report(content, learning_focus="python")
            assert result is not None
            assert "existing goal" in result.learning_goals
            assert "New learning goal." in result.learning_goals
            assert "python" in result.learning_goals
            assert len(result.past_recommendations) == 1  # Original preserved


class TestCalculateRatingBreakdown:
    """Tests for calculate_rating_breakdown function."""

    @pytest.fixture
    def sample_task(self) -> Task:
        """Create a sample task for testing."""
        now = datetime.now(timezone.utc)
        return Task(
            id="test:1",
            title="Fix bug in authentication",
            url="https://github.com/owner/repo/issues/1",
            source="upforgrabs",
            repository=Repository(
                name="owner/repo",
                url="https://github.com/owner/repo",
                stars=1000,
                language="Python",
                topics=["web", "authentication"],
            ),
            labels=["good first issue", "bug"],
            created_at=now,
            updated_at=now,
            hotness_score=50.0,
            fetched_at=now,
        )

    def test_calculate_rating_breakdown_language_match(self, sample_task: Task) -> None:
        """Test rating breakdown with language match."""
        from oss_navi.models.task import IssueStatus
        from oss_navi.services.analyzer import calculate_rating_breakdown

        user_languages = {"Python": 0.8, "JavaScript": 0.2}
        learning_focus = "Python"
        issue_status = IssueStatus(
            issue_url=sample_task.url,
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )

        breakdown = calculate_rating_breakdown(
            task=sample_task,
            user_languages=user_languages,
            learning_focus=learning_focus,
            issue_status=issue_status,
        )

        # Language match should be high (Python matches)
        assert breakdown.language_match >= 8.0
        # Issue availability should be 10 (available)
        assert breakdown.issue_availability == 10.0

    def test_calculate_rating_breakdown_no_match(self, sample_task: Task) -> None:
        """Test rating breakdown with no language match."""
        from oss_navi.models.task import IssueStatus
        from oss_navi.services.analyzer import calculate_rating_breakdown

        user_languages = {"Rust": 0.6, "Go": 0.4}
        learning_focus = "Rust"
        issue_status = IssueStatus(
            issue_url=sample_task.url,
            is_assigned=False,
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )

        breakdown = calculate_rating_breakdown(
            task=sample_task,
            user_languages=user_languages,
            learning_focus=learning_focus,
            issue_status=issue_status,
        )

        # Language match should be low (no Python in user languages)
        assert breakdown.language_match < 5.0

    def test_calculate_rating_breakdown_assigned_issue(self, sample_task: Task) -> None:
        """Test rating breakdown for assigned issue."""
        from oss_navi.models.task import IssueStatus
        from oss_navi.services.analyzer import calculate_rating_breakdown

        user_languages = {"Python": 0.8}
        learning_focus = "Python"
        issue_status = IssueStatus(
            issue_url=sample_task.url,
            is_assigned=True,
            assignee="other_dev",
            is_closed=False,
            has_linked_pr=False,
            checked_at=datetime.now(timezone.utc),
        )

        breakdown = calculate_rating_breakdown(
            task=sample_task,
            user_languages=user_languages,
            learning_focus=learning_focus,
            issue_status=issue_status,
        )

        # Availability should be 0 (assigned)
        assert breakdown.issue_availability == 0.0


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""

    @pytest.fixture
    def sample_tasks(self) -> list[Task]:
        """Create sample tasks for testing."""
        now = datetime.now(timezone.utc)
        tasks = []
        for i in range(15):
            task = Task(
                id=f"test:{i}",
                title=f"Issue {i}",
                url=f"https://github.com/owner/repo{i}/issues/{i}",
                source="upforgrabs",
                repository=Repository(
                    name=f"owner/repo{i}",
                    url=f"https://github.com/owner/repo{i}",
                    stars=100 * (i + 1),
                    language="Python" if i % 2 == 0 else "JavaScript",
                ),
                labels=["good first issue"],
                created_at=now,
                updated_at=now,
                hotness_score=10.0 * (i + 1),
                fetched_at=now,
            )
            tasks.append(task)
        return tasks

    def test_generate_recommendations_count(self, sample_tasks: list[Task]) -> None:
        """Test that generate_recommendations returns correct count."""
        from oss_navi.services.analyzer import generate_recommendations

        user_languages = {"Python": 0.6, "JavaScript": 0.4}
        learning_focus = "Python"

        with patch(
            "oss_navi.services.analyzer.check_issue_status"
        ) as mock_check:
            from oss_navi.models.task import IssueStatus
            mock_check.return_value = IssueStatus(
                issue_url="https://github.com/owner/repo/issues/1",
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(timezone.utc),
            )

            recommendations = generate_recommendations(
                tasks=sample_tasks,
                user_languages=user_languages,
                learning_focus=learning_focus,
                count=7,
            )

        assert 5 <= len(recommendations) <= 10

    def test_generate_recommendations_sorted_by_rating(
        self, sample_tasks: list[Task]
    ) -> None:
        """Test that recommendations are sorted by rating descending."""
        from oss_navi.services.analyzer import generate_recommendations

        user_languages = {"Python": 0.6, "JavaScript": 0.4}
        learning_focus = "Python"

        with patch(
            "oss_navi.services.analyzer.check_issue_status"
        ) as mock_check:
            from oss_navi.models.task import IssueStatus
            mock_check.return_value = IssueStatus(
                issue_url="https://github.com/owner/repo/issues/1",
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(timezone.utc),
            )

            recommendations = generate_recommendations(
                tasks=sample_tasks,
                user_languages=user_languages,
                learning_focus=learning_focus,
                count=5,
            )

        # Check sorted by rating descending
        ratings = [r.rating for r in recommendations]
        assert ratings == sorted(ratings, reverse=True)


class TestSuggestAdjacentFields:
    """Tests for suggest_adjacent_fields function."""

    def test_suggest_from_python(self) -> None:
        """Test field suggestions from Python background."""
        from oss_navi.services.analyzer import suggest_adjacent_fields

        suggestions = suggest_adjacent_fields(
            current_interest="Python",
            user_languages={"Python": 0.7, "JavaScript": 0.3},
        )

        assert len(suggestions) >= 2

    def test_suggest_count(self) -> None:
        """Test that suggestions return reasonable count."""
        from oss_navi.services.analyzer import suggest_adjacent_fields

        suggestions = suggest_adjacent_fields(
            current_interest="TypeScript",
            user_languages={"TypeScript": 0.6, "Python": 0.4},
        )

        assert 2 <= len(suggestions) <= 5
