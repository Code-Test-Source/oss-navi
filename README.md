# OSS-Navi

> A CLI tool that helps programmers discover and contribute to open source projects

OSS-Navi analyzes your GitHub profile, scrapes beginner-friendly issues from multiple sources, and generates personalized project recommendations using Claude Code.

## Features

- **Profile Analysis**: Fetch and analyze your GitHub profile (commits, languages, activity)
- **Task Discovery**: Scrape open source tasks from Up For Grabs and Good First Issue
- **Smart Filtering**: Filter tasks by stars, recency, and compute a "hotness" score
- **Learning Focus**: Specify what you're currently learning with `--learn` flag
- **AI Recommendations**: Generate personalized recommendations with Claude Code
- **Report Archiving**: Archive and optionally publish reports to your blog
- **Robust URL Validation**: Validates all scraped URLs to ensure they point to valid GitHub issues

## Installation

```bash
# Clone the repository
git clone https://github.com/Code-Test-Source/oss-navi.git
cd oss-navi

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

```bash
# Configure your GitHub credentials
oss-navi config --github-username your-username
oss-navi config --github-token ghp_your_token_here

# Sync your profile and available tasks
oss-navi sync

# Generate personalized recommendations
oss-navi analysis

# Focus on learning a specific technology
oss-navi analysis --learn rust
```

## Commands

### `oss-navi config`

Manage configuration settings:

```bash
# Set GitHub username
oss-navi config --github-username your-username

# Set GitHub token (stored securely with 0600 permissions)
oss-navi config --github-token ghp_your_token

# Set blog repository for publishing
oss-navi config --blog-repo /path/to/blog

# Set filter preferences
oss-navi config --min-stars 100 --max-age 30

# View current configuration
oss-navi config --list

# Reset to defaults
oss-navi config --reset
```

### `oss-navi sync`

Fetch GitHub profile and task data:

```bash
# Sync everything
oss-navi sync

# Sync only GitHub profile
oss-navi sync --github

# Sync only task sources
oss-navi sync --tasks

# Force refresh (ignore cache)
oss-navi sync --force

# Preview without fetching
oss-navi sync --dry-run
```

### `oss-navi analysis`

Generate personalized project recommendations:

```bash
# Generate recommendations
oss-navi analysis

# Focus on a technology you're learning
oss-navi analysis --learn python

# Save to custom location
oss-navi analysis --output my-recommendations.md

# Skip cache and require fresh data
oss-navi analysis --no-cache

# Open report after generation
oss-navi analysis --open
```

### `oss-navi publish`

Archive and publish analysis reports:

```bash
# Archive current report
oss-navi publish

# Archive and push to blog
oss-navi publish --push

# With custom commit message
oss-navi publish --push -m "Add weekly recommendations"

# List archived reports
oss-navi publish --list
```

### Global Options

```bash
# Enable verbose output
oss-navi -v sync

# Suppress non-essential output
oss-navi -q analysis

# Show version
oss-navi --version

# Show help
oss-navi --help
```

## Configuration

All data is stored under `~/.oss-navi/`:

```
~/.oss-navi/
├── .token              # GitHub token (secure, 0600 permissions)
├── cache/              # Cached data (24h expiration)
│   ├── github_profile.json
│   ├── upforgrabs_tasks.json
│   ├── goodfirstissue_tasks.json
│   └── metadata.json
├── state/              # Persistent data
│   ├── config.json
│   ├── memory.json
│   └── reports/
└── temp/               # Temporary files
    └── current_report.md
```

## Task Sources

OSS-Navi fetches tasks from:
- **Up For Grabs** (https://up-for-grabs.net) - JSON API
- **Good First Issue** (https://goodfirstissue.dev) - Web scraping

All URLs are validated to ensure they point to valid GitHub issues and repositories.

## Requirements

- Python 3.11+
- GitHub Personal Access Token (optional, for profile sync)
- Claude Code installed locally (for analysis command)

## Development

```bash
# Install development dependencies
uv sync --all-extras

# Run tests
pytest

# Run tests with coverage
pytest --cov=oss_navi --cov-report=term-missing

# Run linter
ruff check src/
```

## License

MIT
