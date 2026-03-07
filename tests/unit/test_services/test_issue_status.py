"""Tests for issue status checking functionality."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

from oss_navi.models.task import IssueStatus
from oss_navi.services.github import GitHubClient


class TestCheckIssueStatus:
    """Tests for check_issue_status method."""

    @pytest.fixture
    def mock_client(self) -> GitHubClient:
        """Create a GitHubClient with mocked token."""
        return GitHubClient(token="ghp_test_token_12345")

    def test_check_issue_status_available(self, mock_client: GitHubClient) -> None:
        """Test checking an available (unassigned, open) issue."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 42,
            "state": "open",
            "assignee": None,
            "assignees": [],
        }

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            status = mock_client.check_issue_status("owner", "repo", 42)

        assert status.is_available is True
        assert status.is_assigned is False
        assert status.is_closed is False

    def test_check_issue_status_assigned(self, mock_client: GitHubClient) -> None:
        """Test checking an assigned issue."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 42,
            "state": "open",
            "assignee": {"login": "developer123"},
            "assignees": [{"login": "developer123"}],
        }

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            status = mock_client.check_issue_status("owner", "repo", 42)

        assert status.is_available is False
        assert status.is_assigned is True
        assert status.assignee == "developer123"

    def test_check_issue_status_closed(self, mock_client: GitHubClient) -> None:
        """Test checking a closed issue."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 42,
            "state": "closed",
            "assignee": None,
            "assignees": [],
        }

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            status = mock_client.check_issue_status("owner", "repo", 42)

        assert status.is_available is False
        assert status.is_closed is True

    def test_check_issue_status_with_labels(self, mock_client: GitHubClient) -> None:
        """Test checking issue with in-progress labels."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 42,
            "state": "open",
            "assignee": None,
            "assignees": [],
            "labels": [
                {"name": "good first issue"},
                {"name": "in progress"},
                {"name": "help wanted"},
            ],
        }

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            status = mock_client.check_issue_status("owner", "repo", 42)

        assert "in progress" in status.in_progress_labels


class TestCheckMultipleIssues:
    """Tests for batch issue status checking."""

    @pytest.fixture
    def mock_client(self) -> GitHubClient:
        """Create a GitHubClient with mocked token."""
        return GitHubClient(token="ghp_test_token_12345")

    def test_check_multiple_issues(self, mock_client: GitHubClient) -> None:
        """Test checking multiple issues at once."""
        issue_urls = [
            "https://github.com/owner/repo1/issues/1",
            "https://github.com/owner/repo2/issues/2",
        ]

        mock_response_open = MagicMock()
        mock_response_open.status_code = 200
        mock_response_open.json.return_value = {
            "number": 1,
            "state": "open",
            "assignee": None,
            "assignees": [],
        }

        mock_response_assigned = MagicMock()
        mock_response_assigned.status_code = 200
        mock_response_assigned.json.return_value = {
            "number": 2,
            "state": "open",
            "assignee": {"login": "dev"},
            "assignees": [{"login": "dev"}],
        }

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.side_effect = [mock_response_open, mock_response_assigned]
            mock_create.return_value = mock_http_client

            statuses = mock_client.check_multiple_issues(issue_urls)

        assert len(statuses) == 2
        assert statuses[0].is_available is True
        assert statuses[1].is_available is False

    def test_check_multiple_issues_with_limit(self, mock_client: GitHubClient) -> None:
        """Test that batch check respects rate limits."""
        # Create 10 issue URLs
        issue_urls = [f"https://github.com/owner/repo/issues/{i}" for i in range(10)]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 1,
            "state": "open",
            "assignee": None,
            "assignees": [],
        }

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            statuses = mock_client.check_multiple_issues(issue_urls, max_issues=5)

        # Should only check 5 issues due to limit
        assert len(statuses) == 5


class TestRateLimitHandling:
    """Tests for rate limit handling in issue status checks."""

    @pytest.fixture
    def mock_client(self) -> GitHubClient:
        """Create a GitHubClient with mocked token."""
        return GitHubClient(token="ghp_test_token_12345")

    def test_rate_limit_error(self, mock_client: GitHubClient) -> None:
        """Test handling of rate limit error during status check."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            # Should return a status indicating unavailable due to rate limit
            status = mock_client.check_issue_status("owner", "repo", 42)

        assert status.is_available is False

    def test_issue_not_found(self, mock_client: GitHubClient) -> None:
        """Test handling of 404 when issue doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(mock_client, "_create_client") as mock_create:
            mock_http_client = MagicMock()
            mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
            mock_http_client.__exit__ = MagicMock(return_value=False)
            mock_http_client.get.return_value = mock_response
            mock_create.return_value = mock_http_client

            # Should return status indicating issue is closed/unavailable
            status = mock_client.check_issue_status("owner", "repo", 999)

        assert status.is_available is False
        assert status.is_closed is True
