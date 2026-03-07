# OSS-Navi

> A CLI tool that helps programmers discover and contribute to open source projects

OSS-Navi analyzes your GitHub profile, scrapes beginner-friendly issues from multiple sources, and generates personalized project recommendations using Claude Code.

## Features

- **Profile Analysis**: Fetch and analyze your GitHub profile (commits, languages, activity)
- **Task Discovery**: Scrape open source tasks from Up For Grabs and Good First Issues
- **Smart Filtering**: Filter tasks by stars, recency, and compute a "hotness" score
- **Learning Focus**: Specify what you're currently learning with `--learn` flag
- **AI Recommendations**: Generate personalized recommendations with Claude Code
- **Report Archiving**: Archive and optionally publish reports to your blog
- **Proxy Support**: Configure HTTP/HTTPS proxy for corporate firewalls

## Requirements

- Python 3.11+ or [uv](https://docs.astral.sh/uv/) package manager
- GitHub Personal Access Token (optional, for profile sync)
- Claude Code installed locally (for analysis command)

## Installation

**One-line setup (Linux/macOS/Windows):**

```bash
# Clone and install as global CLI tool
git clone https://github.com/Code-Test-Source/oss-navi.git && cd oss-navi && uv tool install -e .
```

After installation, `oss-navi` is available globally:

```bash
oss-navi --version
oss-navi --help
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
oss-navi config --github-username your-username
oss-navi config --github-token ghp_your_token
oss-navi config --blog-repo /path/to/blog
oss-navi config --min-stars 100 --max-age 30
oss-navi config --http-proxy http://proxy.example.com:8080
oss-navi config --https-proxy http://proxy.example.com:8080
oss-navi config --list
oss-navi config --reset
```

### `oss-navi sync`

Fetch GitHub profile and task data:

```bash
oss-navi sync              # Sync everything
oss-navi sync --github     # Sync only GitHub profile
oss-navi sync --tasks      # Sync only task sources
oss-navi sync --force      # Force refresh (ignore cache)
oss-navi sync --dry-run    # Preview without fetching
```

**Expected Output:**
```
✓ GitHub profile cached (245 repos, 12 languages)
✓ Up For Grabs: 156 tasks
✓ Good First Issues: 203 tasks
✓ Cache expires: 2026-03-08 10:00:00
```

### `oss-navi analysis`

Generate personalized project recommendations:

```bash
oss-navi analysis                    # Generate recommendations
oss-navi analysis --learn python     # Focus on a technology
oss-navi analysis --output report.md # Save to custom location
oss-navi analysis --no-cache         # Require fresh data
oss-navi analysis --open             # Open report after generation
```

**Expected Output:**
```
✓ Analyzing profile... (12 languages, 245 repos)
✓ Filtering tasks... (47 matches from 359 total)
✓ Generating recommendations via Claude Code...
✓ Report saved: ~/.oss-navi/temp/current_report.md
```

### `oss-navi publish`

Archive and publish analysis reports:

```bash
oss-navi publish                      # Archive current report
oss-navi publish --push               # Archive and push to blog
oss-navi publish --push -m "message"  # With custom commit message
oss-navi publish --list               # List archived reports
```

### Global Options

```bash
oss-navi -v sync        # Verbose output
oss-navi -q analysis    # Quiet mode
oss-navi --version      # Show version
oss-navi --help         # Show help
```

## Configuration

All data is stored under `~/.oss-navi/`:

```
~/.oss-navi/
├── .token              # GitHub token (secure, 0600 permissions)
├── cache/              # Cached data (24h expiration)
│   ├── github_profile.json
│   ├── upforgrabs_tasks.json
│   ├── goodfirstissues_tasks.json
│   └── metadata.json
├── state/              # Persistent data
│   ├── config.json
│   ├── memory.json
│   └── reports/
└── temp/
    └── current_report.md
```

## Task Sources

| Source | URL | Method |
|--------|-----|--------|
| **Up For Grabs** | https://up-for-grabs.net | GitHub API (YAML) |
| **Good First Issues** | https://goodfirstissues.com | JSON API |

## Proxy Configuration

```bash
# Via CLI
oss-navi config --http-proxy http://proxy:8080
oss-navi config --https-proxy http://proxy:8080
oss-navi config --no-proxy "localhost,127.0.0.1"

# Via environment variables (takes precedence)
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080
export NO_PROXY=localhost,127.0.0.1
```

### SSL Verification

If your proxy uses self-signed certificates (e.g., FastGitHub), disable SSL verification:

```bash
export OSS_NAVI_VERIFY_SSL=false
oss-navi sync --force
```

Or inline:
```bash
OSS_NAVI_VERIFY_SSL=false oss-navi sync --force
```

> **Note**: SOCKS proxies (socks5://) are supported via the `httpx[socks]` dependency.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `command not found` | Run `uv tool install -e .` to install as global CLI |
| `Configuration incomplete` | Run `oss-navi config --github-username <user>` |
| `No cached data` | Run `oss-navi sync` |
| `Claude Code not found` | Install from https://claude.ai/code |
| `Rate limit exceeded` | Wait 1 hour or use cached data |

## Development

```bash
uv sync --all-extras
pytest --cov=oss_navi --cov-report=term-missing
ruff check src/
```

## License

MIT
