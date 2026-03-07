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
| great_projects | GreatProject[] | No | Great open source projects analyzed |
| archived_at | datetime | No | When report was archived |

**Report Structure**:
1. Skill Assessment (derived from GitHub profile)
2. Learning Direction & Field Exploration Advice
3. 5-10 Recommendations with:
   - Rating (1-10)
   - Recommendation reason
   - Brief code analysis
4. Great Open Source Projects Analysis (2-3 projects)
5. Long-term Memory Update section

### IssueStatus

Real-time status of an issue (not cached, checked on-demand).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| issue_url | string | Yes | GitHub issue URL |
| is_assigned | boolean | Yes | True if issue has assignee |
| assignee | string | No | Assignee username if assigned |
| is_closed | boolean | Yes | True if issue is closed |
| has_linked_pr | boolean | Yes | True if issue IS a PR (pull_request key in response) |
| has_open_pr | boolean | No | True if separate open PR is linked to this issue |
| linked_pr_url | string | No | URL of linked PR if has_open_pr is true |
| in_progress_labels | string[] | No | Labels indicating work in progress |
| checked_at | datetime | Yes | When status was checked |

**Status Determination**:
- Available: `!is_assigned && !is_closed && !has_linked_pr && !has_open_pr`
- Unavailable: Any of the above is true

**Linked PR Detection** (NEW):
- Uses GitHub Issue Timeline API
- Looks for `cross-referenced` events with open PRs
- Only checked for top candidates to avoid rate limits

### Recommendation

A scored recommendation for a specific task/issue.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task | Task | Yes | The recommended task |
| rating | float | Yes | Score 1.0-10.0 |
| rating_breakdown | RatingBreakdown | Yes | Detailed score components |
| reason | string | Yes | Why this fits the user (2-3 sentences) |
| code_analysis | string | Yes | Brief analysis of project code |
| status | IssueStatus | Yes | Current issue availability |

### RatingBreakdown

Detailed scoring components for a recommendation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| language_match | float | Yes | 0-10: How well languages align |
| hotness_score | float | Yes | 0-10: Normalized popularity score |
| issue_availability | float | Yes | 0-10: 10 if available, 0 if taken |
| learning_alignment | float | Yes | 0-10: Match with learning goals |
| skill_level_fit | float | Yes | 0-10: Appropriate difficulty |
| topic_relevance | float | Yes | 0-10: Project topic match |
| weighted_total | float | Yes | Final weighted score |

**Weights**: language_match (30%), hotness (20%), availability (15%), learning (15%), skill (10%), topic (10%)

### GreatProject

An excellent open source project for learning (not necessarily beginner-friendly).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Repository name (owner/repo) |
| url | string | Yes | Repository URL |
| stars | integer | Yes | Star count |
| language | string | Yes | Primary language |
| why_great | string | Yes | Why this is a great project to study |
| architecture_overview | string | Yes | Brief architecture analysis |
| key_patterns | string[] | Yes | Notable patterns used |
| contribution_areas | string[] | Yes | Good areas for intermediate contribution |
| relevance_reason | string | Yes | Why relevant to user's skills/goals |

### LearningSession

Captured during interactive analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | UUID for this analysis session |
| created_at | datetime | Yes | Session timestamp |
| primary_interest | string | Yes | What user is currently learning |
| explore_fields | string[] | No | Fields user wants to explore |
| suggested_fields | string[] | No | AI-suggested adjacent fields |

### LongTermMemory

Persistent memory stored in `~/.oss-navi/state/memory.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | integer | Yes | Schema version (currently 3) |
| created_at | datetime | Yes | Memory creation date |
| updated_at | datetime | Yes | Last update timestamp |
| skill_history | SkillSnapshot[] | Yes | Historical skill assessments |
| past_recommendations | PastRecommendation[] | Yes | Previously recommended projects |
| learning_goals | string[] | No | Accumulated learning focuses |
| great_projects_discovered | GreatProjectSummary[] | No | Great projects shown to user |
| field_exploration_history | FieldExploration[] | No | Fields user has explored |
| github_profile | GitHubProfileSummary | No | Cached GitHub profile summary |
| last_analysis_date | datetime | No | Date of last analysis run |
| analysis_count | integer | No | Total number of analyses run |

### GitHubProfileSummary

Cached summary of user's GitHub profile for quick reference.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | GitHub username |
| primary_languages | dict[string, float] | Yes | Top languages with percentages |
| total_repos | integer | Yes | Number of public repos |
| last_fetched | datetime | Yes | When profile was last synced |

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
| rating | float | No | Rating given (1-10) |
| status | string | No | User's status (viewed, attempted, completed) |

### GreatProjectSummary

Brief record of a great project shown to user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Repository name |
| shown_at | datetime | Yes | When it was recommended |
| reason | string | Yes | Why it was relevant |

### FieldExploration

Record of field exploration advice given.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| date | datetime | Yes | When advice was given |
| current_interest | string | Yes | User's stated interest |
| suggested_fields | string[] | Yes | Fields suggested to explore |
| rationale | string | Yes | Why these fields were suggested |

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
