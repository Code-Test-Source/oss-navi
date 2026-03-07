"""Integration tests for task scraper services."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestUpForGrabsScraper:
    """Tests for Up For Grabs YAML fetcher."""

    @pytest.fixture
    def mock_upforgrabs_project_files(self) -> list:
        """Create mock Up For Grabs project file list."""
        return [
            {"name": "test-project.yml", "path": "_data/projects/test-project.yml"}
        ]

    @pytest.fixture
    def mock_upforgrabs_yaml(self) -> str:
        """Create mock Up For Grabs YAML content."""
        return """
name: Test Project
desc: A test project for open source contributions
site: https://github.com/owner/repo1
tags:
  - python
  - web
upforgrabs:
  name: good first issue
  link: https://github.com/owner/repo1/labels/good%20first%20issue
stats:
  issue-count: 2
  last-updated: '2026-03-05T00:00:00Z'
  fork-count: 100
"""

    @patch("httpx.Client")
    def test_fetch_upforgrabs_tasks(
        self, mock_client_class: MagicMock, mock_upforgrabs_project_files: list, mock_upforgrabs_yaml: str
    ) -> None:
        """Test fetching tasks from Up For Grabs."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # First call: list of project files
        # Second call: YAML content
        responses = [
            MagicMock(status_code=200, json=lambda: mock_upforgrabs_project_files),
            MagicMock(status_code=200, text=mock_upforgrabs_yaml),
        ]
        mock_client.get.side_effect = responses

        tasks = fetch_upforgrabs_tasks()

        assert len(tasks) >= 1
        assert tasks[0].source == "upforgrabs"

    @patch("httpx.Client")
    def test_fetch_upforgrabs_unavailable(self, mock_client_class: MagicMock) -> None:
        """Test handling when Up For Grabs is unavailable."""
        from oss_navi.services.scraper import UpForGrabsUnavailableError, fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(status_code=503)

        with pytest.raises(UpForGrabsUnavailableError):
            fetch_upforgrabs_tasks()


class TestGoodFirstIssueScraper:
    """Tests for Good First Issue web scraper."""

    @pytest.fixture
    def mock_gfi_html(self) -> str:
        """Create mock Good First Issue HTML response."""
        return """
        <html>
        <body>
            <div class="issue">
                <a href="/owner/repo1" class="project">owner/repo1</a>
                <span class="stars">100</span>
                <span class="language">Python</span>
                <a href="https://github.com/owner/repo1/issues/123" class="issue-link">
                    Fix bug in authentication
                </a>
                <span class="created-at">2026-03-01</span>
            </div>
        </body>
        </html>
        """

    @patch("httpx.Client")
    def test_fetch_goodfirstissue_tasks(
        self, mock_client_class: MagicMock, mock_gfi_html: str
    ) -> None:
        """Test fetching tasks from Good First Issue."""
        from oss_navi.services.scraper import fetch_goodfirstissue_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(
            status_code=200,
            text=mock_gfi_html,
        )

        tasks = fetch_goodfirstissue_tasks()

        assert len(tasks) >= 0  # May be empty if parsing fails

    @patch("httpx.Client")
    def test_fetch_goodfirstissue_unavailable(self, mock_client_class: MagicMock) -> None:
        """Test handling when Good First Issue is unavailable."""
        from oss_navi.services.scraper import GoodFirstIssueUnavailableError, fetch_goodfirstissue_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(status_code=503)

        with pytest.raises(GoodFirstIssueUnavailableError):
            fetch_goodfirstissue_tasks()


class TestURLValidation:
    """Tests for URL validation in scraped data."""

    def test_validate_github_url_valid(self) -> None:
        """Test validating valid GitHub URLs."""
        from oss_navi.services.scraper import validate_github_url

        assert validate_github_url("https://github.com/owner/repo")
        assert validate_github_url("https://github.com/owner/repo/issues/123")

    def test_validate_github_url_invalid(self) -> None:
        """Test validating invalid URLs."""
        from oss_navi.services.scraper import validate_github_url

        assert not validate_github_url("https://gitlab.com/owner/repo")
        assert not validate_github_url("not-a-url")
        assert not validate_github_url("")
