"""Publisher service for archiving and publishing analysis reports."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from oss_navi.utils.paths import REPORTS_DIR, TEMP_DIR, ensure_directories


class GitOperationError(Exception):
    """Error during git operations."""

    pass


class BlogRepoNotConfiguredError(Exception):
    """Blog repository not configured."""

    pass


def archive_report(report_path: Path, archive_name: Optional[str] = None) -> str:
    """Archive a report to the reports directory.

    Args:
        report_path: Path to the report file to archive
        archive_name: Optional custom name for the archived file

    Returns:
        Path to the archived report

    Raises:
        FileNotFoundError: If report file doesn't exist
    """
    ensure_directories()

    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    # Generate archive name if not provided
    if not archive_name:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_name = f"report_{timestamp}.md"

    # Ensure .md extension
    if not archive_name.endswith(".md"):
        archive_name += ".md"

    archive_path = REPORTS_DIR / archive_name

    # Copy the report
    import shutil

    shutil.copy(report_path, archive_path)

    return str(archive_path)


def list_archived_reports() -> list[dict]:
    """List all archived reports.

    Returns:
        List of dicts with report info (name, path, modified_time)
    """
    ensure_directories()

    reports = []
    for report_file in REPORTS_DIR.glob("report_*.md"):
        stat = report_file.stat()
        reports.append({
            "name": report_file.name,
            "path": str(report_file),
            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "size": stat.st_size,
        })

    # Sort by modification time, newest first
    reports.sort(key=lambda r: r["modified"], reverse=True)

    return reports


def get_current_report() -> Optional[Path]:
    """Get the path to the current (temporary) report.

    Returns:
        Path to current report or None if it doesn't exist
    """
    current_report = TEMP_DIR / "current_report.md"
    if current_report.exists():
        return current_report
    return None


def push_to_blog(
    report_path: Path,
    blog_repo_path: str,
    commit_message: Optional[str] = None,
) -> str:
    """Push a report to the configured blog repository.

    Args:
        report_path: Path to the report file
        blog_repo_path: Path to the blog git repository
        commit_message: Optional commit message

    Returns:
        Commit hash

    Raises:
        BlogRepoNotConfiguredError: If blog repo path is not configured
        GitOperationError: If git operations fail
    """
    blog_path = Path(blog_repo_path)

    if not blog_path.exists():
        raise BlogRepoNotConfiguredError(f"Blog repository not found: {blog_repo_path}")

    if not (blog_path / ".git").exists():
        raise BlogRepoNotConfiguredError(f"Not a git repository: {blog_repo_path}")

    # Default commit message
    if not commit_message:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        commit_message = f"Add OSS-Navi report - {timestamp}"

    # Determine destination path in blog repo
    reports_dir = blog_path / "oss-navi"
    reports_dir.mkdir(exist_ok=True)

    dest_file = reports_dir / report_path.name

    # Copy report to blog repo
    import shutil

    shutil.copy(report_path, dest_file)

    # Run git commands
    try:
        # git add
        result = subprocess.run(
            ["git", "add", str(dest_file)],
            cwd=blog_path,
            capture_output=True,
            text=True,
            check=True,
        )

        # git commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=blog_path,
            capture_output=True,
            text=True,
            check=False,  # Don't fail if nothing to commit
        )

        # git push
        result = subprocess.run(
            ["git", "push"],
            cwd=blog_path,
            capture_output=True,
            text=True,
            check=True,
        )

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=blog_path,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Git operation failed: {e.stderr or e.stdout}") from e
    except FileNotFoundError as e:
        raise GitOperationError("Git not found in PATH") from e


def delete_report(report_path: Path) -> None:
    """Delete a report file.

    Args:
        report_path: Path to the report to delete

    Raises:
        FileNotFoundError: If report doesn't exist
    """
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    report_path.unlink()
