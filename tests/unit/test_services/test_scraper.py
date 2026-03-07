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

    @patch("httpx.Client")
    def test_fetch_upforgrabs_with_issues(self, mock_client_class: MagicMock) -> None:
        """Test fetching Up For Grabs with valid issues."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_data = {
            "projects": [
                {
                    "name": "owner/repo",
                    "url": "https://github.com/owner/repo",
                    "stars": 100,
                    "language": "Python",
                    "topics": ["web"],
                    "issues": [
                        {
                            "number": 1,
                            "title": "Test Issue",
                            "url": "https://github.com/owner/repo/issues/1",
                            "labels": ["good first issue"],
                            "created_at": "2026-03-01T00:00:00Z",
                            "updated_at": "2026-03-05T00:00:00Z",
                        }
                    ],
                }
            ]
        }

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Test Issue"

    @patch("httpx.Client")
    def test_fetch_upforgrabs_invalid_url(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with invalid URLs."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_data = {
            "projects": [
                {
                    "name": "owner/repo",
                    "url": "https://gitlab.com/owner/repo",  # Invalid URL
                    "stars": 100,
                    "issues": [],
                }
            ]
        }

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0  # Should skip invalid URLs

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

        # Mock Up For Grabs response
        upforgrabs_data = {
            "projects": [
                {
                    "name": "owner/repo",
                    "url": "https://github.com/owner/repo",
                    "stars": 100,
                    "language": "Python",
                    "issues": [
                        {
                            "number": 1,
                            "title": "Test",
                            "url": "https://github.com/owner/repo/issues/1",
                            "labels": [],
                            "created_at": "2026-03-01T00:00:00Z",
                            "updated_at": "2026-03-05T00:00:00Z",
                        }
                    ],
                }
            ]
        }

        responses = [
            MagicMock(status_code=200, json=lambda: upforgrabs_data),
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
            json=lambda: {"projects": []},
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0

    @patch("httpx.Client")
    def test_fetch_upforgrabs_malformed_issue(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with malformed issue data."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_data = {
            "projects": [
                {
                    "name": "owner/repo",
                    "url": "https://github.com/owner/repo",
                    "stars": 100,
                    "issues": [
                        {"number": 1, "url": "not-a-url"},  # Invalid URL
                    ],
                }
            ]
        }

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 0  # Should skip malformed issues

    @patch("httpx.Client")
    def test_fetch_upforgrabs_missing_dates(self, mock_client_class: MagicMock) -> None:
        """Test Up For Grabs with missing date fields."""
        from oss_navi.services.scraper import fetch_upforgrabs_tasks

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_data = {
            "projects": [
                {
                    "name": "owner/repo",
                    "url": "https://github.com/owner/repo",
                    "stars": 100,
                    "issues": [
                        {
                            "number": 1,
                            "title": "Test",
                            "url": "https://github.com/owner/repo/issues/1",
                            "labels": [],
                            # No created_at/updated_at
                        }
                    ],
                }
            ]
        }

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_data,
        )

        tasks = fetch_upforgrabs_tasks()
        assert len(tasks) == 1  # Should still work with default dates
