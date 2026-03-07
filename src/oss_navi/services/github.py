"""GitHub API client for fetching user profile and repository data."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from oss_navi.models.user_profile import Activity, Repository, UserProfile
from oss_navi.utils.cache import read_json, update_cache_metadata, write_json
from oss_navi.utils.paths import GITHUB_PROFILE_CACHE


# Constants
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0


class GitHubAuthError(Exception):
    """Error for GitHub authentication failures."""

    pass


class GitHubRateLimitError(Exception):
    """Error for GitHub API rate limit exceeded."""

    pass


def get_proxy_settings() -> dict[str, str]:
    """Get proxy settings from environment variables.

    Returns:
        Dict with 'http_proxy', 'https_proxy', and 'no_proxy' keys
    """
    return {
        "http_proxy": os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"),
        "https_proxy": os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
        "no_proxy": os.environ.get("NO_PROXY") or os.environ.get("no_proxy"),
    }


class GitHubClient:
    """GitHub API client for fetching user profile data."""

    def __init__(self, token: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, uses GITHUB_TOKEN env var)
            timeout: Request timeout in seconds
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._proxy_settings = get_proxy_settings()

    def _get_proxies(self) -> Optional[dict[str, str]]:
        """Get proxy configuration for httpx."""
        proxies = {}
        if self._proxy_settings["http_proxy"]:
            proxies["http://"] = self._proxy_settings["http_proxy"]
        if self._proxy_settings["https_proxy"]:
            proxies["https://"] = self._proxy_settings["https_proxy"]
        return proxies if proxies else None

    def _get_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OSS-Navi/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from GitHub API.

        Args:
            response: HTTP response object

        Raises:
            GitHubAuthError: For authentication failures (401)
            GitHubRateLimitError: For rate limit exceeded (403 with rate limit header)
        """
        if response.status_code == 401:
            raise GitHubAuthError(
                "GitHub authentication failed. Check your token is valid."
            )
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            if remaining == "0":
                raise GitHubRateLimitError(
                    "GitHub API rate limit exceeded. Wait and try again later."
                )

    def fetch_user_profile(self, username: str) -> Optional[UserProfile]:
        """Fetch user profile from GitHub API.

        Args:
            username: GitHub username

        Returns:
            UserProfile object or None if user not found

        Raises:
            GitHubAuthError: For authentication failures
            GitHubRateLimitError: For rate limit exceeded
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=24)

        with httpx.Client(timeout=self.timeout, proxies=self._get_proxies()) as client:
            # Fetch user info
            user_response = client.get(
                f"{GITHUB_API_BASE}/users/{username}",
                headers=self._get_headers(),
            )

            if user_response.status_code == 404:
                return None

            self._handle_error_response(user_response)

            if user_response.status_code != 200:
                return None

            user_data = user_response.json()

            # Fetch repositories
            repos_response = client.get(
                f"{GITHUB_API_BASE}/users/{username}/repos",
                headers=self._get_headers(),
                params={"per_page": 100, "sort": "pushed"},
            )

            self._handle_error_response(repos_response)

            repos_data = repos_response.json() if repos_response.status_code == 200 else []

            # Calculate language distribution
            languages: dict[str, int] = {}
            for repo in repos_data:
                lang = repo.get("language")
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1

            total_repos = len(repos_data) if repos_data else 1
            language_percentages: dict[str, float] = {
                name: count / total_repos
                for name, count in sorted(languages.items(), key=lambda x: -x[1])
            }

            # Build top repos
            top_repos = []
            for repo in repos_data[:10]:
                try:
                    last_updated = datetime.fromisoformat(
                        repo.get("pushed_at", "").replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    last_updated = now

                top_repos.append(
                    Repository(
                        name=repo.get("full_name", repo.get("name", "")),
                        url=repo.get("html_url", ""),
                        stars=repo.get("stargazers_count", 0),
                        language=repo.get("language"),
                        description=repo.get("description"),
                        topics=repo.get("topics", []),
                        is_archived=repo.get("archived", False),
                        last_updated=last_updated,
                    )
                )

            # Build recent activity from repos
            recent_activity = []
            for repo in repos_data[:5]:
                try:
                    created_at = datetime.fromisoformat(
                        repo.get("pushed_at", "").replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    created_at = now

                recent_activity.append(
                    Activity(
                        type="PushEvent",
                        repo_name=repo.get("full_name", repo.get("name", "")),
                        created_at=created_at,
                    )
                )

            return UserProfile(
                username=user_data.get("login", username),
                name=user_data.get("name"),
                bio=user_data.get("bio"),
                public_repos=user_data.get("public_repos", 0),
                followers=user_data.get("followers", 0),
                following=user_data.get("following", 0),
                languages=language_percentages,
                recent_activity=recent_activity,
                top_repos=top_repos,
                fetched_at=now,
                expires_at=expires,
            )


def fetch_and_cache_profile(username: str, token: Optional[str] = None) -> Optional[UserProfile]:
    """Fetch user profile and cache it locally.

    Args:
        username: GitHub username
        token: GitHub personal access token

    Returns:
        UserProfile object or None if fetch failed
    """
    client = GitHubClient(token=token)
    profile = client.fetch_user_profile(username)

    if profile:
        # Cache the profile
        write_json(GITHUB_PROFILE_CACHE, profile.model_dump())
        update_cache_metadata("github_profile")

    return profile


def load_cached_profile() -> Optional[dict]:
    """Load cached profile from disk.

    Returns:
        Cached profile data or None if not cached
    """
    return read_json(GITHUB_PROFILE_CACHE)
