# CLI Command Contracts: OSS-Navi

**Date**: 2026-03-07
**Feature**: 001-oss-discovery

This document defines the CLI interface contracts for OSS-Navi.

## Global Options

| Option | Type | Description |
|--------|------|-------------|
| `--help` | flag | Show help message and exit |
| `--version` | flag | Show version and exit |
| `--verbose` / `-v` | flag | Enable verbose output |
| `--quiet` / `-q` | flag | Suppress non-error output |

## Commands

### `oss-navi config`

Manage configuration settings.

#### Usage

```
oss-navi config [OPTIONS] [KEY] [VALUE]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| KEY | No | Configuration key to get/set |
| VALUE | No | Value to set (omitted for get) |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--github-username` | string | Set GitHub username |
| `--github-token` | string | Set GitHub personal access token |
| `--blog-repo` | string | Set blog repository path |
| `--min-stars` | integer | Set minimum stars filter |
| `--max-age` | integer | Set maximum issue age (days) |
| `--list` | flag | List all configuration values |
| `--reset` | flag | Reset configuration to defaults |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration error |
| 2 | Invalid argument |

#### Examples

```bash
# Set GitHub username
oss-navi config --github-username octocat

# Set GitHub token (will be stored securely)
oss-navi config --github-token ghp_xxxx

# View current configuration
oss-navi config --list

# Set filter preferences
oss-navi config --min-stars 100 --max-age 30

# Set blog repository for publishing
oss-navi config --blog-repo ~/my-blog
```

#### Output Format

**Success (get)**:
```
github_username: octocat
github_token: **** (configured)
blog_repo: /home/user/my-blog
filters:
  min_stars: 50
  max_age_days: 90
```

**Success (set)**:
```
✓ Configuration updated
```

---

### `oss-navi sync`

Fetch and cache GitHub profile and task data.

#### Usage

```
oss-navi sync [OPTIONS]
```

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--github` | flag | Sync GitHub profile only |
| `--tasks` | flag | Sync task sources only |
| `--force` | flag | Force refresh ignoring cache |
| `--dry-run` | flag | Show what would be fetched without fetching |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration missing (run config first) |
| 2 | Network/API error |
| 3 | Authentication error |

#### Examples

```bash
# Sync everything
oss-navi sync

# Sync only GitHub profile
oss-navi sync --github

# Force refresh all data
oss-navi sync --force

# See what would be fetched
oss-navi sync --dry-run
```

#### Output Format

**Success**:
```
✓ GitHub profile cached (245 repos, 12 languages)
✓ Up For Grabs: 156 tasks
✓ Good First Issues: 203 tasks
✓ Cache expires: 2026-03-08 10:00:00
```

**Partial success (one source failed)**:
```
✓ GitHub profile cached (245 repos, 12 languages)
✓ Up For Grabs: 156 tasks
⚠ Good First Issues: unavailable (using cached data)
✓ Cache expires: 2026-03-08 10:00:00
```

**Error (configuration missing)**:
```
✗ Configuration incomplete
  Run: oss-navi config --github-username <username>
```

---

### `oss-navi analysis`

Generate personalized project recommendations with enhanced analysis.

#### Usage

```
oss-navi analysis [OPTIONS]
```

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--learn` | string | Learning focus (technology/language) - optional, will prompt if omitted |
| `--explore` | string | Field(s) to explore (comma-separated) - optional, will prompt if omitted |
| `--output` / `-o` | string | Output file path (default: temp/current_report.md) |
| `--no-cache` | flag | Skip cache, require fresh data |
| `--open` | flag | Open report in default editor after generation |
| `--recommendations` / `-n` | integer | Number of recommendations (default: 7, range: 5-10) |
| `--no-interactive` | flag | Skip interactive prompts, use defaults/CLI args only |
| `--no-archive` | flag | Don't auto-archive report after generation |

#### Interactive Prompts

When run without `--no-interactive`, the command will prompt:

1. **Learning Interest**: "What are you currently learning or want to improve?"
   - Free text input
   - Suggestions based on profile languages

2. **Field Exploration**: "Any specific fields you'd like to explore?"
   - Multi-select from suggestions
   - Free text for custom entries

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration missing |
| 2 | No cached data (run sync first) |
| 3 | Claude Code not found |
| 4 | Analysis timeout |
| 5 | No matching tasks found |

#### Examples

```bash
# Run analysis with interactive prompts
oss-navi analysis

# Specify learning focus and fields to explore
oss-navi analysis --learn python --explore "web development,machine learning"

# Skip prompts, use CLI args only
oss-navi analysis --learn rust --no-interactive

# Get more recommendations
oss-navi analysis -n 10

# Output to specific file
oss-navi analysis -o ~/reports/oss-analysis.md

# Force fresh data and open result
oss-navi analysis --no-cache --open
```

#### Output Format

**Success (with interactive prompts)**:
```
✓ Analyzing profile... (12 languages, 245 repos)
? What are you currently learning? rust
? Any fields to explore? [web development, systems programming]
✓ Filtering tasks... (47 matches from 359 total)
✓ Checking issue status... (45 available, 2 assigned/closed)
✓ Generating recommendations via Claude Code...
✓ Report saved: ~/.oss-navi/temp/current_report.md
✓ Report archived: ~/.oss-navi/state/reports/report_20260307_100000.md

Top Recommendations (7 issues):
  1. [9.2/10] rust-lang/rust - Implement const fn for X
  2. [8.7/10] tokio-rs/tokio - Add documentation for Y
  3. [8.5/10] serde-rs/serde - Fix edge case in Z
  ... (4 more)

Great Projects to Study:
  • rust-analyzer/rust-analyzer - Modern IDE support for Rust
  • BurntSushi/ripgrep - Fast search tool with excellent code
```

**Success (non-interactive)**:
```
✓ Analyzing profile... (12 languages, 245 repos)
✓ Filtering tasks... (47 matches from 359 total)
✓ Checking issue status... (45 available)
✓ Generating recommendations via Claude Code...
✓ Report saved: ~/.oss-navi/temp/current_report.md
✓ Report archived: ~/.oss-navi/state/reports/report_20260307_100000.md
```

**Report Content Structure**:
```markdown
# OSS-Navi Analysis Report

## Skill Assessment
[Analysis of user's languages and activity]

## Learning Direction
[Advice based on stated interests + profile]

## Field Exploration
[Suggested adjacent fields with rationale]

## Recommended Issues (5-10)

### 1. [Rating 9.2/10] project/name - Issue Title
**Why this fits you**: [2-3 sentences]
**Code Analysis**: [Brief project structure analysis]
**Issue**: [Link and description]

[... more recommendations ...]

## Great Open Source Projects to Study

### Project 1: owner/repo
**Why study this**: [What makes it great]
**Architecture**: [Brief overview]
**Key Patterns**: [Notable patterns used]

[... more projects ...]

## Memory Updates
[Long-term memory section for persistence]
```

**Error (no cached data)**:
```
✗ No cached data available
  Run: oss-navi sync
```

**Error (Claude Code not found)**:
```
✗ Claude Code not found in PATH
  Install from: https://claude.ai/code
```

---

### `oss-navi publish`

Archive and optionally publish analysis reports.

#### Usage

```
oss-navi publish [OPTIONS] [REPORT]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| REPORT | No | Report file to publish (default: latest) |

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--push` | flag | Push to configured blog repository |
| `--message` / `-m` | string | Commit message for blog push |
| `--list` | flag | List archived reports |
| `--latest` | flag | Publish latest report |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No report to publish |
| 2 | Blog repository not configured |
| 3 | Git operation failed |

#### Examples

```bash
# Archive latest report
oss-navi publish

# Archive and push to blog
oss-navi publish --push

# Publish with custom commit message
oss-navi publish --push -m "Weekly OSS recommendations"

# List archived reports
oss-navi publish --list
```

#### Output Format

**Success (archive only)**:
```
✓ Report archived: ~/.oss-navi/state/reports/report_20260307_100000.md
```

**Success (archive and push)**:
```
✓ Report archived: ~/.oss-navi/state/reports/report_20260307_100000.md
✓ Pushed to blog: main branch
  https://github.com/user/blog/commit/abc123
```

**Error (no blog configured)**:
```
✗ Blog repository not configured
  Run: oss-navi config --blog-repo <path>
```

---

## Output Formats

### Standard Output

- All commands output to stdout
- Progress indicators use ✓ (success) and ✗ (error)
- Warnings use ⚠
- Verbose mode (`-v`) adds timestamps and additional details

### Error Output

- Errors written to stderr
- Include actionable remediation steps
- Exit code indicates error category

### JSON Output (Future)

`--json` flag will be available in future versions for programmatic consumption.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OSS_NAVI_HOME` | Override default data directory (default: `~/.oss-navi`) |
| `OSS_NAVI_CONFIG` | Path to config file |
| `GITHUB_TOKEN` | Fallback GitHub token if not configured |
| `HTTP_PROXY` | HTTP proxy URL (takes precedence over config) |
| `HTTPS_PROXY` | HTTPS proxy URL (takes precedence over config) |
| `NO_PROXY` | Comma-separated hosts to bypass proxy |

## Configuration File Format

**Location**: `~/.oss-navi/state/config.json`

```json
{
  "github_username": "octocat",
  "blog_repo_path": "/home/user/my-blog",
  "http_proxy": "http://proxy.example.com:8080",
  "https_proxy": "http://proxy.example.com:8080",
  "no_proxy": "localhost,127.0.0.1,.internal.example.com",
  "filters": {
    "min_stars": 50,
    "max_age_days": 90,
    "limit": 100
  },
  "created_at": "2026-03-07T10:00:00Z",
  "updated_at": "2026-03-07T12:00:00Z"
}
```

## Version Information

```
oss-navi --version
oss-navi/0.1.0 Python/3.11.0 Linux/6.18.9-arch1-2
```
