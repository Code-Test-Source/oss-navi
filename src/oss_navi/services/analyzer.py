"""Analysis service for generating personalized OSS recommendations."""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oss_navi.models.memory import LongTermMemory, PastRecommendation, SkillSnapshot
from oss_navi.models.report import AnalysisReport
from oss_navi.models.task import (
    GreatProject,
    IssueStatus,
    RatingBreakdown,
    Recommendation,
    Task,
    calculate_hotness_score,
)
from oss_navi.services.github import GitHubClient
from oss_navi.utils.cache import read_json, write_json
from oss_navi.utils.paths import MEMORY_FILE, TEMP_DIR


# Constants
CLAUDE_CODE_COMMAND = "claude"
DEFAULT_TIMEOUT_SECONDS = 60

# Field adjacency mapping for suggestions
ADJACENT_FIELDS = {
    "Python": ["web development", "data science", "automation", "DevOps", "machine learning"],
    "JavaScript": ["web development", "frontend development", "Node.js", "React", "Vue.js"],
    "TypeScript": ["web development", "frontend development", "Node.js", "Angular", "React"],
    "Rust": ["systems programming", "web assembly", "embedded systems", "CLI tools"],
    "Go": ["systems programming", "cloud infrastructure", "microservices", "DevOps"],
    "Java": ["enterprise development", "Android", "microservices", "Spring"],
    "C++": ["systems programming", "game development", "embedded systems", "performance optimization"],
    "C": ["systems programming", "embedded systems", "operating systems", "compilers"],
}


class ClaudeCodeError(Exception):
    """Error from Claude Code invocation."""

    pass


def filter_tasks_by_stars(tasks: list[Task], min_stars: int = 50) -> list[Task]:
    """Filter tasks by minimum star count.

    Args:
        tasks: List of tasks to filter
        min_stars: Minimum number of stars (default: 50)

    Returns:
        Filtered list of tasks
    """
    return [t for t in tasks if t.repository.stars >= min_stars]


def filter_tasks_by_recency(tasks: list[Task], max_age_days: int = 90) -> list[Task]:
    """Filter tasks by recency (maximum age in days).

    Args:
        tasks: List of tasks to filter
        max_age_days: Maximum age of issues in days (default: 90)

    Returns:
        Filtered list of tasks
    """
    now = datetime.now(timezone.utc)
    cutoff = now - __import__("datetime").timedelta(days=max_age_days)

    return [t for t in tasks if t.created_at >= cutoff]


def sort_tasks_by_hotness(tasks: list[Task]) -> list[Task]:
    """Sort tasks by hotness score (highest first).

    Args:
        tasks: List of tasks to sort

    Returns:
        Sorted list of tasks (highest hotness first)
    """
    return sorted(tasks, key=lambda t: t.hotness_score, reverse=True)


def build_prompt(
    profile: dict,
    tasks: list[Task],
    learning_focus: Optional[str] = None,
    memory: Optional[dict] = None,
) -> str:
    """Build the analysis prompt for Claude Code.

    Args:
        profile: User's GitHub profile data
        tasks: List of filtered tasks
        learning_focus: Optional learning focus from --learn flag
        memory: Optional long-term memory data

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "# OSS-Navi Analysis Request",
        "",
        "You are an expert open source advisor. Analyze the following data and generate a personalized Markdown report.",
        "",
        "## User Profile",
        f"- **Username**: {profile.get('username', 'unknown')}",
        f"- **Public Repos**: {profile.get('public_repos', 0)}",
        f"- **Languages**: {', '.join(f'{k} ({v:.0%})' for k, v in profile.get('languages', {}).items())}",
    ]

    if learning_focus:
        prompt_parts.extend([
            "",
            f"## Learning Focus: {learning_focus}",
            "The user is currently learning this technology. Prioritize projects that match this focus.",
        ])

    prompt_parts.extend([
        "",
        "## Available Tasks",
        "Here are beginner-friendly issues from popular repositories:",
        "",
    ])

    for i, task in enumerate(tasks[:20], 1):  # Limit to top 20 tasks
        prompt_parts.extend([
            f"### {i}. {task.title}",
            f"- **Repository**: {task.repository.name} (⭐ {task.repository.stars})",
            f"- **Language**: {task.repository.language or 'Unknown'}",
            f"- **URL**: {task.url}",
            f"- **Hotness Score**: {task.hotness_score}",
            "",
        ])

    if memory:
        prompt_parts.extend([
            "## Past Recommendations",
            "The user has previously been recommended these projects:",
            "",
        ])
        for rec in memory.get("past_recommendations", [])[:5]:
            prompt_parts.append(f"- {rec.get('project', 'unknown')}")

    prompt_parts.extend([
        "",
        "## Required Output Format",
        "",
        "Generate a Markdown report with these sections:",
        "",
        "### 1. Skill Assessment",
        "Analyze the user's current skills based on their profile.",
        "",
        "### 2. Learning Direction",
        "Suggest learning paths based on their profile and stated focus.",
        "",
        "### 3. Top 1-2 Recommendations",
        "Recommend 1-2 projects with:",
        "- Project name and description",
        "- Why it's a good fit",
        "- Code reading hints (files to start with)",
        "",
        "### 4. Long-term Memory Update",
        "A brief note to add to the user's memory for future sessions.",
    ])

    return "\n".join(prompt_parts)


def invoke_claude_code(prompt: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    """Invoke Claude Code as a subprocess to generate analysis.

    Args:
        prompt: The prompt to send to Claude Code
        timeout: Maximum time to wait (default: 60 seconds per FR-039)

    Returns:
        Claude Code's output (Markdown report)

    Raises:
        ClaudeCodeError: If Claude Code fails or times out
    """
    try:
        result = subprocess.run(
            [CLAUDE_CODE_COMMAND, "--print", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "Unknown error"
            raise ClaudeCodeError(f"Claude Code failed: {error_msg}")

        return result.stdout

    except subprocess.TimeoutExpired:
        raise ClaudeCodeError(
            f"Claude Code timed out after {timeout} seconds. "
            "Try again or reduce the scope of analysis."
        )
    except FileNotFoundError:
        raise ClaudeCodeError(
            "Claude Code not found in PATH. "
            "Please install Claude Code: https://claude.ai/code"
        )


def save_report(content: str, report_id: str) -> str:
    """Save the report to the temp directory.

    Args:
        content: Markdown content of the report
        report_id: Unique report identifier

    Returns:
        Path to the saved report file
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    file_path = TEMP_DIR / "current_report.md"

    file_path.write_text(content, encoding="utf-8")

    return str(file_path)


def parse_memory_update(content: str) -> Optional[str]:
    """Parse the Long-term Memory Update section from Claude Code output.

    Args:
        content: Markdown content from Claude Code

    Returns:
        Extracted memory update text, or None if not found
    """
    # Pattern to match "### 4. Long-term Memory Update" section
    # Matches the heading and captures content until the next heading or end
    pattern = r"###\s*4\.\s*Long[-\s]*term\s+Memory\s+Update\s*\n+(.*?)(?=\n#{2,3}|\Z)"

    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
    if match:
        update_text = match.group(1).strip()
        # Clean up the text - remove leading/trailing whitespace
        # Return None if the text is empty or just whitespace
        if update_text and not update_text.startswith("#"):
            return update_text

    return None


def parse_recommendations_from_report(content: str) -> list[PastRecommendation]:
    """Parse project recommendations from Claude Code output.

    Args:
        content: Markdown content from Claude Code

    Returns:
        List of PastRecommendation objects
    """
    recommendations = []
    now = datetime.now(timezone.utc)

    # Pattern to match GitHub URLs in recommendation sections
    # Look for project mentions in "Top 1-2 Recommendations" section
    rec_section_pattern = r"###\s*3\.\s*Top\s+\d+-\d+\s+Recommendations?\s*\n+(.*?)(?=\n###|\n##|\Z)"
    rec_match = re.search(rec_section_pattern, content, re.IGNORECASE | re.DOTALL)

    if rec_match:
        rec_section = rec_match.group(1)

        # Find GitHub URLs in the recommendations section
        url_pattern = r"https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)/issues/(\d+)"
        for match in re.finditer(url_pattern, rec_section):
            owner, repo, issue_num = match.groups()
            project = f"{owner}/{repo}"
            issue_url = match.group(0)

            # Check if we already have this recommendation
            if not any(r.project == project and r.issue_url == issue_url for r in recommendations):
                recommendations.append(PastRecommendation(
                    date=now,
                    project=project,
                    issue_url=issue_url,
                    status="viewed",
                ))

            if len(recommendations) >= 2:
                break

    return recommendations


def update_memory_from_report(
    content: str,
    learning_focus: Optional[str] = None,
) -> Optional[LongTermMemory]:
    """Update long-term memory based on Claude Code analysis output.

    Args:
        content: Markdown content from Claude Code
        learning_focus: Optional learning focus from --learn flag

    Returns:
        Updated LongTermMemory object, or None if no updates
    """
    from oss_navi.utils.cache import read_json, write_json

    # Load existing memory or create new
    memory_data = read_json(MEMORY_FILE)
    if memory_data:
        memory = LongTermMemory(**memory_data)
    else:
        memory = LongTermMemory()

    updated = False

    # Parse and add memory update
    memory_update = parse_memory_update(content)
    if memory_update:
        # Store the update in learning_goals if it's new
        if memory_update not in memory.learning_goals:
            memory.learning_goals.append(memory_update)
            updated = True

    # Parse and add recommendations
    recommendations = parse_recommendations_from_report(content)
    for rec in recommendations:
        # Only add if not already in past_recommendations
        if not any(r.issue_url == rec.issue_url for r in memory.past_recommendations):
            memory.past_recommendations.append(rec)
            updated = True

    # Add learning focus if provided
    if learning_focus and learning_focus not in memory.learning_goals:
        memory.learning_goals.append(learning_focus)
        updated = True

    # Add skill snapshot (once per day max)
    now = datetime.now(timezone.utc)
    today = now.date()
    if not any(s.date.date() == today for s in memory.skill_history):
        # Extract skills from the content if possible
        # This is a simple heuristic - could be enhanced
        snapshot = SkillSnapshot(
            date=now,
            focus_areas=[learning_focus] if learning_focus else [],
        )
        memory.skill_history.append(snapshot)
        updated = True

    if updated:
        memory.updated_at = now
        write_json(MEMORY_FILE, memory.model_dump())
        return memory

    return None


def run_analysis(
    profile: dict,
    tasks: list[Task],
    learning_focus: Optional[str] = None,
    memory: Optional[dict] = None,
    min_stars: int = 50,
    max_age_days: int = 90,
) -> AnalysisReport:
    """Run the full analysis pipeline.

    Args:
        profile: User's GitHub profile data
        tasks: List of available tasks
        learning_focus: Optional learning focus
        memory: Optional long-term memory
        min_stars: Minimum stars filter (default: 50 per FR-006)
        max_age_days: Maximum issue age filter (default: 90 per FR-007)

    Returns:
        AnalysisReport with the generated content
    """
    # Filter and sort tasks
    filtered_tasks = filter_tasks_by_stars(tasks, min_stars)
    filtered_tasks = filter_tasks_by_recency(filtered_tasks, max_age_days)
    filtered_tasks = sort_tasks_by_hotness(filtered_tasks)

    if not filtered_tasks:
        raise ValueError(
            "No matching tasks found. Try broadening your filters "
            "(lower --min-stars or increase --max-age)."
        )

    # Build prompt
    prompt = build_prompt(profile, filtered_tasks, learning_focus, memory)

    # Invoke Claude Code
    content = invoke_claude_code(prompt, timeout=DEFAULT_TIMEOUT_SECONDS)

    # Generate report ID and save
    report_id = AnalysisReport.generate_report_id()
    file_path = save_report(content, report_id)

    # Extract recommended projects from content (simple heuristic)
    recommended = []
    for line in content.split("\n"):
        if "github.com/" in line and "/" in line:
            parts = line.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                project = f"{parts[0]}/{parts[1].split()[0].rstrip(')')}"
                if project not in recommended:
                    recommended.append(project)
                    if len(recommended) >= 2:
                        break

    return AnalysisReport(
        id=report_id,
        created_at=datetime.now(timezone.utc),
        content=content,
        file_path=file_path,
        learning_focus=learning_focus,
        recommended_projects=recommended[:2],
    )


def run_analysis_with_memory_update(
    profile: dict,
    tasks: list[Task],
    learning_focus: Optional[str] = None,
    memory: Optional[dict] = None,
    min_stars: int = 50,
    max_age_days: int = 90,
) -> AnalysisReport:
    """Run analysis and update long-term memory.

    This is a convenience function that runs analysis and automatically
    updates memory based on the results.

    Args:
        profile: User's GitHub profile data
        tasks: List of available tasks
        learning_focus: Optional learning focus
        memory: Optional long-term memory
        min_stars: Minimum stars filter (default: 50)
        max_age_days: Maximum issue age filter (default: 90)

    Returns:
        AnalysisReport with the generated content
    """
    report = run_analysis(
        profile=profile,
        tasks=tasks,
        learning_focus=learning_focus,
        memory=memory,
        min_stars=min_stars,
        max_age_days=max_age_days,
    )

    # Update memory based on the report content
    update_memory_from_report(report.content, learning_focus)

    return report


def calculate_rating_breakdown(
    task: Task,
    user_languages: dict[str, float],
    learning_focus: Optional[str] = None,
    issue_status: Optional[IssueStatus] = None,
) -> RatingBreakdown:
    """Calculate rating breakdown for a task recommendation.

    Weights: language_match (30%), hotness (20%), availability (15%),
    learning (15%), skill (10%), topic (10%)

    Args:
        task: The task to rate
        user_languages: User's language distribution (e.g., {"Python": 0.7})
        learning_focus: What the user wants to learn
        issue_status: Current status of the issue

    Returns:
        RatingBreakdown with detailed scores
    """
    # Language match (0-10)
    task_language = task.repository.language or ""
    language_match = 0.0
    for lang, pct in user_languages.items():
        if lang.lower() == task_language.lower():
            language_match = pct * 10  # Scale percentage to 0-10
            break
    # Partial match for related languages
    if language_match == 0:
        # Check for partial matches (e.g., JS/TS)
        related = {"javascript": ["typescript"], "typescript": ["javascript"]}
        for lang in user_languages:
            if lang.lower() in related.get(task_language.lower(), []):
                language_match = 3.0
                break

    # Hotness score (0-10) - normalize from raw score
    # Most hotness scores are 0-100, normalize to 0-10
    raw_hotness = min(task.hotness_score, 100)  # Cap at 100
    hotness_score = raw_hotness / 10.0

    # Issue availability (0-10)
    issue_availability = 10.0  # Default to available
    if issue_status:
        if issue_status.is_assigned or issue_status.is_closed or issue_status.has_linked_pr:
            issue_availability = 0.0
        elif issue_status.in_progress_labels:
            issue_availability = 5.0  # Partially available

    # Learning alignment (0-10)
    learning_alignment = 5.0  # Default neutral
    if learning_focus:
        focus_lower = learning_focus.lower()
        if task_language.lower() in focus_lower or focus_lower in task_language.lower():
            learning_alignment = 10.0
        elif any(topic.lower() in focus_lower for topic in task.repository.topics):
            learning_alignment = 8.0
        # Check labels for learning hints
        for label in task.labels:
            if focus_lower in label.lower():
                learning_alignment = max(learning_alignment, 7.0)

    # Skill level fit (0-10) - based on labels and user experience
    skill_level_fit = 7.0  # Default good fit
    beginner_labels = {"good first issue", "beginner", "help wanted", "starter"}
    if any(label.lower() in beginner_labels for label in task.labels):
        skill_level_fit = 9.0  # Good for beginners

    # Topic relevance (0-10)
    topic_relevance = 5.0
    if task.repository.topics:
        # Check if topics align with user languages
        for topic in task.repository.topics:
            for lang in user_languages:
                if lang.lower() in topic.lower():
                    topic_relevance = max(topic_relevance, 8.0)

    return RatingBreakdown(
        language_match=language_match,
        hotness_score=hotness_score,
        issue_availability=issue_availability,
        learning_alignment=learning_alignment,
        skill_level_fit=skill_level_fit,
        topic_relevance=topic_relevance,
    )


def check_issue_status(owner: str, repo: str, issue_number: int, token: Optional[str] = None) -> IssueStatus:
    """Check status of an issue using GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        token: Optional GitHub token

    Returns:
        IssueStatus with availability info
    """
    client = GitHubClient(token=token)
    return client.check_issue_status(owner, repo, issue_number)


def generate_recommendations(
    tasks: list[Task],
    user_languages: dict[str, float],
    learning_focus: Optional[str] = None,
    count: int = 7,
    token: Optional[str] = None,
) -> list[Recommendation]:
    """Generate scored recommendations from tasks.

    Args:
        tasks: List of available tasks
        user_languages: User's language distribution
        learning_focus: What the user wants to learn
        count: Number of recommendations (5-10)
        token: Optional GitHub token for status checks

    Returns:
        List of scored recommendations sorted by rating
    """
    count = max(5, min(10, count))  # Ensure 5-10 range
    recommendations = []

    # Score all tasks
    scored_tasks = []
    for task in tasks:
        # Check issue status
        import re
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", task.url)
        issue_status = None
        if match:
            owner, repo, issue_num = match.groups()
            issue_status = check_issue_status(owner, repo, int(issue_num), token)

        breakdown = calculate_rating_breakdown(
            task=task,
            user_languages=user_languages,
            learning_focus=learning_focus,
            issue_status=issue_status,
        )

        scored_tasks.append((task, breakdown, issue_status))

    # Sort by weighted total (descending)
    scored_tasks.sort(key=lambda x: x[1].weighted_total, reverse=True)

    # Take top 'count' tasks
    for task, breakdown, issue_status in scored_tasks[:count]:
        if issue_status is None:
            issue_status = IssueStatus(
                issue_url=task.url,
                is_assigned=False,
                is_closed=False,
                has_linked_pr=False,
                checked_at=datetime.now(timezone.utc),
            )

        reason = generate_recommendation_reason(
            task=task,
            user_languages=user_languages,
            learning_focus=learning_focus,
        )

        recommendation = Recommendation(
            task=task,
            rating=breakdown.weighted_total,
            rating_breakdown=breakdown,
            reason=reason,
            code_analysis=f"This {task.repository.language or 'project'} project has {task.repository.stars} stars and focuses on {', '.join(task.repository.topics[:3]) or 'open source contributions'}.",
            status=issue_status,
        )
        recommendations.append(recommendation)

    return recommendations


def generate_recommendation_reason(
    task: Task,
    user_languages: dict[str, float],
    learning_focus: Optional[str] = None,
) -> str:
    """Generate a personalized reason for recommending this task.

    Args:
        task: The recommended task
        user_languages: User's language distribution
        learning_focus: What the user wants to learn

    Returns:
        Human-readable reason string
    """
    reasons = []

    # Language match
    task_lang = task.repository.language
    if task_lang:
        for lang in user_languages:
            if lang.lower() == task_lang.lower():
                reasons.append(f"matches your {lang} expertise")
                break

    # Learning focus
    if learning_focus:
        if task_lang and learning_focus.lower() in task_lang.lower():
            reasons.append(f"aligns with your learning goal of {learning_focus}")
        for topic in task.repository.topics:
            if learning_focus.lower() in topic.lower():
                reasons.append(f"involves {topic} which relates to {learning_focus}")
                break

    # Project popularity
    if task.repository.stars >= 1000:
        reasons.append("popular and well-maintained project")
    elif task.repository.stars >= 100:
        reasons.append("active community project")

    # Beginner friendly
    beginner_labels = {"good first issue", "beginner", "starter", "help wanted"}
    if any(label.lower() in beginner_labels for label in task.labels):
        reasons.append("beginner-friendly with clear scope")

    if not reasons:
        reasons.append("good opportunity for open source contribution")

    return f"This issue {' and '.join(reasons[:3])}."


def suggest_adjacent_fields(
    current_interest: str,
    user_languages: dict[str, float],
) -> list[str]:
    """Suggest adjacent fields to explore based on user's interests.

    Args:
        current_interest: What the user is currently learning
        user_languages: User's language distribution

    Returns:
        List of suggested fields to explore
    """
    suggestions = []

    # Look up suggestions for known languages
    interest_lower = current_interest.lower()
    for lang, fields in ADJACENT_FIELDS.items():
        if lang.lower() == interest_lower or interest_lower in lang.lower():
            suggestions.extend(fields[:3])
            break

    # If no exact match, suggest based on user languages
    if not suggestions:
        for lang in user_languages:
            if lang in ADJACENT_FIELDS:
                suggestions.extend(ADJACENT_FIELDS[lang][:2])

    # Deduplicate and limit
    seen = set()
    unique = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique[:4]  # Return 2-4 suggestions


# Great project architecture patterns by language
ARCHITECTURE_PATTERNS = {
    "Python": {
        "patterns": ["object-oriented design", "decorators", "context managers", "async/await", "type hints"],
        "common_structure": "src/ layout with __init__.py modules",
    },
    "JavaScript": {
        "patterns": ["modules", "promises/async", "event-driven", "functional", "prototypal inheritance"],
        "common_structure": "src/ with index.js entry points",
    },
    "TypeScript": {
        "patterns": ["interfaces", "generics", "decorators", "modules", "type guards"],
        "common_structure": "src/ with tsconfig.json configuration",
    },
    "Go": {
        "patterns": ["interfaces", "goroutines", "channels", "error handling", "package-oriented design"],
        "common_structure": "cmd/ and pkg/ directories",
    },
    "Rust": {
        "patterns": ["traits", "ownership/borrowing", "error handling", "modules", "macros"],
        "common_structure": "src/ with Cargo.toml configuration",
    },
}

# Great projects cache file
GREAT_PROJECTS_CACHE_KEY = "great_projects_cache"


def find_great_projects(
    user_languages: dict[str, float],
    learning_focus: Optional[str] = None,
    count: int = 3,
    token: Optional[str] = None,
) -> list[GreatProject]:
    """Find great open source projects for learning (not necessarily beginner-friendly).

    Uses GitHub search API to find high-quality projects that match user skills.
    Projects are selected for educational value, not ease of contribution.

    Args:
        user_languages: User's language distribution
        learning_focus: What the user wants to learn
        count: Number of projects to return (default 3)
        token: Optional GitHub token for API access

    Returns:
        List of GreatProject objects with architecture analysis
    """
    # Check cache first
    cache_data = read_json(TEMP_DIR / "great_projects_cache.json")
    cache_key = f"{','.join(sorted(user_languages.keys()))}_{learning_focus}"
    if cache_data and cache_key in cache_data:
        cached = cache_data[cache_key]
        if cached:
            # Check if cache is still valid (24 hours)
            from datetime import timedelta
            cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now(timezone.utc) - cached_time < timedelta(hours=24):
                return [GreatProject(**p) for p in cached.get("projects", [])[:count]]

    # Determine primary language to search
    primary_lang = max(user_languages.keys(), key=lambda k: user_languages[k])
    if learning_focus:
        # Check if learning focus matches a known language
        for lang in user_languages:
            if learning_focus.lower() in lang.lower() or lang.lower() in learning_focus.lower():
                primary_lang = lang
                break

    # Search for popular repositories in that language
    client = GitHubClient(token=token)
    projects: list[GreatProject] = []

    # Build search queries for great projects (high stars, not beginner-focused)
    # We want projects with significant stars that demonstrate good patterns
    queries = [
        f"language:{primary_lang} stars:>1000 archived:false",
    ]

    if learning_focus:
        # Add topic-based search
        queries.insert(0, f"topic:{learning_focus.lower().replace(' ', '-')} stars:>500 archived:false")

    seen_repos: set[str] = set()

    for query in queries:
        if len(projects) >= count:
            break

        try:
            # Use GitHub search API
            results = client.search_repositories(query, sort="stars", per_page=min(count * 2, 10))

            for repo in results:
                if len(projects) >= count:
                    break

                repo_name = repo.get("full_name", "")
                if repo_name in seen_repos:
                    continue
                seen_repos.add(repo_name)

                # Skip repos that are primarily for beginners
                topics = repo.get("topics", [])
                if any(t in topics for t in ["good-first-issue", "beginner-friendly", "hacktoberfest"]):
                    continue

                # Analyze the project
                architecture = analyze_project_architecture(
                    repo_url=repo.get("html_url", ""),
                    language=repo.get("language", primary_lang),
                )

                project = GreatProject(
                    name=repo_name,
                    url=repo.get("html_url", ""),
                    stars=repo.get("stargazers_count", 0),
                    language=repo.get("language", primary_lang),
                    why_great=_generate_why_great(repo, learning_focus),
                    architecture_overview=architecture if isinstance(architecture, str) else architecture.get("overview", "Well-structured project with clear organization."),
                    key_patterns=_extract_key_patterns(repo.get("language", primary_lang), topics),
                    contribution_areas=_suggest_contribution_areas(repo, topics),
                    relevance_reason=_generate_relevance_reason(repo, user_languages, learning_focus),
                )
                projects.append(project)

        except Exception:
            # Continue with next query if one fails
            continue

    # Cache results
    try:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = TEMP_DIR / "great_projects_cache.json"
        existing_cache = read_json(cache_file) or {}
        existing_cache[cache_key] = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "projects": [p.model_dump() for p in projects],
        }
        write_json(cache_file, existing_cache)
    except Exception:
        pass  # Cache failure is not critical

    return projects[:count]


def analyze_project_architecture(
    repo_url: str,
    language: str,
) -> str | dict:
    """Analyze a project's architecture based on its URL and language.

    Provides a brief architecture overview for learning purposes.

    Args:
        repo_url: GitHub repository URL
        language: Primary language of the repository

    Returns:
        Architecture overview string or dict with analysis
    """
    if not repo_url or not repo_url.startswith("https://github.com/"):
        return ""

    # Extract repo name from URL
    parts = repo_url.rstrip("/").split("/")
    repo_name = parts[-1] if len(parts) >= 5 else "project"

    # Get language-specific patterns
    lang_patterns = ARCHITECTURE_PATTERNS.get(language, ARCHITECTURE_PATTERNS.get("Python", {}))

    # Generate architecture overview based on language and common patterns
    overview_parts = [
        f"**{repo_name}** is a {language} project.",
    ]

    # Add language-specific insights
    if language == "Python":
        overview_parts.extend([
            "Typically uses a `src/` layout with Python modules.",
            "Look for `pyproject.toml` or `setup.py` for project configuration.",
            "Key patterns: " + ", ".join(lang_patterns.get("patterns", ["clean code"])[:3]) + ".",
        ])
    elif language == "JavaScript":
        overview_parts.extend([
            "Common structure includes `src/` directory with modular components.",
            "Check `package.json` for scripts and dependencies.",
            "Key patterns: " + ", ".join(lang_patterns.get("patterns", ["modules"])[:3]) + ".",
        ])
    elif language == "TypeScript":
        overview_parts.extend([
            "Uses TypeScript for type safety with `tsconfig.json` configuration.",
            "Look for interface definitions and type exports.",
            "Key patterns: " + ", ".join(lang_patterns.get("patterns", ["interfaces", "generics"])[:3]) + ".",
        ])
    elif language == "Go":
        overview_parts.extend([
            "Follows Go conventions with `cmd/` and `pkg/` directories.",
            "Look for interface definitions and package structure.",
            "Key patterns: " + ", ".join(lang_patterns.get("patterns", ["interfaces", "goroutines"])[:3]) + ".",
        ])
    elif language == "Rust":
        overview_parts.extend([
            "Uses Cargo for package management with `Cargo.toml`.",
            "Look for trait definitions and module organization.",
            "Key patterns: " + ", ".join(lang_patterns.get("patterns", ["traits", "ownership"])[:3]) + ".",
        ])
    else:
        overview_parts.append("Exhibits idiomatic " + language + " patterns and conventions.")

    return " ".join(overview_parts)


def _generate_why_great(repo: dict, learning_focus: Optional[str]) -> str:
    """Generate a reason why this project is great to study."""
    reasons = []
    stars = repo.get("stargazers_count", 0)
    description = repo.get("description", "")
    topics = repo.get("topics", [])

    if stars >= 10000:
        reasons.append("Highly popular with strong community")
    elif stars >= 1000:
        reasons.append("Well-established project with active development")

    if topics:
        relevant_topics = [t for t in topics if t not in ["awesome-list", "hacktoberfest"]]
        if relevant_topics:
            reasons.append(f"Focuses on {relevant_topics[0].replace('-', ' ')}")

    if learning_focus:
        reasons.append(f"Excellent for learning {learning_focus}")

    if not reasons:
        reasons.append("Demonstrates professional-quality code")

    return ". ".join(reasons[:2]) + "."


def _extract_key_patterns(language: str, topics: list[str]) -> list[str]:
    """Extract key patterns the project likely demonstrates."""
    patterns = []

    lang_patterns = ARCHITECTURE_PATTERNS.get(language, {})
    default_patterns = lang_patterns.get("patterns", ["clean architecture", "modular design"])

    # Add language-specific patterns
    patterns.extend(default_patterns[:2])

    # Add topic-based patterns
    topic_to_pattern = {
        "api": "REST API design",
        "web": "web development patterns",
        "cli": "CLI architecture",
        "testing": "test-driven development",
        "documentation": "documentation practices",
        "async": "asynchronous programming",
        "microservices": "microservices architecture",
    }

    for topic in topics:
        pattern = topic_to_pattern.get(topic.lower())
        if pattern and pattern not in patterns:
            patterns.append(pattern)

    return patterns[:4]


def _suggest_contribution_areas(repo: dict, topics: list[str]) -> list[str]:
    """Suggest areas where contributions could add value."""
    areas = []
    description = repo.get("description", "").lower()

    # Generic contribution areas
    areas.append("documentation improvements")

    # Topic-based suggestions
    if "api" in topics or "api" in description:
        areas.append("API endpoint testing")
    if "web" in topics:
        areas.append("frontend components")
    if "cli" in topics:
        areas.append("command implementations")
    if any(t in topics for t in ["testing", "test"]):
        areas.append("test coverage expansion")
    if "docs" in topics or "documentation" in description:
        areas.append("example tutorials")

    # Always add at least code review
    if "code review" not in areas:
        areas.append("code review and feedback")

    return areas[:3]


def _generate_relevance_reason(
    repo: dict,
    user_languages: dict[str, float],
    learning_focus: Optional[str],
) -> str:
    """Generate why this project is relevant to the user."""
    reasons = []
    repo_lang = repo.get("language", "")
    topics = repo.get("topics", [])

    # Language match
    for lang, pct in user_languages.items():
        if lang.lower() == repo_lang.lower():
            reasons.append(f"matches your {lang} expertise ({pct:.0%})")
            break

    # Learning focus match
    if learning_focus:
        focus_lower = learning_focus.lower()
        if repo_lang.lower() in focus_lower or focus_lower in repo_lang.lower():
            reasons.append(f"aligns with your learning goal of {learning_focus}")
        for topic in topics:
            if focus_lower in topic.lower():
                reasons.append(f"involves {topic.replace('-', ' ')}")
                break

    if not reasons:
        reasons.append("expands your open source knowledge")

    return "This project " + " and ".join(reasons[:2]) + "."
