# OSS-Navi

> A CLI tool that helps programmers discover and contribute to open source projects

OSS-Navi analyzes your GitHub profile, scrapes beginner-friendly issues from multiple sources, and generates personalized project recommendations using Claude Code.

## Features

- **Profile Analysis**: Fetch and analyze your GitHub profile (commits, languages, activity)
- **Task Discovery**: Scrape open source tasks from Up For Grabs and Good First Issues
- **Smart Filtering**: Filter tasks by stars, recency, and compute a "hotness" score
- **Enhanced Recommendations**: Get 5-10 scored recommendations with detailed ratings
- **Issue Status Checking**: Verify recommended issues are still available (not assigned/closed)
- **Great Projects Discovery**: Find high-quality projects for learning (not just beginner-friendly)
- **Interactive Prompts**: Get suggestions for adjacent fields to explore
- **Learning Focus**: Specify what you're currently learning with `--learn` flag
- **AI Recommendations**: Generate personalized recommendations with Claude Code
- **Report Archiving**: Archive and optionally publish reports to your blog
- **Proxy Support**: Configure HTTP/HTTPS/SOCKS proxy for corporate firewalls

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

# Generate personalized recommendations (interactive)
oss-navi analysis

# Or specify options directly
oss-navi analysis --learn python --explore -n 5

# Non-interactive mode for automation
oss-navi analysis --no-interactive --learn rust
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

Generate personalized project recommendations with enhanced features:

```bash
oss-navi analysis                         # Generate recommendations (interactive)
oss-navi analysis --learn python          # Focus on a technology
oss-navi analysis -n 5                    # Get 5 recommendations (default: 7)
oss-navi analysis --explore               # Show field exploration suggestions
oss-navi analysis --no-interactive        # Skip interactive prompts
oss-navi analysis --output report.md      # Save to custom location
oss-navi analysis --no-cache              # Require fresh data
oss-navi analysis --open                  # Open report after generation
```

**Enhanced Analysis Output:**
```
✓ Analyzing profile... (12 languages, 245 repos)
✓ Filtering tasks... (47 matches from 359 total)

📚 Suggested fields to explore:
  1. web development
  2. data science
  3. automation

⭐ Great projects for learning:
  - python/cpython (60,000 stars)
    Highly popular with strong community.
  - pallets/flask (65,000 stars)
    Active community project.

✓ Generating 7 recommendations...

🎯 Top Recommendations:
  1. Fix authentication bug in web framework...
     Rating: 8.5/10 - matches your Python expertise and is beginner-friendly.
  2. Add CLI feature for data processing...
     Rating: 7.8/10 - aligns with your learning goal of Python.

✓ Report saved: ~/.oss-navi/temp/current_report.md
```

**Recommendation Scoring (6 factors):**

| Factor | Weight | Description |
|--------|--------|-------------|
| Language Match | 30% | How well it matches your known languages |
| Hotness Score | 20% | Popularity vs. issue age |
| Issue Availability | 15% | Is the issue unassigned and open? |
| Learning Alignment | 15% | Does it match your learning focus? |
| Skill Level Fit | 10% | Is it appropriate for your level? |
| Topic Relevance | 10% | Do topics align with your interests? |

**Issue Status Checking:**

Before recommending, OSS-Navi checks if issues are:
- ✅ Available (unassigned, open, no linked PR)
- ⚠️ Partially available (has "in progress" labels)
- ❌ Unavailable (assigned, closed, or has PR)

### `oss-navi publish`

Archive and publish analysis reports:

```bash
oss-navi publish                      # Archive current report locally
oss-navi publish --push               # Archive and push to configured blog repo
oss-navi publish --push -m "message"  # With custom commit message
oss-navi publish --list               # List archived reports
```

## Publishing Reports Online

### Recommended Approach: Static Site + Git

OSS-Navi uses a **git-based publishing workflow** instead of direct blog platform APIs. This approach is recommended because:

| Benefit | Description |
|---------|-------------|
| **Free Hosting** | GitHub Pages, Vercel, Netlify all offer free static hosting |
| **No API Limits** | Unlike Dev.to/Medium APIs, git has no rate limits |
| **Version Control** | Full history of all your reports |
| **Markdown Native** | No conversion needed - platforms render Markdown |
| **Custom Domains** | Use your own domain for free |
| **Zero Maintenance** | No API tokens to manage, no platform changes to handle |

### Setup: GitHub Pages (Recommended)

**Step 1: Create a reports repository**

```bash
# Create a new GitHub repository for your reports
gh repo create my-oss-journey --public

# Clone it locally
git clone https://github.com/YOUR_USERNAME/my-oss-journey.git
cd my-oss-journey

# Enable GitHub Pages (Settings → Pages → Source: main branch)
```

**Step 2: Configure OSS-Navi**

```bash
# Tell OSS-Navi where your blog repo is
oss-navi config --blog-repo /path/to/my-oss-journey
```

**Step 3: Generate and publish**

```bash
# Generate analysis
oss-navi analysis --learn python

# Archive and push to GitHub
oss-navi publish --push -m "Weekly OSS analysis - Python focus"
```

Your report is now live at: `https://YOUR_USERNAME.github.io/my-oss-journey/oss-navi/`

### Setup: Vercel/Netlify

Both platforms auto-deploy from GitHub:

1. Create a GitHub repository (same as Step 1 above)
2. Connect to [Vercel](https://vercel.com) or [Netlify](https://netlify.com)
3. They auto-detect Markdown and render it
4. Use `oss-navi publish --push` to update

### Alternative: Direct Blog Platform APIs

If you prefer direct integration with Dev.to, Medium, or Hashnode:

> **Note**: Direct API integration is complex because each platform uses different authentication, content formats (HTML vs Markdown vs "blocks"), and has rate limits. We recommend the git-based approach above for simplicity.

| Platform | Content Format | Draft API | Complexity |
|----------|----------------|-----------|------------|
| **Dev.to** | Markdown + frontmatter | ✅ Yes | Low |
| **Hashnode** | Markdown + GraphQL | ✅ Yes | Medium |
| **Medium** | HTML only | ❌ No | High |
| **Notion** | Block objects | ✅ Yes | Very High |

For Dev.to integration, you would need to:
1. Get an API key from dev.to/settings/extensions
2. Convert reports to their frontmatter format
3. Handle their rate limits (10 requests/30 seconds)

### Why Not Direct Blog APIs?

```
OSS-Navi Report (Markdown)
         │
         ├─→ Dev.to: Needs frontmatter, rate limits
         ├─→ Medium: Requires HTML conversion, no drafts
         ├─→ Hashnode: GraphQL complexity, publication workflow
         ├─→ Notion: Block-by-block API calls (50+ per report)
         │
         └─→ Git Repo: Just copy the file ✓
              │
              └─→ GitHub Pages/Vercel/Netlify auto-renders
```

The git-based approach is simpler, more reliable, and works everywhere.

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
│   ├── memory.json     # Long-term learning goals & past recommendations
│   └── reports/
└── temp/
    ├── current_report.md
    └── great_projects_cache.json  # Cached great projects (24h TTL)
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
| `No matching tasks found` | Lower `--min-stars` or increase `--max-age` |
| `All issues unavailable` | Issues may be assigned; wait for new tasks or try `--learn` for different projects |

## Development

```bash
uv sync --all-extras
pytest --cov=oss_navi --cov-report=term-missing
ruff check src/
```

## License

MIT
