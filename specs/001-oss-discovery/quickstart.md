# Quickstart: OSS-Navi CLI Tool

**Date**: 2026-03-07
**Feature**: 001-oss-discovery

## Prerequisites

Before installing OSS-Navi, ensure you have:

1. **Python 3.11+** installed
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Claude Code** installed and in PATH
   ```bash
   claude --version  # Verify Claude Code is available
   ```

3. **GitHub Personal Access Token**
   - Go to https://github.com/settings/tokens
   - Generate new token (classic)
   - Required scopes: `read:user`, `repo` (for private repos)
   - Save the token securely

4. **Git** (optional, for blog publishing)
   ```bash
   git --version
   ```

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/user/oss-navi.git
cd oss-navi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Verify installation
oss-navi --version
```

### From PyPI (Future)

```bash
pip install oss-navi
```

## Quick Start Guide

### Step 1: Configure OSS-Navi (1 minute)

```bash
# Set your GitHub username
oss-navi config --github-username your-username

# Set your GitHub token (stored securely with 0600 permissions)
oss-navi config --github-token ghp_your_token_here

# Verify configuration
oss-navi config --list
```

**Expected output**:
```
github_username: your-username
github_token: **** (configured)
filters:
  min_stars: 50
  max_age_days: 90
```

### Step 2: Sync Your Data (30 seconds)

```bash
# Fetch your GitHub profile and available tasks
oss-navi sync
```

**Expected output**:
```
✓ GitHub profile cached (245 repos, 12 languages)
✓ Up For Grabs: 156 tasks
✓ Good First Issues: 203 tasks
✓ Cache expires: 2026-03-08 10:00:00
```

### Step 3: Run Analysis (30-60 seconds)

```bash
# Generate personalized recommendations (interactive mode)
oss-navi analysis

# Or specify options directly
oss-navi analysis --learn python --explore -n 5

# Non-interactive mode for automation
oss-navi analysis --no-interactive --learn rust
```

**Expected output**:
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
     Rating: 8.5/10 - matches your Python expertise.
  2. Add CLI feature for data processing...
     Rating: 7.8/10 - aligns with your learning goal.

✓ Report saved: ~/.oss-navi/temp/current_report.md
```

**Analysis Options:**

| Option | Description |
|--------|-------------|
| `--learn <tech>` | Focus recommendations on a technology |
| `--explore` | Show adjacent field suggestions |
| `-n, --recommendations <N>` | Number of recommendations (5-10) |
| `--no-interactive` | Skip interactive prompts |

### Step 4: View Your Report

```bash
# Open the report
cat ~/.oss-navi/temp/current_report.md

# Or open in your editor
oss-navi analysis --open
```

## Common Workflows

### Weekly OSS Exploration

```bash
# Refresh data and get new recommendations
oss-navi sync --force
oss-navi analysis
```

### Learning a New Technology

```bash
# Focus recommendations on your learning goal
oss-navi analysis --learn python

# Get field exploration suggestions
oss-navi analysis --learn python --explore

# Specify number of recommendations
oss-navi analysis --learn python -n 10
```

### Quick Non-Interactive Analysis

```bash
# For CI/CD or automation scripts
oss-navi analysis --no-interactive --learn rust -n 5
```

### Share Your Journey

```bash
# Configure blog repository (one-time)
oss-navi config --blog-repo ~/my-blog

# Archive and publish report
oss-navi publish --push -m "Weekly OSS recommendations"
```

### Adjust Filtering

```bash
# Only show very popular, recent issues
oss-navi config --min-stars 500 --max-age 30

# Re-sync to apply new filters
oss-navi sync --tasks --force
```

### Proxy Configuration

If you're behind a corporate firewall or need to use a proxy:

```bash
# Configure HTTP proxy
oss-navi config --http-proxy http://proxy.example.com:8080

# Configure HTTPS proxy
oss-navi config --https-proxy http://proxy.example.com:8080

# Configure hosts to bypass proxy (comma-separated)
oss-navi config --no-proxy "localhost,127.0.0.1,.internal.example.com"
```

Alternatively, use environment variables (takes precedence):

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1

# Run oss-navi commands
oss-navi sync
```

## Directory Structure

OSS-Navi stores all data under `~/.oss-navi/`:

```
~/.oss-navi/
├── .token              # Your GitHub token (secure)
├── cache/              # Cached data (24h expiration)
│   ├── github_profile.json
│   ├── upforgrabs_tasks.json
│   └── goodfirstissues_tasks.json
├── state/              # Persistent data
│   ├── config.json     # Your settings
│   ├── memory.json     # Long-term memory
│   └── reports/        # Archived reports
└── temp/               # Temporary files
    └── current_report.md
```

## Troubleshooting

### "Configuration incomplete"

Run configuration first:
```bash
oss-navi config --github-username <username>
oss-navi config --github-token <token>
```

### "No cached data available"

Run sync first:
```bash
oss-navi sync
```

### "Claude Code not found"

Install Claude Code:
```bash
# Visit https://claude.ai/code for installation instructions
```

### "GitHub API rate limit exceeded"

Wait 1 hour for rate limit reset, or use cached data (valid for 24 hours).

### "Good First Issues unavailable"

OSS-Navi falls back to Up For Grabs data. Check your internet connection.

## Next Steps

1. Review your generated report
2. Explore recommended projects
3. Check out the suggested issues
4. Start contributing!

## Getting Help

```bash
# Show help for any command
oss-navi --help
oss-navi analysis --help

# Report issues
# https://github.com/user/oss-navi/issues
```
