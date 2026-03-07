"""Unit tests for publisher service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPublisherService:
    """Tests for publisher service."""

    @pytest.fixture
    def temp_reports_dir(self, tmp_path: Path) -> Path:
        """Create a temporary reports directory."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        return reports_dir

    @pytest.fixture
    def temp_blog_repo(self, tmp_path: Path) -> Path:
        """Create a temporary blog repo directory."""
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        (blog_dir / ".git").mkdir()  # Fake git directory
        return blog_dir

    @pytest.fixture
    def sample_report(self, tmp_path: Path) -> Path:
        """Create a sample report file."""
        report = tmp_path / "test_report.md"
        report.write_text("# Test Report\n\nThis is a test.")
        return report

    def test_archive_report(self, sample_report: Path, temp_reports_dir: Path) -> None:
        """Test archiving a report."""
        from oss_navi.services.publisher import archive_report

        with patch("oss_navi.services.publisher.REPORTS_DIR", temp_reports_dir):
            archived = archive_report(sample_report)
            assert Path(archived).exists()
            assert "report_" in Path(archived).name

    def test_archive_report_custom_name(
        self, sample_report: Path, temp_reports_dir: Path
    ) -> None:
        """Test archiving with custom name."""
        from oss_navi.services.publisher import archive_report

        with patch("oss_navi.services.publisher.REPORTS_DIR", temp_reports_dir):
            archived = archive_report(sample_report, "custom_report.md")
            assert Path(archived).name == "custom_report.md"

    def test_archive_report_not_found(self, temp_reports_dir: Path) -> None:
        """Test archiving non-existent report."""
        from oss_navi.services.publisher import archive_report

        with patch("oss_navi.services.publisher.REPORTS_DIR", temp_reports_dir):
            with pytest.raises(FileNotFoundError):
                archive_report(Path("/nonexistent/report.md"))

    def test_list_archived_reports(self, temp_reports_dir: Path, tmp_path: Path) -> None:
        """Test listing archived reports."""
        from oss_navi.services.publisher import archive_report, list_archived_reports

        with patch("oss_navi.services.publisher.REPORTS_DIR", temp_reports_dir):
            # Create and archive reports with unique names
            for i in range(3):
                source = tmp_path / f"source_{i}.md"
                source.write_text(f"# Report {i}")
                archive_report(source, f"report_{i}.md")

            reports = list_archived_reports()
            assert len(reports) == 3

    def test_get_current_report_exists(self, tmp_path: Path) -> None:
        """Test getting current report when it exists."""
        from oss_navi.services.publisher import get_current_report

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        current_report = temp_dir / "current_report.md"
        current_report.write_text("# Current Report")

        with patch("oss_navi.services.publisher.TEMP_DIR", temp_dir):
            result = get_current_report()
            assert result == current_report

    def test_get_current_report_not_exists(self, tmp_path: Path) -> None:
        """Test getting current report when it doesn't exist."""
        from oss_navi.services.publisher import get_current_report

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        with patch("oss_navi.services.publisher.TEMP_DIR", temp_dir):
            result = get_current_report()
            assert result is None

    def test_push_to_blog_success(
        self, sample_report: Path, temp_blog_repo: Path, tmp_path: Path
    ) -> None:
        """Test successful push to blog."""
        from oss_navi.services.publisher import push_to_blog

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123def",
                stderr="",
            )

            commit = push_to_blog(
                sample_report,
                str(temp_blog_repo),
                "Test commit",
            )
            assert commit == "abc123def"

    def test_push_to_blog_not_git_repo(self, sample_report: Path, tmp_path: Path) -> None:
        """Test push to non-git directory."""
        from oss_navi.services.publisher import BlogRepoNotConfiguredError, push_to_blog

        non_git_dir = tmp_path / "not_git"
        non_git_dir.mkdir()

        with pytest.raises(BlogRepoNotConfiguredError):
            push_to_blog(sample_report, str(non_git_dir))

    def test_push_to_blog_not_found(self, sample_report: Path) -> None:
        """Test push to non-existent blog repo."""
        from oss_navi.services.publisher import BlogRepoNotConfiguredError, push_to_blog

        with pytest.raises(BlogRepoNotConfiguredError):
            push_to_blog(sample_report, "/nonexistent/path")

    def test_delete_report(self, tmp_path: Path) -> None:
        """Test deleting a report."""
        from oss_navi.services.publisher import delete_report

        report = tmp_path / "to_delete.md"
        report.write_text("# Delete me")

        delete_report(report)
        assert not report.exists()

    def test_delete_report_not_found(self, tmp_path: Path) -> None:
        """Test deleting non-existent report."""
        from oss_navi.services.publisher import delete_report

        with pytest.raises(FileNotFoundError):
            delete_report(tmp_path / "nonexistent.md")
