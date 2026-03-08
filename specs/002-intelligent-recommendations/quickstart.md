# Quickstart: Intelligent Recommendations & Learning Paths

**Feature**: 002-intelligent-recommendations
**Date**: 2026-03-08

## Prerequisites

- Python 3.11+
- GitHub Personal Access Token (for profile sync)
- oss-navi installed (`pip install -e ".[dev]"`)

## Quick Setup

```bash
# 1. Configure GitHub credentials (if not done)
oss-navi config --github-username YOUR_USERNAME
oss-navi config --github-token YOUR_TOKEN

# 2. Set your language preferences
oss-navi prefs set-language python --type primary --level advanced
oss-navi prefs set-language go --type secondary --level intermediate
oss-navi prefs set-language rust --type learning --level beginner

# 3. Sync profile and learning resources
oss-navi sync
oss-navi sync --learning
```

## Basic Usage

### Recommendation Modes

OSS-Navi offers three recommendation modes with different trade-offs:

| Mode | Command | Time | Memory | Best For |
|------|---------|------|--------|----------|
| **Fast** | `--mode fast` | <30s | <50MB | Quick exploration, CI/CD |
| **Normal** | `--mode normal` (default) | <90s | <200MB | Daily use |
| **Thinking** | `--mode thinking` | <180s | <500MB | Deep analysis |

**Installation Requirements**:
- **Fast mode**: Works with minimal installation
- **Normal/Thinking modes**: Requires `pip install oss-navi[recommend]`

### Interactive Recommendations (Recommended)

```bash
# Start interactive recommendation session (normal mode)
oss-navi recommend

# Fast mode for quick results
oss-navi recommend --mode fast

# Thinking mode for best quality
oss-navi recommend --mode thinking

# The system will:
# 1. Analyze your GitHub profile + preferences
# 2. Generate initial recommendations with scores
# 3. Suggest learning resources automatically
# 4. Let you accept/reject/request alternatives
# 5. Allow multiple rounds of refinement
```

### Non-Interactive (One-Shot)

```bash
# Generate recommendations without interaction
oss-navi recommend --non-interactive --output report.md

# Fast one-shot for CI/CD
oss-navi recommend --mode fast --non-interactive
```

### Learning Focus

```bash
# Focus on learning a specific technology
oss-navi recommend --learn rust

# The system will:
# 1. Mark rust as learning prerequisite (if no Rust tasks found)
# 2. Recommend adjacent technologies (C/C++, Go)
# 3. Suggest rust-specific courses and tutorials
# 4. Include LeetCode/Codeforces problems for fundamentals
```

## Interactive Session Flow

```
$ oss-navi recommend

🔍 Analyzing your profile...
✓ Found 3 primary languages: Python, Go, JavaScript
✓ Loaded 1,247 cached tasks
✓ Synced learning resources

═══════════════════════════════════════════════════════════
ROUND 1: Language Match (Python)
═══════════════════════════════════════════════════════════

📦 fastapi/fastapi (Score: 9/10)
   Language: Python | Stars: 75.2k
   Why: Matches your Python expertise and web development interests
   Skills: async patterns, API design, type hints
   Issue: Add OpenAPI validation for edge cases
   🔗 https://github.com/fastapi/fastapi/issues/12345

📦 django/django (Score: 8/10)
   Language: Python | Stars: 78.1k
   Why: Popular framework matching your skill level
   Skills: ORM patterns, migrations, authentication
   Issue: Improve queryset performance
   🔗 https://github.com/django/django/issues/67890

───────────────────────────────────────────────────────────
📚 Learning Resources (Auto-suggested)
───────────────────────────────────────────────────────────
• LeetCode: Two Sum (Easy) - Arrays
• Codeforces: Problem 4A (Rating 800) - Basics
• csdiy.wiki: MIT 6.006 - Introduction to Algorithms

───────────────────────────────────────────────────────────
What would you like to do?
[A] Accept  [R] Reject  [D] Detailed analysis
[S] Alternatives  [M] Modify report  [N] Next round  [F] Finalize
```

## Managing Preferences

```bash
# View current preferences
oss-navi prefs show

# Add blocking rule
oss-navi prefs block language typescript --reason "Not interested"

# Remove language
oss-navi prefs remove-language ruby

# Export preferences
oss-navi prefs export my-prefs.json

# Import preferences
oss-navi prefs import my-prefs.json
```

## Session Management

```bash
# List active sessions
oss-navi session list

# Resume a session
oss-navi recommend --session abc123

# Export session report
oss-navi session export abc123 --output my-report.md

# Delete old session
oss-navi session delete abc123
```

## Detailed Code Analysis

```bash
# Analyze a specific repository
oss-navi analyze fastapi/fastapi

# Add analysis to current session
oss-navi analyze django/django --add-to-session
```

## Performance Tips

1. **Choose the right mode**: Use `--mode fast` for quick exploration, `--mode thinking` for important decisions
2. **Sync learning resources separately**: Run `oss-navi sync --learning` during off-peak times
3. **Use cached data**: Non-interactive mode is faster for repeated queries
4. **Limit rounds**: Use `--rounds 2` for quicker sessions
5. **Resume sessions**: Don't re-analyze; resume existing sessions

## Installation Options

```bash
# Minimal installation (fast mode only)
pip install oss-navi

# With recommendation algorithms (normal/thinking modes)
pip install oss-navi[recommend]

# Full development installation
pip install -e ".[dev,recommend]"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No recommendations found" | Broaden language preferences or use `--learn` flag |
| "API rate limit reached" | Wait 1 hour or use cached data (automatic fallback) |
| "Session not found" | Sessions expire after 7 days; start new session |
| "Learning resources unavailable" | Run `oss-navi sync --learning --force` |
| "LightFM not installed" | Run `pip install oss-navi[recommend]` or use `--mode fast` |
| "Mode unavailable" | System will fall back to a compatible mode automatically |

## Directory Structure

```
~/.oss-navi/
├── cache/
│   ├── github_profile.json    # Your GitHub data
│   ├── tasks.json             # Cached OSS tasks
│   ├── leetcode.json          # LeetCode problems
│   ├── codeforces.json        # Codeforces problems
│   └── csdiy.json             # csdiy.wiki courses
├── state/
│   ├── preferences.json       # Your preferences
│   ├── patterns.json          # Learned recommendation patterns
│   ├── sessions/              # Active sessions
│   └── reports/               # Archived reports
└── temp/
    └── (temporary files)
```

## Next Steps

1. Run `oss-navi recommend` to start your first session
2. Accept/reject recommendations to train the system
3. Request detailed analysis for promising projects
4. Finalize your report and start contributing!
