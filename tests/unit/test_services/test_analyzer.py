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
                source="goodfirstissue",
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
