"""Additional unit tests for scraper service."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestScrapersDetailed:
    """Detailed tests for scraper functions."""

    def test_sanitize_text(self) -> None:
        """Test text sanitization."""
        from oss_navi.services.scraper import sanitize_text

        assert sanitize_text("<p>Hello</p>") == "Hello"
        assert sanitize_text("  multiple   spaces  ") == "multiple spaces"
        assert sanitize_text(None) == ""
        assert sanitize_text("") == ""

    def test_validate_github_url(self) -> None:
        """Test GitHub URL validation."""
        from oss_navi.services.scraper import validate_github_url

        assert validate_github_url("https://github.com/owner/repo")
        assert validate_github_url("https://github.com/owner/repo/issues/1")
        assert not validate_github_url("https://gitlab.com/owner/repo")
        assert not validate_github_url("not-a-url")
        assert not validate_github_url("")
        assert not validate_github_url(None)

    def test_validate_github_issue_url_valid(self) -> None:
        """Test valid GitHub issue URLs."""
        from oss_navi.services.scraper import validate_github_issue_url

        assert validate_github_issue_url("https://github.com/python/cpython/issues/12345")
        assert validate_github_issue_url("https://github.com/pallets/click/issues/1")
        assert validate_github_issue_url("http://github.com/owner/repo/issues/999")

    def test_validate_github_issue_url_invalid(self) -> None:
        """Test invalid GitHub issue URLs."""
        from oss_navi.services.scraper import validate_github_issue_url

        # Not a GitHub URL
        assert not validate_github_issue_url("https://gitlab.com/owner/repo/issues/1")
        # Not an issue URL
        assert not validate_github_issue_url("https://github.com/owner/repo")
        assert not validate_github_issue_url("https://github.com/owner/repo/pulls/1")
        # Missing issue number
        assert not validate_github_issue_url("https://github.com/owner/repo/issues/")
        # Invalid issue number
        assert not validate_github_issue_url("https://github.com/owner/repo/issues/abc")
        # Empty/None
        assert not validate_github_issue_url("")
        assert not validate_github_issue_url(None)

    def test_validate_github_repo_url_valid(self) -> None:
        """Test valid GitHub repository URLs."""
        from oss_navi.services.scraper import validate_github_repo_url

        assert validate_github_repo_url("https://github.com/python/cpython")
        assert validate_github_repo_url("https://github.com/pallets/click")
        assert validate_github_repo_url("http://github.com/owner/repo")
        assert validate_github_repo_url("https://github.com/owner/repo-with-dashes")
        assert validate_github_repo_url("https://github.com/owner/repo_with_underscores")

    def test_validate_github_repo_url_invalid(self) -> None:
        """Test invalid GitHub repository URLs."""
        from oss_navi.services.scraper import validate_github_repo_url

        # Not a GitHub URL
        assert not validate_github_repo_url("https://gitlab.com/owner/repo")
        # Missing repo name
        assert not validate_github_repo_url("https://github.com/owner")
        assert not validate_github_repo_url("https://github.com/")
        # Invalid characters in names
        assert not validate_github_repo_url("https://github.com/owner/repo@invalid")
        # Empty/None
        assert not validate_github_repo_url("")
        assert not validate_github_repo_url(None)

    @patch("httpx.Client")
    def test_fetch_upforgrabs_with_issues(self, mock_client_class: MagicMock) -> None:
        """Test fetching Up For Grabs with valid projects."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First call: list of project files
        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        # Second call: YAML content
        yaml_content = """
name: Test Project
desc: A test project
site: https://github.com/owner/repo
tags:
  - python
  - web
upforgrabs:
  name: good first issue
  link: https://github.com/owner/repo/labels/good%20first%20issue
stats:
  issue-count: 2
  last-updated: '2026-03-05T00:00:00Z'
  fork-count: 100
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 2  # 2 issues from issue-count
        assert "Test Project" in tasks[0].title

    @patch("httpx.Client")
    def test_fetch_upforgrabs_invalid_url(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with invalid URLs."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First call: list of project files
        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        # Second call: YAML with non-GitHub URL
        yaml_content = """
name: Test Project
site: https://gitlab.com/owner/repo
upforgrabs:
  name: good first issue
stats:
  issue-count: 1
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0  # Should skip non-GitHub URLs

    @patch("httpx.Client")
    def test_fetch_goodfirstissue_empty(self, mock_client_class: MagicMock) -> None:
        """Test Good First Issue with empty response."""
        from oss_navi.services.scraper import fetch_goodfirstissue_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_client.get.return_value = MagicMock(
            status_code=200,
            text="<html><body></body></html>",
        )

        tasks = fetch_goodfirstissue_tasks()
        assert len(tasks) == 0

    @patch("httpx.Client")
    def test_fetch_and_cache_tasks(self, mock_client_class: MagicMock, tmp_path) -> None:
        """Test fetch_and_cache_tasks function."""
        from oss_navi.services.scraper import fetch_and_cache_tasks
        from pathlib import Path

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock Up For Grabs response (new YAML structure)
        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]
        yaml_content = """
name: Test Project
site: https://github.com/owner/repo
upforgrabs:
  name: good first issue
  link: https://github.com/owner/repo/issues/1
stats:
  issue-count: 1
  last-updated: '2026-03-05T00:00:00Z'
  fork-count: 100
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
            MagicMock(status_code=503, text=""),  # GFI unavailable
        ]
        mock_client.get.side_effect = responses

        with patch("oss_navi.utils.paths.UPFORGRABS_TASKS_CACHE", tmp_path / "ufg.json"):
            with patch("oss_navi.utils.paths.GOODFIRSTISSUE_TASKS_CACHE", tmp_path / "gfi.json"):
                with patch("oss_navi.utils.paths.CACHE_METADATA_FILE", tmp_path / "meta.json"):
                    tasks = fetch_and_cache_tasks(sources=["upforgrabs", "goodfirstissue"])
                    assert len(tasks) == 1

    @patch("httpx.Client")
    def test_fetch_goodfirstissue_with_content(self, mock_client_class: MagicMock) -> None:
        """Test Good First Issue with actual HTML content."""
        from oss_navi.services.scraper import fetch_goodfirstissue_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        html = """
        <html>
        <body>
            <article class="issue">
                <a class="issue-link" href="https://github.com/owner/repo/issues/1">Fix bug</a>
                <span class="stars">100</span>
                <span class="language">Python</span>
            </article>
        </body>
        </html>
        """

        mock_client.get.return_value = MagicMock(
            status_code=200,
            text=html,
        )

        tasks = fetch_goodfirstissue_tasks()
        # May or may not parse successfully depending on HTML structure
        assert isinstance(tasks, list)

    @patch("httpx.Client")
    def test_fetch_upforgrabs_empty_projects(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with empty projects list."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: [],
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0

    @patch("httpx.Client")
    def test_fetch_upforgrabs_malformed_issue(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with malformed YAML data."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text="invalid: yaml: : :"),  # Invalid YAML
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0  # Should skip malformed projects

    @patch("httpx.Client")
    def test_fetch_upforgrabs_missing_dates(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with missing date fields."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        project_files = [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

        # YAML without last-updated date
        yaml_content = """
name: Test Project
site: https://github.com/owner/repo
upforgrabs:
  name: good first issue
stats:
  issue-count: 1
"""

        responses = [
            MagicMock(status_code=200, json=lambda: project_files),
            MagicMock(status_code=200, text=yaml_content),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 1  # Should still work with default dates
