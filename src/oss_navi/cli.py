"""CLI entry point for OSS-Navi."""

import click

from oss_navi import __version__


@click.group()
@click.version_option(version=__version__, prog_name="oss-navi")
def main() -> None:
    """OSS-Navi - Discover and contribute to open source projects."""
    pass


@main.command()
@click.option("--learn", "-l", help="Learning focus (technology/language)")
@click.option("--output", "-o", "output_path", help="Output file path")
@click.option("--no-cache", is_flag=True, help="Skip cache, require fresh data")
@click.option("--open", "open_report", is_flag=True, help="Open report after generation")
def analysis(
    learn: str | None,
    output_path: str | None,
    no_cache: bool,
    open_report: bool,
) -> None:
    """Generate personalized project recommendations.

    Analyzes your GitHub profile and available tasks to recommend
    the best open source projects for you to contribute to.
    """
    from oss_navi.services.analyzer import ClaudeCodeError, run_analysis
    from oss_navi.utils.cache import read_json
    from oss_navi.utils.paths import (
        GITHUB_PROFILE_CACHE,
        GOODFIRSTISSUE_TASKS_CACHE,
        UPFORGRABS_TASKS_CACHE,
    )

    click.echo("✓ Analyzing profile...")

    # Load cached profile data
    profile = read_json(GITHUB_PROFILE_CACHE)
    if not profile:
        click.echo(
            "✗ No cached profile data available\n"
            "  Run: oss-navi sync",
            err=True,
        )
        raise SystemExit(2)

    # Load cached task data
    tasks_data = read_json(UPFORGRABS_TASKS_CACHE) or []
    tasks_data += read_json(GOODFIRSTISSUE_TASKS_CACHE) or []

    if not tasks_data:
        click.echo(
            "✗ No cached task data available\n"
            "  Run: oss-navi sync",
            err=True,
        )
        raise SystemExit(2)

    # Convert to Task objects
    from oss_navi.models.task import Task

    tasks = []
    for t in tasks_data:
        try:
            tasks.append(Task(**t))
        except Exception:
            continue  # Skip malformed tasks

    click.echo(f"✓ Filtering tasks... ({len(tasks)} matches)")

    # Get memory if available
    from oss_navi.utils.paths import MEMORY_FILE

    memory = read_json(MEMORY_FILE)

    # Run analysis
    try:
        report = run_analysis(
            profile=profile,
            tasks=tasks,
            learning_focus=learn,
            memory=memory,
        )
        click.echo(f"✓ Report saved: {report.file_path}")

        # Show top recommendations
        if report.recommended_projects:
            click.echo("\nTop Recommendations:")
            for i, proj in enumerate(report.recommended_projects, 1):
                click.echo(f"  {i}. {proj}")

        # Copy to custom output path if specified
        if output_path:
            import shutil

            shutil.copy(report.file_path, output_path)
            click.echo(f"✓ Report copied to: {output_path}")

        # Open report if requested
        if open_report:
            import webbrowser

            webbrowser.open(f"file://{report.file_path}")

    except ClaudeCodeError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(3)
    except ValueError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(5)


@main.command()
@click.option("--github", is_flag=True, help="Sync GitHub profile only")
@click.option("--tasks", is_flag=True, help="Sync task sources only")
@click.option("--force", is_flag=True, help="Force refresh ignoring cache")
@click.option("--dry-run", is_flag=True, help="Show what would be fetched")
def sync(github: bool, tasks: bool, force: bool, dry_run: bool) -> None:
    """Fetch and cache GitHub profile and task data.

    By default, syncs both GitHub profile and task sources.
    Use --github or --tasks to sync only specific sources.
    """
    from oss_navi.services.github import (
        GitHubAuthError,
        GitHubRateLimitError,
        fetch_and_cache_profile,
    )
    from oss_navi.services.scraper import (
        GoodFirstIssueUnavailableError,
        UpForGrabsUnavailableError,
        fetch_and_cache_tasks,
    )
    from oss_navi.utils.cache import is_cache_valid

    # If neither flag is set, sync both
    sync_github = github or (not github and not tasks)
    sync_tasks = tasks or (not github and not tasks)

    if dry_run:
        click.echo("Would fetch:")
        if sync_github:
            click.echo("  - GitHub profile (requires --github-username in config)")
        if sync_tasks:
            click.echo("  - Up For Grabs tasks")
            click.echo("  - Good First Issue tasks")
        return

    # Sync GitHub profile
    if sync_github:
        # Try to get username from config
        from oss_navi.config import load_config

        config = load_config()
        username = config.github_username if config else None

        if not username:
            click.echo(
                "⚠ No GitHub username configured\n"
                "  Run: oss-navi config --github-username YOUR_USERNAME",
                err=True,
            )
        elif not force and is_cache_valid("github_profile"):
            click.echo("✓ GitHub profile cache is valid (use --force to refresh)")
        else:
            click.echo(f"✓ Fetching GitHub profile for {username}...")
            try:
                profile = fetch_and_cache_profile(username, config.github_token if config else None)
                if profile:
                    click.echo(f"  Found {profile.public_repos} public repos")
                    langs = list(profile.languages.keys())[:5]
                    click.echo(f"  Languages: {', '.join(langs)}")
                else:
                    click.echo("✗ User not found", err=True)
            except GitHubAuthError as e:
                click.echo(f"✗ {e}", err=True)
            except GitHubRateLimitError as e:
                click.echo(f"✗ {e}", err=True)

    # Sync task sources
    if sync_tasks:
        sources_to_fetch = []
        if force or not is_cache_valid("upforgrabs_tasks"):
            sources_to_fetch.append("upforgrabs")
        else:
            click.echo("✓ Up For Grabs cache is valid (use --force to refresh)")

        if force or not is_cache_valid("goodfirstissue_tasks"):
            sources_to_fetch.append("goodfirstissue")
        else:
            click.echo("✓ Good First Issue cache is valid (use --force to refresh)")

        if sources_to_fetch:
            click.echo(f"✓ Fetching tasks from: {', '.join(sources_to_fetch)}...")
            try:
                fetched_tasks = fetch_and_cache_tasks(sources=sources_to_fetch)
                click.echo(f"  Fetched {len(fetched_tasks)} tasks")
            except (UpForGrabsUnavailableError, GoodFirstIssueUnavailableError) as e:
                click.echo(f"⚠ {e}", err=True)

    click.echo("✓ Sync complete")


@main.command()
@click.option("--github-username", help="Set GitHub username")
@click.option("--github-token", help="Set GitHub personal access token")
@click.option("--blog-repo", help="Set blog repository path")
@click.option("--min-stars", type=int, help="Set minimum stars filter")
@click.option("--max-age", type=int, help="Set maximum issue age (days)")
@click.option("--list", "show_list", is_flag=True, help="List current configuration")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config(
    github_username: str | None,
    github_token: str | None,
    blog_repo: str | None,
    min_stars: int | None,
    max_age: int | None,
    show_list: bool,
    reset: bool,
) -> None:
    """Manage configuration settings.

    Configure your GitHub credentials and filter preferences.
    Settings are stored in ~/.oss-navi/state/config.json
    """
    from oss_navi.config import (
        load_config,
        reset_config,
        save_config,
        save_github_token,
        validate_github_token,
        validate_github_username,
    )
    from oss_navi.models.config import Config, Filters

    # Handle reset
    if reset:
        reset_config()
        click.echo("✓ Configuration reset to defaults")
        return

    # Handle list
    if show_list:
        current_config = load_config()
        if not current_config:
            click.echo("No configuration found. Use --github-username to set up.")
            return

        click.echo("Current Configuration:")
        click.echo(f"  GitHub Username: {current_config.github_username or 'not set'}")
        click.echo(f"  Blog Repository: {current_config.blog_repo_path or 'not set'}")
        click.echo(f"  Min Stars: {current_config.filters.min_stars}")
        click.echo(f"  Max Age (days): {current_config.filters.max_age_days}")
        return

    # Load existing config or create new
    current_config = load_config()
    updated = False

    if current_config is None:
        current_config = Config()
        updated = True

    # Update username
    if github_username is not None:
        if validate_github_username(github_username):
            current_config.github_username = github_username
            updated = True
            click.echo(f"✓ GitHub username set: {github_username}")
        else:
            click.echo(f"✗ Invalid GitHub username: {github_username}", err=True)
            raise SystemExit(1)

    # Update token (stored separately for security)
    if github_token is not None:
        try:
            validate_github_token(github_token)
            save_github_token(github_token)
            click.echo("✓ GitHub token saved securely")
        except ValueError as e:
            click.echo(f"✗ {e}", err=True)
            raise SystemExit(1)

    # Update blog repo
    if blog_repo is not None:
        current_config.blog_repo_path = blog_repo
        updated = True
        click.echo(f"✓ Blog repository set: {blog_repo}")

    # Update filters
    if min_stars is not None:
        current_config.filters.min_stars = min_stars
        updated = True
        click.echo(f"✓ Min stars filter set: {min_stars}")

    if max_age is not None:
        current_config.filters.max_age_days = max_age
        updated = True
        click.echo(f"✓ Max age filter set: {max_age} days")

    # Save if any changes
    if updated:
        from datetime import datetime, timezone

        current_config.updated_at = datetime.now(timezone.utc)
        save_config(current_config)
        click.echo("✓ Configuration saved")


@main.command()
@click.option("--push", is_flag=True, help="Push to configured blog repository")
@click.option("--message", "-m", help="Commit message for blog push")
@click.option("--list", "show_list", is_flag=True, help="List archived reports")
@click.argument("report", required=False)
def publish(push: bool, message: str | None, show_list: bool, report: str | None) -> None:
    """Archive and optionally publish analysis reports.

    Without arguments, archives the current report.
    Use --push to also push to a configured blog repository.
    """
    from oss_navi.config import load_config
    from oss_navi.services.publisher import (
        BlogRepoNotConfiguredError,
        GitOperationError,
        archive_report,
        get_current_report,
        list_archived_reports,
        push_to_blog,
    )

    # Handle list
    if show_list:
        reports = list_archived_reports()
        if not reports:
            click.echo("No archived reports found")
            return

        click.echo("Archived Reports:")
        for r in reports:
            size_kb = r["size"] / 1024
            click.echo(f"  {r['name']} ({size_kb:.1f} KB) - {r['modified'][:10]}")
        return

    # Determine report to archive
    report_path = None
    if report:
        report_path = Path(report)
    else:
        report_path = get_current_report()

    if not report_path or not report_path.exists():
        click.echo("✗ No report found to archive\n  Run: oss-navi analysis", err=True)
        raise SystemExit(1)

    # Archive the report
    archived_path = archive_report(report_path)
    click.echo(f"✓ Report archived: {archived_path}")

    # Push if requested
    if push:
        config = load_config()
        if not config or not config.blog_repo_path:
            click.echo(
                "✗ Blog repository not configured\n"
                "  Run: oss-navi config --blog-repo /path/to/blog",
                err=True,
            )
            raise SystemExit(1)

        try:
            commit_hash = push_to_blog(
                Path(archived_path),
                config.blog_repo_path,
                message,
            )
            click.echo(f"✓ Pushed to blog (commit: {commit_hash[:7]})")
        except BlogRepoNotConfiguredError as e:
            click.echo(f"✗ {e}", err=True)
            raise SystemExit(1)
        except GitOperationError as e:
            click.echo(f"✗ {e}", err=True)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
