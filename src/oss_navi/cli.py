"""CLI entry point for OSS-Navi."""

import logging
from datetime import UTC

import click

from oss_navi import __version__


# Configure logging
def configure_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging level based on verbose/quiet flags."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


@click.group()
@click.version_option(version=__version__, prog_name="oss-navi")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-essential output")
@click.pass_context
def main(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """OSS-Navi - Discover and contribute to open source projects."""
    # Store flags in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # Configure logging
    configure_logging(verbose, quiet)


def prompt_learning_interests() -> str | None:
    """Prompt user for their current learning interests.

    Returns:
        User input string or None if empty
    """
    return click.prompt(
        "What are you currently learning or interested in?",
        default="",
        show_default=False,
        type=str,
    ).strip() or None


@main.command()
@click.option("--learn", "-l", help="Learning focus (technology/language)")
@click.option("--output", "-o", "output_path", help="Output file path")
@click.option("--no-cache", is_flag=True, help="Skip cache, require fresh data")
@click.option("--open", "open_report", is_flag=True, help="Open report after generation")
@click.option("--no-interactive", is_flag=True, help="Skip interactive prompts")
@click.option("--explore", is_flag=True, help="Suggest adjacent fields to explore")
@click.option("-n", "--recommendations", type=int, default=7, help="Number of recommendations (5-10)")
def analysis(
    learn: str | None,
    output_path: str | None,
    no_cache: bool,
    open_report: bool,
    no_interactive: bool,
    explore: bool,
    recommendations: int,
) -> None:
    """Generate personalized project recommendations.

    Analyzes your GitHub profile and available tasks to recommend
    the best open source projects for you to contribute to.
    """
    from oss_navi.services.analyzer import (
        ClaudeCodeError,
        find_great_projects,
        generate_recommendations,
        run_analysis,
        suggest_adjacent_fields,
    )
    from oss_navi.utils.cache import read_json
    from oss_navi.utils.paths import (
        GITHUB_PROFILE_CACHE,
        GOODFIRSTISSUES_TASKS_CACHE,
        UPFORGRABS_TASKS_CACHE,
    )

    # Clamp recommendations to valid range
    recommendations = max(5, min(10, recommendations))

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
    tasks_data += read_json(GOODFIRSTISSUES_TASKS_CACHE) or []

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

    # Interactive prompt for learning interests
    learning_focus = learn
    if not no_interactive and not learn:
        learning_focus = prompt_learning_interests()

    # Show field exploration suggestions if requested
    if explore:
        user_languages = profile.get("languages", {})
        current_interest = learning_focus or list(user_languages.keys())[0] if user_languages else "programming"
        suggestions = suggest_adjacent_fields(current_interest, user_languages)
        click.echo("\n📚 Suggested fields to explore:")
        for i, field in enumerate(suggestions, 1):
            click.echo(f"  {i}. {field}")
        click.echo()

    # Find great projects for learning
    user_languages = profile.get("languages", {})
    great_projects = find_great_projects(
        user_languages=user_languages,
        learning_focus=learning_focus,
        count=3,
    )

    if great_projects:
        click.echo("\n⭐ Great projects for learning:")
        for proj in great_projects:
            click.echo(f"  - {proj.name} ({proj.stars:,} stars)")
            click.echo(f"    {proj.why_great}")

    # Generate scored recommendations
    click.echo(f"\n✓ Generating {recommendations} recommendations...")
    scored_recommendations = generate_recommendations(
        tasks=tasks,
        user_languages=user_languages,
        learning_focus=learning_focus,
        count=recommendations,
    )

    # Show top recommendations with ratings
    if scored_recommendations:
        click.echo("\n🎯 Top Recommendations:")
        for i, rec in enumerate(scored_recommendations[:recommendations], 1):
            status_icon = "✓" if rec.status.is_available else "⚠"
            click.echo(f"  {i}. {rec.task.title[:50]}...")
            click.echo(f"     Rating: {rec.rating:.1f}/10 - {rec.reason[:60]}...")
            if not rec.status.is_available:
                click.echo(f"     {status_icon} Issue may not be available")

    # Run analysis
    try:
        report = run_analysis(
            profile=profile,
            tasks=tasks,
            learning_focus=learning_focus,
            memory=memory,
        )
        click.echo(f"\n✓ Report saved: {report.file_path}")

        # Update long-term memory if learning focus was provided
        if learn:
            from oss_navi.services.analyzer import update_memory_from_report
            updated_memory = update_memory_from_report(report.content, learn)
            if updated_memory:
                click.echo("✓ Long-term memory updated")

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

        if force or not is_cache_valid("goodfirstissues_tasks"):
            sources_to_fetch.append("goodfirstissues")
        else:
            click.echo("✓ Good First Issues cache is valid (use --force to refresh)")

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
@click.option("--http-proxy", help="Set HTTP proxy URL (e.g., http://proxy:8080)")
@click.option("--https-proxy", help="Set HTTPS proxy URL (e.g., http://proxy:8080)")
@click.option("--no-proxy", help="Set hosts to bypass proxy (comma-separated)")
@click.option("--list", "show_list", is_flag=True, help="List current configuration")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config(
    github_username: str | None,
    github_token: str | None,
    blog_repo: str | None,
    min_stars: int | None,
    max_age: int | None,
    http_proxy: str | None,
    https_proxy: str | None,
    no_proxy: str | None,
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
    from oss_navi.models.config import Config

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
        click.echo(f"  HTTP Proxy: {current_config.http_proxy or 'not set'}")
        click.echo(f"  HTTPS Proxy: {current_config.https_proxy or 'not set'}")
        click.echo(f"  No Proxy: {current_config.no_proxy or 'not set'}")
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

    # Update proxy settings
    if http_proxy is not None:
        current_config.http_proxy = http_proxy if http_proxy else None
        updated = True
        click.echo(f"✓ HTTP proxy set: {http_proxy or 'cleared'}")

    if https_proxy is not None:
        current_config.https_proxy = https_proxy if https_proxy else None
        updated = True
        click.echo(f"✓ HTTPS proxy set: {https_proxy or 'cleared'}")

    if no_proxy is not None:
        current_config.no_proxy = no_proxy if no_proxy else None
        updated = True
        click.echo(f"✓ No proxy set: {no_proxy or 'cleared'}")

    # Save if any changes
    if updated:
        from datetime import datetime

        current_config.updated_at = datetime.now(UTC)
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
    from pathlib import Path

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
