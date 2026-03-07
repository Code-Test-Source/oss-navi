# Data Model: OSS-Navi CLI Tool

**Date**: 2026-03-07
**Feature**: 001-oss-discovery

## Entity Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│    Config   │     │ UserProfile │     │     Task        │
└─────────────┘     └─────────────┘     └─────────────────┘
       │                   │                    │
       │                   │                    │
       ▼                   ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Filters   │     │  Language   │     │   Repository    │
└─────────────┘     └─────────────┘     └─────────────────┘
                                               │
                           ┌───────────────────┘
                           ▼
                    ┌─────────────────┐
                    │ AnalysisReport  │
                    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │ LongTermMemory  │
                    └─────────────────┘
```

## Entities

### Config

User configuration stored in `~/.oss-navi/state/config.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| github_username | string | Yes | GitHub username for profile fetching |
| github_token | string | Yes* | Personal access token (stored in separate file) |
| blog_repo_path | string | No | Local path to blog repository for publishing |
| filters | Filters | No | Task filtering preferences |
| created_at | datetime | Yes | Configuration creation timestamp |
| updated_at | datetime | Yes | Last modification timestamp |

*Token stored in `~/.oss-navi/.token` with 0600 permissions

**Validation Rules**:
- `github_username`: 1-39 characters, alphanumeric and hyphens only, cannot start/end with hyphen
- `github_token`: Must start with `ghp_`, `gho_`, `ghu_`, or `ghs_` (GitHub token prefixes)
- `blog_repo_path`: Must be valid directory path if provided

### Filters

Task filtering configuration.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| min_stars | integer | 50 | Minimum repository stars |
| max_age_days | integer | 90 | Maximum issue age in days |
| limit | integer | 100 | Maximum tasks to fetch per source |

**Validation Rules**:
- `min_stars`: 0-1000000
- `max_age_days`: 1-365
- `limit`: 1-1000

### UserProfile

GitHub user profile data cached in `~/.oss-navi/cache/github_profile.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | GitHub username |
| name | string | No | Display name |
| bio | string | No | User bio |
| public_repos | integer | Yes | Number of public repositories |
| followers | integer | Yes | Follower count |
| following | integer | Yes | Following count |
| languages | dict[string, float] | Yes | Language usage percentages |
| recent_activity | Activity[] | Yes | Recent commits/events |
| top_repos | Repository[] | Yes | Top repositories by stars/activity |
| fetched_at | datetime | Yes | Cache timestamp |
| expires_at | datetime | Yes | Cache expiration (24h from fetched_at) |

### Activity

Recent GitHub activity entry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Event type (PushEvent, PullRequestEvent, etc.) |
| repo_name | string | Yes | Repository name (owner/repo) |
| created_at | datetime | Yes | Event timestamp |
| details | dict | No | Event-specific details |

### Language

Programming language statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Language name (Python, TypeScript, etc.) |
| bytes | integer | Yes | Total bytes across all repos |
| percentage | float | Yes | Percentage of total code (0.0-1.0) |

### Task

Open source contribution opportunity from scraped sources.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (source:issue_number) |
| title | string | Yes | Issue title |
| description | string | No | Issue description (truncated to 500 chars) |
| url | string | Yes | Issue URL |
| source | string | Yes | Source (upforgrabs, goodfirstissues) |
| repository | Repository | Yes | Parent repository info |
| labels | string[] | Yes | Issue labels |
| created_at | datetime | Yes | Issue creation timestamp |
| updated_at | datetime | Yes | Issue last update timestamp |
| hotness_score | float | Yes | Calculated: stars / age_in_days |
| fetched_at | datetime | Yes | Cache timestamp |

**Hotness Score Formula**:
```
hotness_score = repository.stars / max(age_in_days, 1)
```

Higher score = more popular and newer issue.

### Repository

GitHub repository information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Repository name (owner/repo) |
| url | string | Yes | Repository URL |
| stars | integer | Yes | Star count |
| language | string | No | Primary language |
| description | string | No | Repository description |
| topics | string[] | No | Repository topics/tags |
| is_archived | boolean | No | Whether repository is archived |
| last_updated | datetime | No | Last push timestamp |

### AnalysisReport

Generated Markdown report with recommendations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Timestamp-based ID (YYYYMMDD_HHMMSS) |
| created_at | datetime | Yes | Report generation timestamp |
| content | string | Yes | Full Markdown content |
| file_path | string | Yes | Path to saved report |
| learning_focus | string | No | User's learning focus if provided |
| recommended_projects | string[] | Yes | List of recommended repo names |

**Report Structure**:
1. Skill Assessment (derived from GitHub profile)
2. Learning Direction (influenced by --learn flag)
3. Top 1-2 Recommendations with code reading hints
4. Long-term Memory Update section

### LongTermMemory

Persistent memory stored in `~/.oss-navi/state/memory.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | integer | Yes | Schema version (currently 1) |
| created_at | datetime | Yes | Memory creation date |
| updated_at | datetime | Yes | Last update timestamp |
| skill_history | SkillSnapshot[] | Yes | Historical skill assessments |
| past_recommendations | PastRecommendation[] | Yes | Previously recommended projects |
| learning_goals | string[] | No | Accumulated learning focuses |

### SkillSnapshot

Point-in-time skill assessment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| date | datetime | Yes | Snapshot date |
| languages | dict[string, float] | Yes | Language percentages |
| top_repos | string[] | Yes | Top 5 repo names |
| focus_areas | string[] | No | Learning focuses active at this time |

### PastRecommendation

Record of a previous project recommendation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| date | datetime | Yes | Recommendation date |
| project | string | Yes | Repository name (owner/repo) |
| issue_url | string | Yes | Specific issue URL |
| reason | string | No | Why it was recommended |
| status | string | No | User's status (viewed, attempted, completed) |

## State Transitions

### Cache Lifecycle

```
┌─────────┐    sync    ┌─────────┐   24h    ┌─────────┐
│  Empty  │ ─────────▶ │  Fresh  │ ───────▶ │ Stale   │
└─────────┘            └─────────┘          └─────────┘
                            │                     │
                            │                     │
                            ▼                     ▼
                       [analysis]           [sync or use with warning]
                            │
                            ▼
                      ┌─────────┐
                      │ Used    │
                      └─────────┘
```

### Report Lifecycle

```
┌─────────┐  analysis  ┌─────────┐  publish  ┌─────────┐
│   N/A   │ ─────────▶ │  temp/  │ ────────▶ │ state/  │
└─────────┘            └─────────┘           └─────────┘
                            │
                            │ archive
                            ▼
                       [saved with timestamp]
```

## File Storage

### Directory Structure

```
~/.oss-navi/
├── .token                    # GitHub PAT (0600 permissions)
├── cache/
│   ├── github_profile.json   # UserProfile cache
│   ├── upforgrabs_tasks.json # Task[] from Up For Grabs
│   ├── goodfirstissues_tasks.json # Task[] from Good First Issues
│   └── metadata.json         # Cache timestamps
├── state/
│   ├── config.json           # Configuration
│   ├── memory.json           # LongTermMemory
│   └── reports/
│       └── report_YYYYMMDD_HHMMSS.md
└── temp/
    └── current_report.md     # Latest analysis (before archive)
```

### Cache Metadata

```json
{
  "version": 1,
  "caches": {
    "github_profile": {
      "fetched_at": "2026-03-07T10:00:00Z",
      "expires_at": "2026-03-08T10:00:00Z",
      "is_valid": true
    },
    "upforgrabs_tasks": {
      "fetched_at": "2026-03-07T10:00:00Z",
      "expires_at": "2026-03-08T10:00:00Z",
      "count": 150,
      "is_valid": true
    },
    "goodfirstissues_tasks": {
      "fetched_at": "2026-03-07T10:00:00Z",
      "expires_at": "2026-03-08T10:00:00Z",
      "count": 200,
      "is_valid": true
    }
  }
}
```
