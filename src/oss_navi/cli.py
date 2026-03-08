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
@click.option("--skip-status", is_flag=True, help="Skip issue status checks (avoids GitHub API rate limits)")
@click.option(
    "--mode", "-m",
    type=click.Choice(["fast", "normal", "thinking"], case_sensitive=False),
    default="normal",
    help="Recommendation mode: fast (<30s), normal (<90s), thinking (<180s)",
)
@click.option("--language", type=str, help="Primary language for recommendations")
@click.option("--rounds", type=int, default=3, help="Maximum recommendation rounds (interactive mode)")
@click.option("--session", type=str, help="Resume existing session by ID")
def analysis(
    learn: str | None,
    output_path: str | None,
    no_cache: bool,
    open_report: bool,
    no_interactive: bool,
    explore: bool,
    recommendations: int,
    skip_status: bool,
    mode: str,
    language: str | None,
    rounds: int,
    session: str | None,
) -> None:
    """Generate personalized project recommendations.

    Analyzes your GitHub profile and available tasks to recommend
    the best open source projects for you to contribute to.

    \b
    Recommendation Modes:
      fast     Content-based filtering only (<30s, <50MB)
      normal   Surprise SVD/KNN collaborative filtering (<90s, <200MB)
      thinking LightFM + Apriori pattern mining (<180s, <500MB)
    """
    from oss_navi.models.recommendation import RecommendationMode, check_mode_availability
    from oss_navi.services.analyzer import (
        ClaudeCodeError,
        find_great_projects,
        generate_recommendations,
        run_analysis,
        suggest_adjacent_fields,
    )
    from oss_navi.services.recommender import create_recommender_service
    from oss_navi.utils.cache import read_json
    from oss_navi.utils.paths import (
        GITHUB_PROFILE_CACHE,
        GOODFIRSTISSUES_TASKS_CACHE,
        UPFORGRABS_TASKS_CACHE,
    )

    # Clamp recommendations to valid range
    recommendations = max(5, min(10, recommendations))

    click.echo("✓ Analyzing profile...")

    # Check mode availability
    mode_enum = RecommendationMode(mode.lower())
    is_available, missing = check_mode_availability(mode_enum)
    if not is_available:
        click.echo(
            f"⚠ Mode '{mode}' requires: {', '.join(missing)}\n"
            f"  Install with: pip install oss-navi[recommend]\n"
            f"  Falling back to fast mode",
            err=True,
        )
        mode = "fast"
        mode_enum = RecommendationMode.FAST

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
    click.echo(f"✓ Mode: {mode} ({'Surprise SVD/KNN' if mode == 'normal' else 'LightFM + Apriori' if mode == 'thinking' else 'Content-based'})")

    # Load or create user preferences

    from oss_navi.models.preferences import (
        LanguageProfile,
        LanguageType,
        SkillLevel,
        UserPreferences,
    )
    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"
    user_prefs = None
    if prefs_path.exists():
        prefs_data = read_json(prefs_path)
        if prefs_data:
            try:
                user_prefs = UserPreferences(**prefs_data)
            except Exception:
                pass

    # Create preferences from profile if not set
    if not user_prefs:
        user_prefs = UserPreferences()
        user_languages = profile.get("languages", {})
        for i, (lang, bytes_count) in enumerate(user_languages.items()):
            lang_type = LanguageType.PRIMARY if i == 0 else LanguageType.SECONDARY
            skill = SkillLevel.ADVANCED if bytes_count > 100000 else SkillLevel.INTERMEDIATE if bytes_count > 10000 else SkillLevel.BEGINNER
            user_prefs.languages.append(LanguageProfile(
                language=lang,
                type=lang_type,
                skill_level=skill,
            ))

    # Override language if specified
    if language:
        user_prefs.languages = [
            lp for lp in user_prefs.languages
            if lp.language.lower() != language.lower()
        ]
        user_prefs.languages.insert(0, LanguageProfile(
            language=language,
            type=LanguageType.PRIMARY,
            skill_level=SkillLevel.INTERMEDIATE,
        ))

    # Use intelligent recommender service
    click.echo(f"\n✓ Generating {recommendations} recommendations using {mode} mode...")
    recommender = create_recommender_service(mode=mode, max_recommendations=recommendations)

    # Convert tasks to dict format for recommender
    tasks_dicts = [t.model_dump() for t in tasks]

    # Generate recommendations
    intelligent_recs = recommender.recommend(
        user_preferences=user_prefs,
        cached_tasks=tasks_dicts,
    )

    # Display intelligent recommendations
    if intelligent_recs:
        click.echo("\n🎯 Intelligent Recommendations:")
        for i, rec in enumerate(intelligent_recs[:recommendations], 1):
            click.echo(f"\n  {i}. {rec.project_name} (Score: {rec.relevance_score}/10)")
            click.echo(f"     Language: {rec.language} | Stars: {rec.stars:,}")
            click.echo(f"     Why: {rec.reasoning}")
            if rec.skill_gap_analysis:
                click.echo(f"     Skills to develop: {', '.join(rec.skill_gap_analysis)}")
            if rec.issue_url:
                click.echo(f"     Issue: {rec.issue_url}")

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

    # Generate scored recommendations (legacy for compatibility)
    scored_recommendations = generate_recommendations(
        tasks=tasks,
        user_languages=user_languages,
        learning_focus=learning_focus,
        count=recommendations,
        check_status=not skip_status,
    )

    # Show top recommendations with ratings
    if scored_recommendations:
        click.echo("\n📋 Additional Recommendations:")
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

        # Update long-term memory ALWAYS (not just when --learn is provided)
        from oss_navi.services.analyzer import update_memory_from_report_with_profile

        updated_memory = update_memory_from_report_with_profile(
            report.content, profile, learning_focus
        )
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
        raise SystemExit(3) from None
    except ValueError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(5) from None


@main.command()
@click.option("--github", is_flag=True, help="Sync GitHub profile only")
@click.option("--tasks", is_flag=True, help="Sync task sources only")
@click.option("--learning", is_flag=True, help="Sync learning resources (csdiy, LeetCode, Codeforces)")
@click.option("--csdiy", is_flag=True, help="Sync csdiy.wiki courses only")
@click.option("--leetcode", is_flag=True, help="Sync LeetCode problems only")
@click.option("--codeforces", is_flag=True, help="Sync Codeforces problems only")
@click.option("--force", is_flag=True, help="Force refresh ignoring cache")
@click.option("--dry-run", is_flag=True, help="Show what would be fetched")
def sync(
    github: bool,
    tasks: bool,
    learning: bool,
    csdiy: bool,
    leetcode: bool,
    codeforces: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Fetch and cache GitHub profile, task data, and learning resources.

    By default, syncs GitHub profile and task sources.
    Use --learning to sync learning resources from third-party datasets.
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

    # Determine what to sync
    sync_github = github or (not github and not tasks and not learning and not csdiy and not leetcode and not codeforces)
    sync_tasks = tasks or (not github and not tasks and not learning and not csdiy and not leetcode and not codeforces)
    sync_learning = learning or csdiy or leetcode or codeforces

    if dry_run:
        click.echo("Would fetch:")
        if sync_github:
            click.echo("  - GitHub profile (requires --github-username in config)")
        if sync_tasks:
            click.echo("  - Up For Grabs tasks")
            click.echo("  - Good First Issue tasks")
        if sync_learning:
            click.echo("  - Learning resources:")
            if csdiy or learning:
                click.echo("    - csdiy.wiki courses")
            if leetcode or learning:
                click.echo("    - LeetCode problems (neenza/leetcode-problems dataset)")
            if codeforces or learning:
                click.echo("    - Codeforces problems (Kaggle/HuggingFace dataset)")
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

    # Sync learning resources
    if sync_learning:
        from oss_navi.services.learning import LearningService
        from oss_navi.utils.cache import is_cache_valid

        learning_service = LearningService()
        click.echo("\n🔄 Syncing learning resources...")

        total_courses = 0
        total_problems = 0

        # Sync csdiy.wiki
        if csdiy or learning:
            if force or not is_cache_valid("csdiy"):
                click.echo("  - csdiy.wiki: Scraping courses...")
                courses = learning_service.load_csdiy_courses(force=True)
                total_courses = len(courses)
                click.echo(f"    ✓ Loaded {total_courses} courses")
            else:
                click.echo("  - csdiy.wiki: Cache valid (use --force to refresh)")

        # Sync LeetCode
        if leetcode or learning:
            if force or not is_cache_valid("leetcode"):
                click.echo("  - LeetCode: Loading from neenza/leetcode-problems dataset...")
                problems = learning_service.load_leetcode_problems(force=True)
                leetcode_count = len(problems)
                total_problems += leetcode_count
                click.echo(f"    ✓ Loaded {leetcode_count} problems")
            else:
                click.echo("  - LeetCode: Cache valid (use --force to refresh)")

        # Sync Codeforces
        if codeforces or learning:
            if force or not is_cache_valid("codeforces"):
                click.echo("  - Codeforces: Loading from Kaggle/HuggingFace dataset...")
                problems = learning_service.load_codeforces_problems(force=True)
                codeforces_count = len(problems)
                total_problems += codeforces_count
                click.echo(f"    ✓ Loaded {codeforces_count} problems")
            else:
                click.echo("  - Codeforces: Cache valid (use --force to refresh)")

        click.echo("\n📊 Summary:")
        if total_courses > 0:
            click.echo(f"  - Courses: {total_courses}")
        click.echo(f"  - Practice problems: {total_problems}")
        click.echo("  - API calls: Minimal (datasets used for bulk data)")

    click.echo("\n✓ Sync complete")


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
            raise SystemExit(1) from None

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
            raise SystemExit(1) from None
        except GitOperationError as e:
            click.echo(f"✗ {e}", err=True)
            raise SystemExit(1) from None


@main.group()
def prefs() -> None:
    """Manage user preferences for recommendations.

    Configure your languages, skill levels, and blocking rules.
    """
    pass


@prefs.command("set-language")
@click.argument("language")
@click.option("--type", "-t", "lang_type",
    type=click.Choice(["primary", "secondary", "learning"], case_sensitive=False),
    default="primary",
    help="Language type (default: primary)",
)
@click.option("--level", "-l",
    type=click.Choice(["beginner", "intermediate", "advanced"], case_sensitive=False),
    default="intermediate",
    help="Skill level (default: intermediate)",
)
def prefs_set_language(language: str, lang_type: str, level: str) -> None:
    """Set a language in your profile.

    Example: oss-navi prefs set-language python --type primary --level advanced
    """
    import json

    from oss_navi.models.preferences import (
        LanguageProfile,
        LanguageType,
        SkillLevel,
        UserPreferences,
    )
    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"

    # Load existing preferences
    user_prefs = None
    if prefs_path.exists():
        try:
            with open(prefs_path) as f:
                prefs_data = json.load(f)
            user_prefs = UserPreferences(**prefs_data)
        except Exception:
            pass

    if not user_prefs:
        user_prefs = UserPreferences()

    # Remove existing entry for this language
    user_prefs.languages = [
        lp for lp in user_prefs.languages
        if lp.language.lower() != language.lower()
    ]

    # Add new language profile
    user_prefs.languages.append(LanguageProfile(
        language=language.lower(),
        type=LanguageType(lang_type.lower()),
        skill_level=SkillLevel(level.lower()),
    ))

    # Save preferences
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(prefs_path, "w") as f:
        json.dump(user_prefs.model_dump(mode="json"), f, indent=2, default=str)

    click.echo(f"✓ Language set: {language} ({lang_type}, {level})")


@prefs.command("remove-language")
@click.argument("language")
def prefs_remove_language(language: str) -> None:
    """Remove a language from your profile."""
    import json

    from oss_navi.models.preferences import UserPreferences
    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"

    if not prefs_path.exists():
        click.echo("✗ No preferences file found", err=True)
        raise SystemExit(1)

    try:
        with open(prefs_path) as f:
            prefs_data = json.load(f)
        user_prefs = UserPreferences(**prefs_data)
    except Exception:
        click.echo("✗ Failed to load preferences", err=True)
        raise SystemExit(1) from None

    # Remove language
    original_count = len(user_prefs.languages)
    user_prefs.languages = [
        lp for lp in user_prefs.languages
        if lp.language.lower() != language.lower()
    ]

    if len(user_prefs.languages) == original_count:
        click.echo(f"✗ Language not found: {language}", err=True)
        raise SystemExit(1)

    # Save preferences
    with open(prefs_path, "w") as f:
        json.dump(user_prefs.model_dump(mode="json"), f, indent=2, default=str)

    click.echo(f"✓ Language removed: {language}")


@prefs.command("block")
@click.argument("block_type", type=click.Choice(["project", "maintainer", "organization", "topic", "language"]))
@click.argument("value")
@click.option("--reason", "-r", help="Reason for blocking")
def prefs_block(block_type: str, value: str, reason: str | None) -> None:
    """Add a blocking rule.

    Example: oss-navi prefs block language typescript --reason "Not interested"
    """
    import json

    from oss_navi.models.preferences import BlockingRule, BlockType, UserPreferences
    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"

    # Load existing preferences
    user_prefs = None
    if prefs_path.exists():
        try:
            with open(prefs_path) as f:
                prefs_data = json.load(f)
            user_prefs = UserPreferences(**prefs_data)
        except Exception:
            pass

    if not user_prefs:
        user_prefs = UserPreferences()

    # Check for duplicate
    for rule in user_prefs.blocking_rules:
        if rule.block_type.value == block_type.lower() and rule.value.lower() == value.lower():
            click.echo(f"✗ Already blocking: {block_type} = {value}", err=True)
            raise SystemExit(1)

    # Add blocking rule
    user_prefs.blocking_rules.append(BlockingRule(
        block_type=BlockType(block_type.lower()),
        value=value,
        reason=reason,
    ))

    # Save preferences
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(prefs_path, "w") as f:
        json.dump(user_prefs.model_dump(mode="json"), f, indent=2, default=str)

    click.echo(f"✓ Blocked: {block_type} = {value}")


@prefs.command("unblock")
@click.argument("block_type", type=click.Choice(["project", "maintainer", "organization", "topic", "language"]))
@click.argument("value")
def prefs_unblock(block_type: str, value: str) -> None:
    """Remove a blocking rule."""
    import json

    from oss_navi.models.preferences import UserPreferences
    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"

    if not prefs_path.exists():
        click.echo("✗ No preferences file found", err=True)
        raise SystemExit(1)

    try:
        with open(prefs_path) as f:
            prefs_data = json.load(f)
        user_prefs = UserPreferences(**prefs_data)
    except Exception:
        click.echo("✗ Failed to load preferences", err=True)
        raise SystemExit(1) from None

    # Remove blocking rule
    original_count = len(user_prefs.blocking_rules)
    user_prefs.blocking_rules = [
        r for r in user_prefs.blocking_rules
        if not (r.block_type.value == block_type.lower() and r.value.lower() == value.lower())
    ]

    if len(user_prefs.blocking_rules) == original_count:
        click.echo(f"✗ Blocking rule not found: {block_type} = {value}", err=True)
        raise SystemExit(1)

    # Save preferences
    with open(prefs_path, "w") as f:
        json.dump(user_prefs.model_dump(mode="json"), f, indent=2, default=str)

    click.echo(f"✓ Unblocked: {block_type} = {value}")


@prefs.command("show")
def prefs_show() -> None:
    """Display current preferences."""
    import json

    from oss_navi.models.preferences import UserPreferences
    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"

    if not prefs_path.exists():
        click.echo("No preferences configured yet.")
        click.echo("\nTo get started:")
        click.echo("  oss-navi prefs set-language python --type primary --level advanced")
        return

    try:
        with open(prefs_path) as f:
            prefs_data = json.load(f)
        user_prefs = UserPreferences(**prefs_data)
    except Exception as e:
        click.echo(f"✗ Failed to load preferences: {e}", err=True)
        raise SystemExit(1) from None

    click.echo("Current Preferences:\n")

    if user_prefs.languages:
        click.echo("Languages:")
        for lp in user_prefs.languages:
            click.echo(f"  - {lp.language}: {lp.type.value} ({lp.skill_level.value})")
    else:
        click.echo("Languages: (none configured)")

    if user_prefs.domain_interests:
        click.echo("\nDomain Interests:")
        for di in user_prefs.domain_interests:
            click.echo(f"  - {di.domain}: {di.interest_level}/10")

    if user_prefs.blocking_rules:
        click.echo("\nBlocking Rules:")
        for rule in user_prefs.blocking_rules:
            reason = f" ({rule.reason})" if rule.reason else ""
            click.echo(f"  - {rule.block_type.value}: {rule.value}{reason}")
    else:
        click.echo("\nBlocking Rules: (none)")


@prefs.command("export")
@click.argument("file", default="preferences.json")
def prefs_export(file: str) -> None:
    """Export preferences to a JSON file."""
    import shutil

    from oss_navi.utils.paths import STATE_DIR

    prefs_path = STATE_DIR / "preferences.json"

    if not prefs_path.exists():
        click.echo("✗ No preferences to export", err=True)
        raise SystemExit(1)

    shutil.copy(prefs_path, file)
    click.echo(f"✓ Preferences exported to: {file}")


@prefs.command("import")
@click.argument("file")
def prefs_import(file: str) -> None:
    """Import preferences from a JSON file."""
    import shutil
    from pathlib import Path

    from oss_navi.models.preferences import UserPreferences
    from oss_navi.utils.paths import STATE_DIR

    source_path = Path(file)
    if not source_path.exists():
        click.echo(f"✗ File not found: {file}", err=True)
        raise SystemExit(1)

    # Validate the file
    try:
        import json
        with open(source_path) as f:
            data = json.load(f)
        UserPreferences(**data)
    except Exception as e:
        click.echo(f"✗ Invalid preferences file: {e}", err=True)
        raise SystemExit(1) from None

    # Copy to preferences
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(source_path, STATE_DIR / "preferences.json")
    click.echo(f"✓ Preferences imported from: {file}")


@main.group()
def session() -> None:
    """Manage recommendation sessions.

    List, show, export, or delete previous analysis sessions.
    """
    pass


@session.command("list")
@click.option("--status", type=click.Choice(["active", "completed", "all"]), default="active")
def session_list(status: str) -> None:
    """List all sessions."""
    from oss_navi.models.session import SessionStatus
    from oss_navi.services.session import get_session_service

    svc = get_session_service()

    status_filter = None if status == "all" else SessionStatus(status)
    sessions = svc.list_sessions(status=status_filter)

    if not sessions:
        click.echo("No sessions found")
        return

    click.echo(f"Sessions ({len(sessions)}):\n")
    for s in sessions:
        rounds = len(s.rounds)
        created = s.created_at.strftime("%Y-%m-%d %H:%M")
        click.echo(f"  {s.session_id} [{s.status.value}] {rounds} rounds - {created}")


@session.command("show")
@click.argument("session_id")
def session_show(session_id: str) -> None:
    """Show session details."""
    from oss_navi.services.session import get_session_service

    svc = get_session_service()
    session = svc.get_session(session_id)

    if not session:
        click.echo(f"✗ Session not found: {session_id}", err=True)
        raise SystemExit(1)

    click.echo(f"Session: {session.session_id}")
    click.echo(f"Status: {session.status.value}")
    click.echo(f"Mode: {session.mode.value}")
    click.echo(f"Rounds: {len(session.rounds)}")
    click.echo(f"Created: {session.created_at}")

    if session.rounds:
        click.echo("\nRounds:")
        for r in session.rounds:
            accepted = sum(1 for f in r.user_feedback if f.feedback_type.value == "accept")
            rejected = sum(1 for f in r.user_feedback if f.feedback_type.value == "reject")
            click.echo(f"  Round {r.round_number}: {len(r.recommendations)} recs, {accepted} accepted, {rejected} rejected")


@session.command("export")
@click.argument("session_id")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["markdown", "json"]), default="markdown")
def session_export(session_id: str, output: str | None, format: str) -> None:
    """Export session report."""
    from pathlib import Path

    from oss_navi.services.session import get_session_service

    svc = get_session_service()
    session = svc.get_session(session_id)

    if not session:
        click.echo(f"✗ Session not found: {session_id}", err=True)
        raise SystemExit(1)

    if format == "json":
        import json
        content = json.dumps(session.model_dump(mode="json"), indent=2, default=str)
    else:
        content = session.to_markdown_report()

    if output:
        Path(output).write_text(content)
        click.echo(f"✓ Report exported to: {output}")
    else:
        click.echo(content)


@session.command("delete")
@click.argument("session_id")
@click.option("--force", is_flag=True, help="Skip confirmation")
def session_delete(session_id: str, force: bool) -> None:
    """Delete a session."""
    from oss_navi.services.session import get_session_service

    svc = get_session_service()
    session = svc.get_session(session_id)

    if not session:
        click.echo(f"✗ Session not found: {session_id}", err=True)
        raise SystemExit(1)

    if not force:
        if not click.confirm(f"Delete session {session_id}?"):
            click.echo("Cancelled")
            return

    if svc.delete_session(session_id):
        click.echo(f"✓ Session deleted: {session_id}")
    else:
        click.echo("✗ Failed to delete session", err=True)


if __name__ == "__main__":
    main()
