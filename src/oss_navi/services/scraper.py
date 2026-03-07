"""Task scraper for fetching open source contribution opportunities."""

import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx
import yaml
from bs4 import BeautifulSoup

from oss_navi.models.task import Repository, Task, calculate_hotness_score
from oss_navi.utils.cache import read_json, update_cache_metadata, write_json
from oss_navi.utils.paths import GOODFIRSTISSUE_TASKS_CACHE, UPFORGRABS_TASKS_CACHE


# Constants
UPFORGRABS_PROJECTS_API = "https://api.github.com/repos/up-for-grabs/up-for-grabs.net/contents/_data/projects"
UPFORGRABS_RAW_URL = "https://raw.githubusercontent.com/up-for-grabs/up-for-grabs.net/gh-pages/_data/projects/{}"
GOODFIRSTISSUE_URL = "https://goodfirstissue.dev"
DEFAULT_TIMEOUT = 30.0


class UpForGrabsUnavailableError(Exception):
    """Error when Up For Grabs is unavailable."""

    pass


class GoodFirstIssueUnavailableError(Exception):
    """Error when Good First Issue is unavailable."""

    pass


def validate_github_url(url: str) -> bool:
    """Validate that a URL is a valid GitHub URL.

    Args:
        url: URL to validate

    Returns:
        True if valid GitHub URL, False otherwise
    """
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.netloc == "github.com" and parsed.scheme in ("http", "https")
    except Exception:
        return False


def validate_github_issue_url(url: str) -> bool:
    """Validate that a URL is a valid GitHub issue URL.

    Expected format: https://github.com/{owner}/{repo}/issues/{number}

    Args:
        url: URL to validate

    Returns:
        True if valid GitHub issue URL, False otherwise
    """
    if not validate_github_url(url):
        return False

    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        # Expected: [owner, repo, "issues", number] or [owner, repo, "issues"]
        if len(path_parts) < 4:
            return False

        if path_parts[2] != "issues":
            return False

        # Validate owner and repo names (non-empty, valid characters)
        owner = path_parts[0]
        repo = path_parts[1]

        if not owner or not repo:
            return False

        # GitHub naming rules: alphanumeric, hyphens, underscores
        valid_name_pattern = r"^[a-zA-Z0-9._-]+$"
        if not re.match(valid_name_pattern, owner) or not re.match(valid_name_pattern, repo):
            return False

        # Issue number should be numeric (if present)
        if len(path_parts) >= 4:
            issue_num = path_parts[3]
            if not issue_num.isdigit():
                return False

        return True
    except Exception:
        return False


def validate_github_repo_url(url: str) -> bool:
    """Validate that a URL is a valid GitHub repository URL.

    Expected format: https://github.com/{owner}/{repo}

    Args:
        url: URL to validate

    Returns:
        True if valid GitHub repository URL, False otherwise
    """
    if not validate_github_url(url):
        return False

    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        # Expected: [owner, repo] (optionally more for deeper paths)
        if len(path_parts) < 2:
            return False

        owner = path_parts[0]
        repo = path_parts[1]

        if not owner or not repo:
            return False

        # GitHub naming rules
        valid_name_pattern = r"^[a-zA-Z0-9._-]+$"
        if not re.match(valid_name_pattern, owner) or not re.match(valid_name_pattern, repo):
            return False

        return True
    except Exception:
        return False


def sanitize_text(text: Optional[str]) -> str:
    """Sanitize text by removing HTML tags and extra whitespace.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text.strip()


def fetch_upforgrabs_tasks(timeout: float = DEFAULT_TIMEOUT) -> list[Task]:
    """Fetch tasks from Up For Grabs.

    Note: Up For Grabs changed their data structure in 2024-2025. They no longer
    provide a single projects.json API. Instead, each project is stored as an
    individual YAML file in _data/projects/ directory.

    This function fetches project data from the new YAML-based structure.
    Since individual issues are no longer provided, we create project-level
    tasks that link to the GitHub label page for each project.

    Args:
        timeout: Request timeout in seconds

    Returns:
        List of Task objects (project-level, linking to label pages)

    Raises:
        UpForGrabsUnavailableError: If Up For Grabs is unavailable
    """
    tasks: list[Task] = []
    now = datetime.now(timezone.utc)

    with httpx.Client(timeout=timeout) as client:
        # Step 1: Fetch list of project YAML files
        try:
            list_response = client.get(UPFORGRABS_PROJECTS_API)
            if list_response.status_code != 200:
                raise UpForGrabsUnavailableError(
                    f"Up For Grabs API returned status {list_response.status_code}"
                )

            project_files = list_response.json()
            if not isinstance(project_files, list):
                raise UpForGrabsUnavailableError(
                    "Unexpected response format from Up For Grabs API"
                )

        except httpx.RequestError as e:
            raise UpForGrabsUnavailableError(f"Failed to fetch Up For Grabs: {e}")

        # Step 2: Fetch and parse each project YAML file (limit to avoid rate limits)
        max_projects = 50  # Limit to avoid GitHub API rate limits
        for project_file in project_files[:max_projects]:
            try:
                filename = project_file.get("name", "")
                if not filename.endswith(".yml"):
                    continue

                # Fetch raw YAML content
                raw_url = UPFORGRABS_RAW_URL.format(filename)
                yaml_response = client.get(raw_url)

                if yaml_response.status_code != 200:
                    continue

                # Parse YAML
                project_data = yaml.safe_load(yaml_response.text)
                if not project_data:
                    continue

                # Extract project info
                site_url = project_data.get("site", "")
                if not validate_github_repo_url(site_url):
                    continue

                # Parse repository name from URL
                parsed = urlparse(site_url)
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) < 2:
                    continue
                repo_name = f"{path_parts[0]}/{path_parts[1]}"

                # Get label info
                upforgrabs = project_data.get("upforgrabs", {})
                label_name = upforgrabs.get("name", "up for grabs")
                label_url = upforgrabs.get("link", "")

                if not validate_github_url(label_url):
                    # Construct label URL from site URL
                    label_url = f"{site_url}/labels/{label_name.replace(' ', '%20')}"

                # Get stats
                stats = project_data.get("stats", {})
                issue_count = stats.get("issue-count", 0) or 0
                fork_count = stats.get("fork-count", 0) or 0
                last_updated = stats.get("last-updated", "")

                # Parse last updated date
                try:
                    updated_at = datetime.fromisoformat(
                        last_updated.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    updated_at = now

                # Get tags
                tags = project_data.get("tags", [])
                language = tags[0] if tags else None

                # Create repository
                repo = Repository(
                    name=repo_name,
                    url=site_url,
                    stars=fork_count,  # Use fork count as proxy for popularity
                    language=sanitize_text(language),
                    topics=tags,
                )

                # Create a task for each issue (simulated based on issue_count)
                # Since we don't have individual issues, we create project-level tasks
                for i in range(min(issue_count, 3)):  # Limit to 3 tasks per project
                    hotness = calculate_hotness_score(fork_count, max(1, (now - updated_at).days))

                    task = Task(
                        id=f"upforgrabs:{repo_name.replace('/', '-')}:{i}",
                        title=f"{project_data.get('name', repo_name)} - {label_name}",
                        url=label_url,
                        source="upforgrabs",
                        repository=repo,
                        labels=[label_name],
                        created_at=updated_at,
                        updated_at=updated_at,
                        hotness_score=hotness,
                        fetched_at=now,
                    )
                    tasks.append(task)

            except Exception:
                # Skip malformed projects
                continue

    return tasks


def fetch_goodfirstissue_tasks(timeout: float = DEFAULT_TIMEOUT) -> list[Task]:
    """Fetch tasks from Good First Issue website.

    Args:
        timeout: Request timeout in seconds

    Returns:
        List of Task objects

    Raises:
        GoodFirstIssueUnavailableError: If Good First Issue is unavailable
    """
    tasks: list[Task] = []
    now = datetime.now(timezone.utc)

    with httpx.Client(timeout=timeout) as client:
        response = client.get(GOODFIRSTISSUE_URL)

        if response.status_code != 200:
            raise GoodFirstIssueUnavailableError(
                f"Good First Issue returned status {response.status_code}"
            )

        soup = BeautifulSoup(response.text, "lxml")

        # Parse issue cards (structure depends on actual site)
        # This is a basic implementation that may need adjustment
        for issue_card in soup.select(".issue, .card, article"):
            try:
                # Extract issue link
                link = issue_card.find("a", href=True)
                if not link:
                    continue

                issue_url = link.get("href", "")
                # Validate issue URL format
                if not validate_github_issue_url(issue_url):
                    continue

                # Extract title
                title = sanitize_text(link.get_text())

                # Extract project name from URL
                parsed = urlparse(issue_url)
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) < 2:
                    continue
                repo_name = f"{path_parts[0]}/{path_parts[1]}"

                # Validate the constructed repo URL
                repo_url = f"https://github.com/{repo_name}"
                if not validate_github_repo_url(repo_url):
                    continue

                # Extract stars (if available)
                stars_text = issue_card.find(class_="stars")
                stars = 0
                if stars_text:
                    match = re.search(r"(\d+)", stars_text.get_text())
                    if match:
                        stars = int(match.group(1))

                # Extract language (if available)
                lang_elem = issue_card.find(class_="language")
                language = sanitize_text(lang_elem.get_text()) if lang_elem else None

                repo = Repository(
                    name=repo_name,
                    url=repo_url,
                    stars=stars,
                    language=language,
                )

                # Parse dates
                created_at = now
                updated_at = now

                date_elem = issue_card.find(class_="created-at")
                if date_elem:
                    try:
                        created_at = datetime.fromisoformat(
                            date_elem.get_text().strip()
                        )
                    except (ValueError, TypeError):
                        pass

                age_days = max(1, (now - created_at).days)
                hotness = calculate_hotness_score(stars, age_days)

                task = Task(
                    id=f"goodfirstissue:{hash(issue_url)}",
                    title=title,
                    url=issue_url,
                    source="goodfirstissue",
                    repository=repo,
                    labels=["good first issue"],
                    created_at=created_at,
                    updated_at=updated_at,
                    hotness_score=hotness,
                    fetched_at=now,
                )
                tasks.append(task)

            except Exception:
                # Skip malformed issues
                continue

    return tasks


def fetch_and_cache_tasks(
    sources: Optional[list[str]] = None, timeout: float = DEFAULT_TIMEOUT
) -> list[Task]:
    """Fetch tasks from all sources and cache them.

    Args:
        sources: List of sources to fetch ("upforgrabs", "goodfirstissue")
        timeout: Request timeout in seconds

    Returns:
        Combined list of Task objects
    """
    sources = sources or ["upforgrabs", "goodfirstissue"]
    all_tasks: list[Task] = []

    if "upforgrabs" in sources:
        try:
            tasks = fetch_upforgrabs_tasks(timeout)
            all_tasks.extend(tasks)

            # Cache Up For Grabs tasks
            tasks_data = [t.model_dump() for t in tasks]
            write_json(UPFORGRABS_TASKS_CACHE, tasks_data)
            update_cache_metadata("upforgrabs_tasks", count=len(tasks))
        except UpForGrabsUnavailableError:
            pass

    if "goodfirstissue" in sources:
        try:
            tasks = fetch_goodfirstissue_tasks(timeout)
            all_tasks.extend(tasks)

            # Cache Good First Issue tasks
            tasks_data = [t.model_dump() for t in tasks]
            write_json(GOODFIRSTISSUE_TASKS_CACHE, tasks_data)
            update_cache_metadata("goodfirstissue_tasks", count=len(tasks))
        except GoodFirstIssueUnavailableError:
            pass

    return all_tasks


def load_cached_tasks() -> list[dict]:
    """Load cached tasks from all sources.

    Returns:
        Combined list of cached task data
    """
    tasks: list[dict] = []

    upforgrabs_data = read_json(UPFORGRABS_TASKS_CACHE)
    if upforgrabs_data:
        tasks.extend(upforgrabs_data if isinstance(upforgrabs_data, list) else [])

    goodfirstissue_data = read_json(GOODFIRSTISSUE_TASKS_CACHE)
    if goodfirstissue_data:
        tasks.extend(goodfirstissue_data if isinstance(goodfirstissue_data, list) else [])

    return tasks
