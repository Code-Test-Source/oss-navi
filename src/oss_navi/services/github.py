"""GitHub API client for fetching user profile and repository data."""

import os
import re
from datetime import UTC, datetime, timedelta

import httpx

from oss_navi.config import get_proxy_settings, should_verify_ssl
from oss_navi.models.task import IssueStatus
from oss_navi.models.user_profile import Activity, Repository, UserProfile
from oss_navi.utils.cache import read_json, update_cache_metadata, write_json
from oss_navi.utils.paths import GITHUB_PROFILE_CACHE

# Constants
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0

# The timeline endpoint requires the mockingbird preview to include cross-reference events.
# We keep both the standard v3 Accept and the preview type so other consumers of this
# header value are not affected.
TIMELINE_ACCEPT_HEADER = (
    "application/vnd.github.v3+json, application/vnd.github.mockingbird-preview+json"
)

# Labels that indicate an issue is being worked on
IN_PROGRESS_LABELS = {"in progress", "wip", "work in progress", "assigned", "taken"}


class GitHubAuthError(Exception):
    """Error for GitHub authentication failures."""

    pass


class GitHubRateLimitError(Exception):
    """Error for GitHub API rate limit exceeded."""

    pass


class GitHubClient:
    """GitHub API client for fetching user profile data."""

    def __init__(self, token: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, uses GITHUB_TOKEN env var)
            timeout: Request timeout in seconds
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._proxy_settings = get_proxy_settings()

    def _create_client(self) -> httpx.Client:
        """Create an httpx client with proxy support.

        Automatically uses proxy from environment variables (HTTP_PROXY, HTTPS_PROXY).
        SSL verification can be disabled via OSS_NAVI_VERIFY_SSL=false env var.

        Returns:
            Configured httpx.Client instance
        """
        http_proxy = self._proxy_settings["http_proxy"]
        https_proxy = self._proxy_settings["https_proxy"]
        verify_ssl = should_verify_ssl()

        if https_proxy and http_proxy:
            # Use mounts for different proxies per scheme
            return httpx.Client(
                timeout=self.timeout,
                verify=verify_ssl,
                mounts={
                    "http://": httpx.HTTPTransport(proxy=http_proxy, verify=verify_ssl),
                    "https://": httpx.HTTPTransport(proxy=https_proxy, verify=verify_ssl),
                }
            )
        elif https_proxy:
            return httpx.Client(timeout=self.timeout, verify=verify_ssl, proxy=https_proxy)
        elif http_proxy:
            return httpx.Client(timeout=self.timeout, verify=verify_ssl, proxy=http_proxy)
        else:
            return httpx.Client(timeout=self.timeout, verify=verify_ssl)

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

    def fetch_user_profile(self, username: str) -> UserProfile | None:
        """Fetch user profile from GitHub API.

        Args:
            username: GitHub username

        Returns:
            UserProfile object or None if user not found

        Raises:
            GitHubAuthError: For authentication failures
            GitHubRateLimitError: For rate limit exceeded
        """
        now = datetime.now(UTC)
        expires = now + timedelta(hours=24)

        with self._create_client() as client:
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

    def check_issue_status(
        self, owner: str, repo: str, issue_number: int
    ) -> IssueStatus:
        """Check the current status of a GitHub issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            IssueStatus with availability information
        """
        now = datetime.now(UTC)
        issue_url = f"https://github.com/{owner}/{repo}/issues/{issue_number}"

        with self._create_client() as client:
            response = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}",
                headers=self._get_headers(),
            )

            # Handle 403: raise rate limit error if rate-limited, otherwise treat as unavailable
            if response.status_code == 403:
                if response.headers.get("X-RateLimit-Remaining") == "0":
                    raise GitHubRateLimitError(
                        "GitHub API rate limit exceeded while checking issue status"
                    )
                return IssueStatus(
                    issue_url=issue_url,
                    is_assigned=False,
                    is_closed=True,  # Treat as unavailable (e.g. private repo)
                    has_linked_pr=False,
                    checked_at=now,
                )

            # Handle not found
            if response.status_code == 404:
                return IssueStatus(
                    issue_url=issue_url,
                    is_assigned=False,
                    is_closed=True,
                    has_linked_pr=False,
                    checked_at=now,
                )

            if response.status_code != 200:
                return IssueStatus(
                    issue_url=issue_url,
                    is_assigned=False,
                    is_closed=True,
                    has_linked_pr=False,
                    checked_at=now,
                )

            data = response.json()

            # Check if assigned
            assignee = data.get("assignee")
            is_assigned = assignee is not None
            assignee_login = assignee.get("login") if assignee else None

            # Check if closed
            is_closed = data.get("state") == "closed"

            # Check for in-progress labels
            labels = data.get("labels", [])
            in_progress_labels = [
                label["name"]
                for label in labels
                if label.get("name", "").lower() in IN_PROGRESS_LABELS
            ]

            # Check for linked PRs by inspecting the issue timeline for cross-referenced PRs
            has_linked_pr = False
            try:
                timeline_response = client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/timeline",
                    headers={**self._get_headers(), "Accept": TIMELINE_ACCEPT_HEADER},
                )
                if timeline_response.status_code == 403:
                    if timeline_response.headers.get("X-RateLimit-Remaining") == "0":
                        raise GitHubRateLimitError(
                            "GitHub API rate limit exceeded while fetching issue timeline"
                        )
                    # Other 403s (e.g. private repo) — fall back to no linked PR
                elif timeline_response.status_code == 200:
                    for event in timeline_response.json():
                        if event.get("event") != "cross-referenced":
                            continue
                        source_issue = event.get("source", {}).get("issue") or {}
                        # A source issue that has a "pull_request" key is itself a PR
                        if "pull_request" in source_issue:
                            has_linked_pr = True
                            break
            except GitHubRateLimitError:
                raise
            except Exception:
                # Network errors or unexpected failures — fall back to no linked PR
                has_linked_pr = False

            return IssueStatus(
                issue_url=issue_url,
                is_assigned=is_assigned,
                assignee=assignee_login,
                is_closed=is_closed,
                has_linked_pr=has_linked_pr,
                in_progress_labels=in_progress_labels,
                checked_at=now,
            )

    def check_multiple_issues(
        self, issue_urls: list[str], max_issues: int = 10
    ) -> list[IssueStatus]:
        """Check status of multiple issues with rate limit protection.

        Args:
            issue_urls: List of GitHub issue URLs
            max_issues: Maximum number of issues to check (default 10)

        Returns:
            List of IssueStatus objects
        """
        statuses = []

        # Parse URLs and limit to max_issues
        parsed = []
        for url in issue_urls[:max_issues]:
            match = re.match(
                r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", url
            )
            if match:
                parsed.append((match.group(1), match.group(2), int(match.group(3)), url))

        for owner, repo, issue_number, url in parsed:
            status = self.check_issue_status(owner, repo, issue_number)
            statuses.append(status)

        return statuses

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        per_page: int = 10,
    ) -> list[dict]:
        """Search GitHub repositories.

        Args:
            query: Search query (e.g., "language:Python stars:>1000")
            sort: Sort by "stars", "forks", or "updated"
            per_page: Number of results per page (max 100)

        Returns:
            List of repository dictionaries
        """
        with self._create_client() as client:
            response = client.get(
                f"{GITHUB_API_BASE}/search/repositories",
                headers=self._get_headers(),
                params={
                    "q": query,
                    "sort": sort,
                    "per_page": min(per_page, 100),
                },
            )

            self._handle_error_response(response)

            if response.status_code != 200:
                return []

            data = response.json()
            return data.get("items", [])


def fetch_and_cache_profile(username: str, token: str | None = None) -> UserProfile | None:
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


def load_cached_profile() -> dict | None:
    """Load cached profile from disk.

    Returns:
        Cached profile data or None if not cached
    """
    return read_json(GITHUB_PROFILE_CACHE)
