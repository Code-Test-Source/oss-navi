"""Analysis service for generating personalized OSS recommendations."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oss_navi.models.report import AnalysisReport
from oss_navi.models.task import Task, calculate_hotness_score
from oss_navi.utils.paths import TEMP_DIR


# Constants
CLAUDE_CODE_COMMAND = "claude"
DEFAULT_TIMEOUT_SECONDS = 60


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
