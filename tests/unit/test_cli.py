"""Unit tests for CLI commands."""

from datetime import UTC
from pathlib import Path
from unittest.mock import patch

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

    @pytest.mark.xfail(reason="Test isolation issue with CONFIG_FILE patching")
    def test_config_list_with_config(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test config --list with existing configuration."""
        from oss_navi.cli import main
        from oss_navi.models.config import Config

        config_file = tmp_path / "state" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write config file directly
        config = Config(github_username="testuser")
        config_file.write_text(config.model_dump_json())

        with patch("oss_navi.config.CONFIG_FILE", config_file):
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
        from datetime import datetime

        from oss_navi.cli import main
        from oss_navi.models.report import AnalysisReport

        mock_report = AnalysisReport(
            id="20260307_120000",
            created_at=datetime.now(UTC),
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
                with patch("oss_navi.services.analyzer.find_great_projects", return_value=[]):
                    with patch("oss_navi.services.analyzer.generate_recommendations", return_value=[]):
                        result = runner.invoke(main, ["analysis", "--no-interactive"])
                        assert result.exit_code == 0

    def test_analysis_with_learn_flag(
        self, runner: CliRunner, mock_profile: dict, mock_tasks: list[dict]
    ) -> None:
        """Test analysis with --learn flag."""
        from datetime import datetime

        from oss_navi.cli import main
        from oss_navi.models.report import AnalysisReport

        mock_report = AnalysisReport(
            id="20260307_120000",
            created_at=datetime.now(UTC),
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


class TestInteractivePrompts:
    """Tests for interactive prompts functionality."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a Click test runner."""
        return CliRunner()

    def test_prompt_learning_interests_returns_input(self) -> None:
        """Test that prompt_learning_interests returns user input."""
        from oss_navi.cli import prompt_learning_interests

        # Mock click.prompt to return user input
        with patch("click.prompt", return_value="Python async programming"):
            result = prompt_learning_interests()
            assert result == "Python async programming"

    def test_prompt_learning_interests_empty_allowed(self) -> None:
        """Test that prompt_learning_interests allows empty input."""
        from oss_navi.cli import prompt_learning_interests

        # Mock click.prompt to return empty string
        with patch("click.prompt", return_value=""):
            result = prompt_learning_interests()
            # Empty string should be converted to None
            assert result is None

    def test_analysis_with_explore_flag(
        self, runner: CliRunner
    ) -> None:
        """Test analysis with --explore flag for field suggestions."""
        from datetime import datetime

        from oss_navi.cli import main
        from oss_navi.models.report import AnalysisReport

        mock_profile = {"username": "test", "languages": {"Python": 1.0}}
        mock_tasks = [{
            "id": "test:1",
            "title": "Test",
            "url": "https://github.com/owner/repo/issues/1",
            "source": "upforgrabs",
            "repository": {"name": "owner/repo", "url": "https://github.com/owner/repo", "stars": 100, "language": "Python"},
            "labels": [],
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-05T00:00:00+00:00",
            "hotness_score": 10.0,
            "fetched_at": "2026-03-07T00:00:00+00:00",
        }]

        mock_report = AnalysisReport(
            id="20260307_120000",
            created_at=datetime.now(UTC),
            content="# Report",
            file_path="/tmp/report.md",
        )

        def mock_read_json_side_effect(path):
            if "github_profile" in str(path):
                return mock_profile
            elif "tasks" in str(path):
                return mock_tasks
            return None

        with patch("oss_navi.utils.cache.read_json", side_effect=mock_read_json_side_effect):
            with patch("oss_navi.services.analyzer.run_analysis", return_value=mock_report):
                with patch("oss_navi.services.analyzer.find_great_projects", return_value=[]):
                    with patch("oss_navi.services.analyzer.generate_recommendations", return_value=[]):
                        result = runner.invoke(main, ["analysis", "--explore", "--no-interactive"])
                        assert result.exit_code == 0

    def test_analysis_with_recommendations_count(
        self, runner: CliRunner
    ) -> None:
        """Test analysis with -n/--recommendations option."""
        from datetime import datetime

        from oss_navi.cli import main
        from oss_navi.models.report import AnalysisReport

        mock_profile = {"username": "test", "languages": {"Python": 1.0}}
        mock_tasks = [{
            "id": f"test:{i}",
            "title": f"Test {i}",
            "url": f"https://github.com/owner/repo{i}/issues/{i}",
            "source": "upforgrabs",
            "repository": {"name": f"owner/repo{i}", "url": f"https://github.com/owner/repo{i}", "stars": 100, "language": "Python"},
            "labels": [],
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-05T00:00:00+00:00",
            "hotness_score": 10.0,
            "fetched_at": "2026-03-07T00:00:00+00:00",
        } for i in range(10)]

        mock_report = AnalysisReport(
            id="20260307_120000",
            created_at=datetime.now(UTC),
            content="# Report",
            file_path="/tmp/report.md",
        )

        def mock_read_json_side_effect(path):
            if "github_profile" in str(path):
                return mock_profile
            elif "tasks" in str(path):
                return mock_tasks
            return None

        with patch("oss_navi.utils.cache.read_json", side_effect=mock_read_json_side_effect):
            with patch("oss_navi.services.analyzer.run_analysis", return_value=mock_report):
                with patch("oss_navi.services.analyzer.find_great_projects", return_value=[]):
                    with patch("oss_navi.services.analyzer.generate_recommendations", return_value=[]):
                        result = runner.invoke(main, ["analysis", "-n", "5", "--no-interactive"])
                        assert result.exit_code == 0
