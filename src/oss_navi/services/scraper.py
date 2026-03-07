"""Task scraper for fetching open source contribution opportunities."""

import os
import random
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx
import yaml

from oss_navi.models.task import Repository, Task, calculate_hotness_score
from oss_navi.utils.cache import read_json, update_cache_metadata, write_json
from oss_navi.utils.paths import GOODFIRSTISSUES_TASKS_CACHE, UPFORGRABS_TASKS_CACHE


# Constants
UPFORGRABS_PROJECTS_API = "https://api.github.com/repos/up-for-grabs/up-for-grabs.net/contents/_data/projects"
UPFORGRABS_RAW_URL = "https://raw.githubusercontent.com/up-for-grabs/up-for-grabs.net/gh-pages/_data/projects/{}"
GOODFIRSTISSUES_API = "https://raw.githubusercontent.com/iedr/goodfirstissues/master/backend/data.json"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_ISSUES = 100  # Maximum issues to fetch per source


class UpForGrabsUnavailableError(Exception):
    """Error when Up For Grabs is unavailable."""

    pass


class GoodFirstIssueUnavailableError(Exception):
    """Error when Good First Issue is unavailable."""

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


def create_http_client(timeout: float = DEFAULT_TIMEOUT) -> httpx.Client:
    """Create an httpx client with proxy support.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Configured httpx.Client instance
    """
    proxy_settings = get_proxy_settings()
    proxies = {}

    if proxy_settings["http_proxy"]:
        proxies["http://"] = proxy_settings["http_proxy"]
    if proxy_settings["https_proxy"]:
        proxies["https://"] = proxy_settings["https_proxy"]

    return httpx.Client(timeout=timeout, proxies=proxies if proxies else None)


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

    with create_http_client(timeout=timeout) as client:
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


def fetch_goodfirstissues_tasks(timeout: float = 60.0, max_issues: int = DEFAULT_MAX_ISSUES) -> list[Task]:
    """Fetch tasks from Good First Issues (goodfirstissues.com).

    This source provides individual issue URLs via a JSON API.
    Note: The JSON file is ~1.1MB, so a longer timeout is needed.

    Args:
        timeout: Request timeout in seconds (default: 60.0 for large file)
        max_issues: Maximum number of issues to fetch

    Returns:
        List of Task objects

    Raises:
        GoodFirstIssueUnavailableError: If Good First Issues is unavailable
    """
    tasks: list[Task] = []
    now = datetime.now(timezone.utc)

    with create_http_client(timeout=timeout) as client:
        try:
            response = client.get(GOODFIRSTISSUES_API)

            if response.status_code != 200:
                raise GoodFirstIssueUnavailableError(
                    f"Good First Issues returned status {response.status_code}"
                )

            data = response.json()

            if not isinstance(data, list):
                raise GoodFirstIssueUnavailableError(
                    "Unexpected response format from Good First Issues API"
                )

        except httpx.RequestError as e:
            raise GoodFirstIssueUnavailableError(f"Failed to fetch Good First Issues: {e}")

        # Randomize the order for variety
        random.shuffle(data)

        for issue_data in data[:max_issues]:
            try:
                issue = issue_data.get("Issue", {})
                issue_url = issue.get("issue_url", "")

                if not validate_github_issue_url(issue_url):
                    continue

                # Extract issue info
                title = sanitize_text(issue.get("issue_title", ""))
                created_at_str = issue.get("issue_createdAt", "")

                try:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    created_at = now

                # Extract repo info
                repo_data = issue.get("issue_repo", {})
                repo_name_full = repo_data.get("repo_name", "")
                owner_data = repo_data.get("Owner", {})
                owner = owner_data.get("repo_owner", "")

                if owner and repo_name_full:
                    repo_name = f"{owner}/{repo_name_full}"
                else:
                    # Parse from URL
                    parsed = urlparse(issue_url)
                    path_parts = parsed.path.strip("/").split("/")
                    if len(path_parts) >= 2:
                        repo_name = f"{path_parts[0]}/{path_parts[1]}"
                    else:
                        continue

                repo_url = f"https://github.com/{repo_name}"
                stars = repo_data.get("repo_stars", 0) or 0

                # Extract languages
                langs_data = repo_data.get("repo_langs", {}).get("Nodes", [])
                languages = [node.get("repo_prog_language", "") for node in langs_data if node.get("repo_prog_language")]
                primary_language = languages[0] if languages else None

                repo = Repository(
                    name=repo_name,
                    url=repo_url,
                    stars=stars,
                    language=primary_language,
                    topics=languages,
                )

                # Extract labels
                labels_data = issue.get("issue_labels", {}).get("Nodes", [])
                labels = [node.get("label_name", "") for node in labels_data if node.get("label_name")]

                age_days = max(1, (now - created_at).days)
                hotness = calculate_hotness_score(stars, age_days)

                task = Task(
                    id=f"goodfirstissues:{hash(issue_url)}",
                    title=title,
                    url=issue_url,
                    source="goodfirstissues",
                    repository=repo,
                    labels=labels,
                    created_at=created_at,
                    updated_at=created_at,
                    hotness_score=hotness,
                    fetched_at=now,
                )
                tasks.append(task)

            except Exception:
                # Skip malformed issues
                continue

    return tasks


def filter_tasks_by_tags(tasks: list[Task], preferred_tags: list[str], min_match: int = 1) -> list[Task]:
    """Filter tasks by matching tags/languages.

    Args:
        tasks: List of tasks to filter
        preferred_tags: List of preferred languages/tags (e.g., ["Python", "TypeScript"])
        min_match: Minimum number of tag matches required (default: 1)

    Returns:
        Filtered list of tasks
    """
    if not preferred_tags:
        return tasks

    # Normalize tags for matching
    preferred_lower = {tag.lower() for tag in preferred_tags}

    matching_tasks = []
    for task in tasks:
        task_tags = set()

        # Add repository language
        if task.repository.language:
            task_tags.add(task.repository.language.lower())

        # Add repository topics
        if task.repository.topics:
            for topic in task.repository.topics:
                task_tags.add(topic.lower())

        # Check for matches
        matches = len(task_tags & preferred_lower)
        if matches >= min_match:
            matching_tasks.append(task)

    return matching_tasks


def select_diverse_tasks(tasks: list[Task], count: int = 20, strategy: str = "random") -> list[Task]:
    """Select a diverse set of tasks using different strategies.

    Args:
        tasks: List of tasks to select from
        count: Number of tasks to select
        strategy: Selection strategy ("random", "top", "diverse")

    Returns:
        Selected tasks
    """
    if len(tasks) <= count:
        return tasks

    if strategy == "random":
        # Pure random selection
        return random.sample(tasks, count)

    elif strategy == "top":
        # Select top tasks by hotness score
        sorted_tasks = sorted(tasks, key=lambda t: t.hotness_score, reverse=True)
        return sorted_tasks[:count]

    elif strategy == "diverse":
        # Select diverse tasks across languages and sources
        selected = []
        languages_seen = set()
        sources_seen = set()

        # First pass: prioritize diversity
        for task in tasks:
            if len(selected) >= count:
                break

            lang = task.repository.language
            source = task.source

            # Prefer tasks with new languages or sources
            is_new_lang = lang and lang.lower() not in languages_seen
            is_new_source = source not in sources_seen

            if is_new_lang or is_new_source:
                selected.append(task)
                if lang:
                    languages_seen.add(lang.lower())
                sources_seen.add(source)

        # Second pass: fill remaining slots with random selection
        remaining = [t for t in tasks if t not in selected]
        remaining_count = count - len(selected)
        if remaining_count > 0 and remaining:
            selected.extend(random.sample(remaining, min(remaining_count, len(remaining))))

        return selected

    # Default to random
    return random.sample(tasks, count)


def search_tasks(
    tasks: list[Task],
    preferred_languages: Optional[list[str]] = None,
    min_stars: int = 0,
    max_age_days: int = 90,
    limit: int = 20,
    strategy: str = "diverse",
) -> list[Task]:
    """Search and filter tasks based on criteria.

    Args:
        tasks: List of tasks to search
        preferred_languages: Optional list of preferred languages
        min_stars: Minimum repository stars
        max_age_days: Maximum issue age in days
        limit: Maximum number of results
        strategy: Selection strategy ("random", "top", "diverse")

    Returns:
        Filtered and selected tasks
    """
    now = datetime.now(timezone.utc)

    # Filter by stars
    filtered = [t for t in tasks if t.repository.stars >= min_stars]

    # Filter by age
    cutoff = now - __import__("datetime").timedelta(days=max_age_days)
    filtered = [t for t in filtered if t.created_at >= cutoff]

    # Filter by languages if specified
    if preferred_languages:
        filtered = filter_tasks_by_tags(filtered, preferred_languages, min_match=1)

    # Select using strategy
    return select_diverse_tasks(filtered, count=limit, strategy=strategy)


def fetch_and_cache_tasks(
    sources: Optional[list[str]] = None, timeout: float = DEFAULT_TIMEOUT
) -> list[Task]:
    """Fetch tasks from all sources and cache them.

    Args:
        sources: List of sources to fetch ("upforgrabs", "goodfirstissues")
        timeout: Request timeout in seconds

    Returns:
        Combined list of Task objects
    """
    sources = sources or ["upforgrabs", "goodfirstissues"]
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

    if "goodfirstissues" in sources:
        try:
            tasks = fetch_goodfirstissues_tasks(timeout)
            all_tasks.extend(tasks)

            # Cache Good First Issues tasks
            tasks_data = [t.model_dump() for t in tasks]
            write_json(GOODFIRSTISSUES_TASKS_CACHE, tasks_data)
            update_cache_metadata("goodfirstissues_tasks", count=len(tasks))
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

    goodfirstissues_data = read_json(GOODFIRSTISSUES_TASKS_CACHE)
    if goodfirstissues_data:
        tasks.extend(goodfirstissues_data if isinstance(goodfirstissues_data, list) else [])

    return tasks
