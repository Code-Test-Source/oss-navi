# OSS-Navi

> A CLI tool that helps programmers discover and contribute to open source projects

OSS-Navi analyzes your GitHub profile, scrapes beginner-friendly issues from multiple sources, and generates personalized project recommendations with intelligent algorithms.

## Features

- **Profile Analysis**: Fetch and analyze your GitHub profile (commits, languages, activity)
- **Task Discovery**: Scrape open source tasks from Up For Grabs and Good First Issues
- **Intelligent Recommendations**: Three recommendation modes (fast, normal, thinking) with algorithmic scoring
- **Smart Filtering**: Filter tasks by stars, recency, and compute a "hotness" score
- **Learning Paths**: Automatic suggestions from csdiy.wiki, LeetCode, Codeforces
- **Personalization**: Set language preferences, skill levels, and blocking rules
- **Multi-Round Sessions**: Interactive recommendations with feedback tracking
- **Great Projects Discovery**: Find high-quality projects for learning
- **Proxy Support**: Configure HTTP/HTTPS/SOCKS proxy for corporate firewalls

## Requirements

- Python 3.11+ or [uv](https://docs.astral.sh/uv/) package manager
- GitHub Personal Access Token (optional, for profile sync)
- Claude Code (optional, for enhanced AI-powered analysis reports)

## Installation

**One-line setup (Linux/macOS/Windows):**

```bash
# Clone and install as global CLI tool
git clone https://github.com/Code-Test-Source/oss-navi.git && cd oss-navi && uv tool install -e .

# For recommendation algorithms (normal/thinking modes)
uv tool install -e ".[recommend]"

# For scraping with user agent rotation
uv tool install -e ".[scrape]"
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

# Set your language preferences
oss-navi prefs set-language python --type primary --level advanced
oss-navi prefs set-language rust --type learning --level beginner

# Sync your profile, tasks, and learning resources
oss-navi sync
oss-navi sync --learning

# Generate personalized recommendations
oss-navi analysis --mode normal

# Fast mode for quick results (<30s)
oss-navi analysis --mode fast
```

## Commands

### `oss-navi analysis`

Generate personalized project recommendations combining intelligent algorithms with Claude Code:

```bash
oss-navi analysis                         # Interactive recommendations (normal mode)
oss-navi analysis --mode fast             # Quick exploration (<30s)
oss-navi analysis --mode normal           # Balanced quality (<90s)
oss-navi analysis --mode thinking         # Best quality (<180s)
oss-navi analysis --language go           # Focus on specific language
oss-navi analysis --learn rust            # Learning focus
oss-navi analysis --session abc123        # Resume session
oss-navi analysis --no-interactive        # One-shot mode
oss-navi analysis --explore               # Show field exploration suggestions
oss-navi analysis --output report.md      # Save report to file
```

**Two-Layer Recommendation System:**

1. **Intelligent Recommendations** (algorithmic): Content-based filtering, collaborative filtering (Surprise), and pattern mining (Apriori/LightFM)
2. **Claude Code Analysis** (AI-powered): Deep project insights, contribution guidance, and personalized learning paths

**Recommendation Modes:**

| Mode | Algorithms | Time | Memory | Use Case |
|------|------------|------|--------|----------|
| `fast` | Content-based filtering | <30s | <50MB | Quick exploration, CI/CD |
| `normal` | Surprise SVD/KNN | <90s | <200MB | Daily use (default) |
| `thinking` | LightFM + Apriori | <180s | <500MB | Deep analysis |

### `oss-navi prefs`

Manage user preferences:

```bash
oss-navi prefs set-language python --type primary --level advanced
oss-navi prefs set-language rust --type learning --level beginner
oss-navi prefs remove-language ruby
oss-navi prefs block language typescript --reason "Not interested"
oss-navi prefs block organization some-org
oss-navi prefs unblock language typescript
oss-navi prefs show
oss-navi prefs export my-prefs.json
oss-navi prefs import my-prefs.json
```

### `oss-navi session`

Manage recommendation sessions:

```bash
oss-navi session list              # List active sessions
oss-navi session list --status all # List all sessions
oss-navi session show abc123       # Show session details
oss-navi session export abc123     # Export as markdown
oss-navi session export abc123 --format json
oss-navi session delete abc123     # Delete session
```

### `oss-navi sync`

Fetch GitHub profile, tasks, and learning resources:

```bash
oss-navi sync                    # Sync profile and tasks
oss-navi sync --learning         # Sync learning resources
oss-navi sync --csdiy            # Sync csdiy.wiki courses
oss-navi sync --leetcode         # Sync LeetCode problems
oss-navi sync --codeforces       # Sync Codeforces problems
oss-navi sync --force            # Force refresh
```

**Data Sources (no API rate limits):**

| Source | Dataset | Items |
|--------|---------|-------|
| LeetCode | neenza/leetcode-problems | 2,500+ problems |
| Codeforces | Kaggle/HuggingFace | 7,000+ problems |
| csdiy.wiki | Direct scrape | 150+ courses |

### `oss-navi config`

Manage configuration settings:

```bash
oss-navi config --github-username your-username
oss-navi config --github-token ghp_your_token
oss-navi config --blog-repo /path/to/blog
oss-navi config --min-stars 100 --max-age 30
oss-navi config --http-proxy http://proxy.example.com:8080
oss-navi config --list
oss-navi config --reset
```

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
│   ├── leetcode.json       # LeetCode problems
│   ├── codeforces.json     # Codeforces problems
│   ├── csdiy.json          # csdiy.wiki courses
│   └── metadata.json
├── state/              # Persistent data
│   ├── config.json
│   ├── preferences.json    # User preferences (languages, blocking rules)
│   ├── memory.json         # Long-term learning goals
│   ├── sessions/           # Recommendation sessions
│   └── reports/
└── temp/
    ├── current_report.md
    └── great_projects_cache.json
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
| `Rate limit exceeded` | Use `--skip-status` flag or wait 1 hour |
| `No matching tasks found` | Lower `--min-stars` or increase `--max-age` |
| `All issues unavailable` | Issues may be assigned; wait for new tasks or try `--learn` for different projects |
| `Slow analysis` | Use `--skip-status` to skip API calls |

## Development

```bash
uv sync --all-extras
pytest --cov=oss_navi --cov-report=term-missing
ruff check src/
```

## Long-Term Memory

OSS-Navi maintains a persistent memory of your learning journey:

```bash
~/.oss-navi/state/memory.json
```

**What's stored:**
- `skill_history`: Your language distribution over time
- `past_recommendations`: Issues you've been recommended
- `learning_goals`: Technologies you've expressed interest in
- `great_projects_discovered`: High-quality projects shown to you
- `github_profile`: Cached summary of your GitHub profile

**How it's used:**
1. **Better recommendations**: Avoid recommending the same issues twice
2. **Context enrichment**: Claude Code sees your history when generating advice
3. **Progress tracking**: See how your skills evolve over time

Memory is automatically updated after each analysis - no extra flags needed.

## License

MIT
