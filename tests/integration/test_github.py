"""Integration tests for GitHub API client."""

from unittest.mock import MagicMock, patch

import pytest


class TestGitHubClient:
    """Tests for GitHub API client."""

    @pytest.fixture
    def mock_user_response(self) -> dict:
        """Create a mock GitHub user API response."""
        return {
            "login": "testuser",
            "name": "Test User",
            "bio": "A test user",
            "public_repos": 42,
            "followers": 100,
            "following": 50,
        }

    @pytest.fixture
    def mock_repos_response(self) -> list[dict]:
        """Create a mock GitHub repos API response."""
        return [
            {
                "name": "repo1",
                "full_name": "testuser/repo1",
                "html_url": "https://github.com/testuser/repo1",
                "stargazers_count": 100,
                "language": "Python",
                "description": "Test repo 1",
                "topics": ["web", "api"],
                "archived": False,
                "pushed_at": "2026-03-01T00:00:00Z",
            },
            {
                "name": "repo2",
                "full_name": "testuser/repo2",
                "html_url": "https://github.com/testuser/repo2",
                "stargazers_count": 50,
                "language": "TypeScript",
                "description": "Test repo 2",
                "topics": ["cli"],
                "archived": False,
                "pushed_at": "2026-02-15T00:00:00Z",
            },
        ]

    @patch("httpx.Client")
    def test_fetch_user_profile(
        self,
        mock_client_class: MagicMock,
        mock_user_response: dict,
        mock_repos_response: list[dict],
    ) -> None:
        """Test fetching user profile from GitHub API."""
        from oss_navi.services.github import GitHubClient

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock responses
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_user_response),
            MagicMock(status_code=200, json=lambda: mock_repos_response),
        ]

        client = GitHubClient(token="test_token")
        profile = client.fetch_user_profile("testuser")

        assert profile is not None
        assert profile.username == "testuser"
        assert profile.public_repos == 42
        assert len(profile.languages) > 0

    @patch("httpx.Client")
    def test_fetch_user_profile_not_found(self, mock_client_class: MagicMock) -> None:
        """Test fetching non-existent user profile."""
        from oss_navi.services.github import GitHubClient

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(status_code=404)

        client = GitHubClient(token="test_token")
        profile = client.fetch_user_profile("nonexistent")

        assert profile is None

    @patch("httpx.Client")
    def test_rate_limit_handling(self, mock_client_class: MagicMock) -> None:
        """Test handling of GitHub API rate limits."""
        from oss_navi.services.github import GitHubClient, GitHubRateLimitError

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(
            status_code=403,
            headers={"X-RateLimit-Remaining": "0"},
        )

        client = GitHubClient(token="test_token")
        with pytest.raises(GitHubRateLimitError):
            client.fetch_user_profile("testuser")

    @patch("httpx.Client")
    def test_authentication_failure(self, mock_client_class: MagicMock) -> None:
        """Test handling of authentication failure."""
        from oss_navi.services.github import GitHubAuthError, GitHubClient

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(status_code=401)

        client = GitHubClient(token="invalid_token")
        with pytest.raises(GitHubAuthError):
            client.fetch_user_profile("testuser")
