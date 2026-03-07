"""Unit tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a Click test runner."""
        return CliRunner()

    def test_version_option(self, runner: CliRunner) -> None:
        """Test --version option."""
        from oss_navi.cli import main

        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "oss-navi" in result.output

    def test_verbose_flag(self, runner: CliRunner) -> None:
        """Test --verbose/-v flag."""
        from oss_navi.cli import main

        result = runner.invoke(main, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_quiet_flag(self, runner: CliRunner) -> None:
        """Test --quiet/-q flag."""
        from oss_navi.cli import main

        result = runner.invoke(main, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_help_option(self, runner: CliRunner) -> None:
        """Test --help option."""
        from oss_navi.cli import main

        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "OSS-Navi" in result.output
        assert "--verbose" in result.output
        assert "--quiet" in result.output

    def test_analysis_no_cache(self, runner: CliRunner) -> None:
        """Test analysis command with no cached data."""
        from oss_navi.cli import main

        with patch("oss_navi.utils.cache.read_json", return_value=None):
            result = runner.invoke(main, ["analysis"])
            assert result.exit_code == 2
            assert "No cached profile data" in result.output

    def test_sync_dry_run(self, runner: CliRunner) -> None:
        """Test sync command with --dry-run."""
        from oss_navi.cli import main

        result = runner.invoke(main, ["sync", "--dry-run"])
        assert result.exit_code == 0
        assert "Would fetch:" in result.output

    def test_sync_no_username(self, runner: CliRunner) -> None:
        """Test sync command without configured username."""
        from oss_navi.cli import main

        with patch("oss_navi.config.load_config", return_value=None):
            result = runner.invoke(main, ["sync", "--github"])
            assert result.exit_code == 0
            assert "No GitHub username configured" in result.output

    def test_sync_tasks_force(self, runner: CliRunner) -> None:
        """Test sync --tasks --force."""
        from oss_navi.cli import main

        with patch("oss_navi.utils.cache.is_cache_valid", return_value=False):
            with patch("oss_navi.services.scraper.fetch_and_cache_tasks", return_value=[]):
                result = runner.invoke(main, ["sync", "--tasks", "--force"])
                assert result.exit_code == 0

    def test_config_set_username(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config --github-username command."""
        from oss_navi.cli import main
        from oss_navi.models.config import Config

        config_file = tmp_path / "state" / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            result = runner.invoke(main, ["config", "--github-username", "testuser"])
            assert result.exit_code == 0
            assert "GitHub username set" in result.output

    def test_config_set_invalid_username(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config with invalid GitHub username."""
        from oss_navi.cli import main

        config_file = tmp_path / "state" / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            result = runner.invoke(main, ["config", "--github-username", "-invalid"])
            assert result.exit_code == 1
            assert "Invalid GitHub username" in result.output

    def test_config_set_token(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config --github-token command."""
        from oss_navi.cli import main

        config_file = tmp_path / "state" / "config.json"
        token_file = tmp_path / ".token"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            with patch("oss_navi.config.TOKEN_FILE", token_file):
                result = runner.invoke(main, ["config", "--github-token", "ghp_test123"])
                assert result.exit_code == 0
                assert "token saved" in result.output.lower()

    def test_config_set_filters(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config with filter options."""
        from oss_navi.cli import main
        from oss_navi.config import load_config

        config_file = tmp_path / "state" / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            result = runner.invoke(main, [
                "config",
                "--github-username", "testuser",
                "--min-stars", "100",
                "--max-age", "30",
            ])
            assert result.exit_code == 0
            assert "Min stars filter" in result.output

    def test_config_reset(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config --reset command."""
        from oss_navi.cli import main

        config_file = tmp_path / "state" / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            result = runner.invoke(main, ["config", "--reset"])
            assert result.exit_code == 0
            assert "reset" in result.output.lower()

    def test_config_list_empty(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config --list with no configuration."""
        from oss_navi.cli import main

        config_file = tmp_path / "state" / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            result = runner.invoke(main, ["config", "--list"])
            assert result.exit_code == 0
            assert "No configuration" in result.output

    def test_config_list_with_config(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config --list with existing configuration."""
        from oss_navi.cli import main
        from oss_navi.config import save_config
        from oss_navi.models.config import Config

        config_file = tmp_path / "state" / "config.json"

        with patch("oss_navi.config.CONFIG_FILE", config_file):
            save_config(Config(github_username="testuser"))
            result = runner.invoke(main, ["config", "--list"])
            assert result.exit_code == 0
            assert "testuser" in result.output

    def test_publish_command(self, runner: CliRunner) -> None:
        """Test publish command with no report."""
        from oss_navi.cli import main

        with patch("oss_navi.services.publisher.get_current_report", return_value=None):
            result = runner.invoke(main, ["publish"])
            assert result.exit_code == 1  # No report to archive
            assert "No report found" in result.output


class TestAnalysisCommand:
    """Tests for analysis command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_profile(self) -> dict:
        """Create mock profile data."""
        return {
            "username": "testuser",
            "languages": {"Python": 0.6, "TypeScript": 0.3},
            "public_repos": 42,
        }

    @pytest.fixture
    def mock_tasks(self) -> list[dict]:
        """Create mock task data."""
        return [
            {
                "id": "test:1",
                "title": "Test issue",
                "url": "https://github.com/owner/repo/issues/1",
                "source": "upforgrabs",
                "repository": {
                    "name": "owner/repo",
                    "url": "https://github.com/owner/repo",
                    "stars": 100,
                    "language": "Python",
                },
                "labels": ["good first issue"],
                "created_at": "2026-03-01T00:00:00+00:00",
                "updated_at": "2026-03-05T00:00:00+00:00",
                "hotness_score": 10.0,
                "fetched_at": "2026-03-07T00:00:00+00:00",
            }
        ]

    def test_analysis_success(
        self, runner: CliRunner, mock_profile: dict, mock_tasks: list[dict]
    ) -> None:
        """Test successful analysis."""
        from oss_navi.cli import main
        from oss_navi.models.report import AnalysisReport
        from datetime import datetime, timezone

        mock_report = AnalysisReport(
            id="20260307_120000",
            created_at=datetime.now(timezone.utc),
            content="# Test Report",
            file_path="/tmp/test_report.md",
        )

        def mock_read_json_side_effect(path):
            if "github_profile" in str(path):
                return mock_profile
            elif "tasks" in str(path):
                return mock_tasks
            return None

        with patch("oss_navi.utils.cache.read_json", side_effect=mock_read_json_side_effect):
            with patch("oss_navi.services.analyzer.run_analysis", return_value=mock_report):
                result = runner.invoke(main, ["analysis"])
                assert result.exit_code == 0

    def test_analysis_with_learn_flag(
        self, runner: CliRunner, mock_profile: dict, mock_tasks: list[dict]
    ) -> None:
        """Test analysis with --learn flag."""
        from oss_navi.cli import main
        from oss_navi.models.report import AnalysisReport
        from datetime import datetime, timezone

        mock_report = AnalysisReport(
            id="20260307_120000",
            created_at=datetime.now(timezone.utc),
            content="# Test Report",
            file_path="/tmp/test_report.md",
            learning_focus="python",
        )

        def mock_read_json_side_effect(path):
            if "github_profile" in str(path):
                return mock_profile
            elif "tasks" in str(path):
                return mock_tasks
            return None

        with patch("oss_navi.utils.cache.read_json", side_effect=mock_read_json_side_effect):
            with patch("oss_navi.services.analyzer.run_analysis", return_value=mock_report) as mock_run:
                result = runner.invoke(main, ["analysis", "--learn", "python"])
                # Verify learning_focus was passed
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs.get("learning_focus") == "python"
