# Research: OSS-Navi CLI Tool

**Date**: 2026-03-07 (Updated)
**Feature**: 001-oss-discovery

## Technology Decisions

### Language: Python 3.11+

**Decision**: Python 3.11+

**Rationale**:
- Excellent CLI ecosystem (click, typer, rich)
- Strong HTTP client libraries (httpx, requests)
- Mature web scraping tools (beautifulsoup4, lxml)
- Native subprocess support for Claude Code invocation
- Cross-platform compatibility
- Good for JSON manipulation and file I/O

**Alternatives Considered**:
- **Go**: Faster execution, single binary distribution, but smaller ecosystem for web scraping
- **Rust**: High performance, but steeper learning curve and more complexity for a CLI tool
- **Node.js**: Good CLI tools, but Python has better data science/scripting ergonomics

### CLI Framework: Click

**Decision**: Click

**Rationale**:
- De facto standard for Python CLI apps
- Decorator-based command definition (clean, readable)
- Built-in help generation
- Support for subcommands (config, sync, analysis, publish)
- Type conversion and validation

**Alternatives Considered**:
- **Typer**: Simpler API but built on Click, adds dependency for marginal benefit
- **Argparse**: Built-in, but more verbose and less feature-rich
- **Rich CLI**: Great for output formatting, can be combined with Click

### HTTP Client: httpx

**Decision**: httpx

**Rationale**:
- Modern async/sync HTTP client
- Better API than requests for both modes
- Excellent timeout and retry support
- Good for GitHub API and web scraping
- **Supports async for parallel requests** (added for performance)

**Alternatives Considered**:
- **requests**: Battle-tested but synchronous only, older API design
- **aiohttp**: Async-only, more complex for mixed sync/async needs

### Web Scraping: BeautifulSoup4 + lxml

**Decision**: BeautifulSoup4 with lxml parser

**Rationale**:
- Industry standard for Python web scraping
- Forgiving parser handles imperfect HTML
- lxml backend is fast and robust
- Easy to extract data from static pages

**Alternatives Considered**:
- **Scrapy**: Overkill for simple scraping of 1-2 websites
- **Playwright/Selenium**: Overkill for static content, adds browser dependency
- **parsel**: Good but less community support than BeautifulSoup

### Data Validation: Pydantic v2

**Decision**: Pydantic v2

**Rationale**:
- Excellent for data models with validation
- JSON serialization built-in
- Type hints integration
- Settings management for configuration
- v2 is significantly faster than v1

**Alternatives Considered**:
- **dataclasses**: Built-in but no validation, JSON serialization requires extra work
- **attrs**: Good but Pydantic's validation and JSON support are superior
- **marshmallow**: More verbose, slower than Pydantic v2

### Testing: pytest + pytest-cov

**Decision**: pytest with pytest-cov

**Rationale**:
- Standard Python testing framework
- Excellent fixture system for test data
- Coverage reporting built-in
- Plugin ecosystem (pytest-httpx for mocking HTTP, etc.)
- Supports TDD workflow well

**Alternatives Considered**:
- **unittest**: Built-in but more verbose, less powerful fixtures
- **hypothesis**: Good for property-based testing, can be added as supplement

## Integration Patterns

### GitHub API Integration

**Approach**: REST API via httpx with authentication

**Key Endpoints**:
- `GET /users/{username}` - Basic profile info
- `GET /users/{username}/repos` - Repository list with languages
- `GET /users/{username}/events` - Recent activity
- `GET /repos/{owner}/{repo}` - Repository details (stars, etc.)

**Rate Limiting**:
- Authenticated: 5000 requests/hour
- Handle 403 responses gracefully
- Use conditional requests with ETag/If-None-Match for caching

### Up For Grabs Integration

**Source**: https://up-for-grabs.net

**Approach**: YAML files via GitHub API (updated 2024-2025)

**Data Structure**:
- Individual YAML files in `_data/projects/` directory
- Each project has name, site (GitHub URL), tags, upforgrabs label
- Issue counts and last-updated timestamps

**Performance Optimization**:
- Use async httpx for parallel YAML fetches
- Limit to 50 projects to avoid rate limits
- Cache results with 24-hour expiration

### Good First Issues Integration

**Source**: https://goodfirstissues.com

**Approach**: JSON API (discovered 2026-03-07)

**API**: `https://raw.githubusercontent.com/iedr/goodfirstissues/master/backend/data.json`

**Data Structure**:
- Array of issues with:
  - `Issue.issue_url` - GitHub issue URL
  - `Issue.issue_title` - Issue title
  - `Issue.issue_createdAt` - Creation timestamp
  - `Issue.issue_repo.repo_name` - Repository name
  - `Issue.issue_repo.repo_stars` - Star count
  - `Issue.issue_repo.repo_langs.Nodes[].repo_prog_language` - Languages
  - `Issue.issue_labels.Nodes[].label_name` - Labels

**Performance Notes**:
- JSON file is ~1.1MB
- Use 60-second timeout
- Sort alphabetically by repository name for deterministic output (no randomization)

### ~~Good First Issue Integration~~ (REMOVED)

**Source**: https://goodfirstissue.dev

**Status**: NOT WORKING - Client-side Nuxt.js rendering

**Issue**: The site uses Nuxt.js with client-side JavaScript rendering. The HTML response contains no actual issue data - content is loaded dynamically via JavaScript. BeautifulSoup cannot extract data from client-rendered content.

**Alternatives Considered**:
- **Playwright/Selenium**: Would work but adds browser dependency, slow, overkill
- **API reverse-engineering**: No public API available

**Decision**: Remove this source. Use goodfirstissues.com instead which provides a working JSON API.

### Claude Code Integration

**Approach**: Subprocess invocation

**Command Pattern**:
```bash
claude --print "prompt text here"
```

**Output Capture**:
- Capture stdout for Markdown report
- Capture stderr for error handling
- Handle timeout (60 second limit per SC-001)

### Git Operations (Publishing)

**Approach**: subprocess calls to git CLI

**Operations**:
- `git add`, `git commit`, `git push` for blog publishing
- Requires git installed and configured (document in prerequisites)

## Data Format Decisions

### Cache Structure

```
~/.oss-navi/
├── cache/
│   ├── github_profile.json      # User profile data
│   ├── upforgrabs_tasks.json    # Up For Grabs tasks
│   ├── goodfirstissues_tasks.json # Good First Issues tasks (renamed)
│   └── metadata.json            # Cache timestamps and version
├── state/
│   ├── config.json              # User configuration
│   ├── memory.json              # Long-term memory
│   └── reports/                 # Archived reports
└── temp/
    └── report_YYYYMMDD_HHMMSS.md  # Current report (before archive)
```

### Configuration Schema

```json
{
  "github_username": "string",
  "github_token": "string (stored separately with 0600)",
  "blog_repo_path": "string (optional)",
  "filters": {
    "min_stars": 50,
    "max_age_days": 90
  }
}
```

### Memory Schema

```json
{
  "version": 3,
  "created_at": "2026-03-07T10:00:00Z",
  "updated_at": "2026-03-08T14:30:00Z",
  "skill_history": [
    {
      "date": "2026-03-07",
      "languages": {"python": 0.7, "typescript": 0.3},
      "focus_areas": []
    }
  ],
  "past_recommendations": [
    {
      "date": "2026-03-07",
      "project": "owner/repo",
      "issue_url": "https://github.com/..."
    }
  ],
  "learning_goals": ["Python async programming", "Rust basics"],
  "great_projects_discovered": [
    {
      "name": "python/cpython",
      "shown_at": "2026-03-07T10:00:00Z",
      "reason": "Excellent for learning Python internals"
    }
  ],
  "field_exploration_history": [],
  "github_profile": {
    "username": "developer",
    "primary_languages": {"Python": 0.65, "TypeScript": 0.35},
    "total_repos": 42,
    "last_fetched": "2026-03-08T10:00:00Z"
  },
  "last_analysis_date": "2026-03-08T14:30:00Z",
  "analysis_count": 5
}
```

## Performance Considerations

### API Call Optimization

- Batch GitHub API calls where possible
- Use field filtering (`?fields=...`) to reduce response size
- Cache aggressively with 24-hour expiration
- Implement conditional requests for GitHub API
- **Use async httpx for parallel YAML fetches** (new)

### Search Algorithm Optimization

- Pre-index tasks by language for fast filtering
- Use sets for O(1) tag lookups
- Limit result sets early in pipeline
- Random sampling with `random.sample()` is O(n) - acceptable for our scale

### Scraping Efficiency

- Single fetch per source per sync
- Parse in-memory, no intermediate files
- Handle large responses with streaming if needed
- **Parallel fetch for Up For Grabs YAML files** (new)

### Claude Code Timeout

- 60-second timeout per SC-001
- Consider prompt length optimization
- Handle timeout gracefully with partial results

## Security Considerations

### Token Storage

- Store in `~/.oss-navi/.token` with 0600 permissions
- Never log or display token in output
- Validate token scope on first use

### Input Validation

- Validate GitHub username format (alphanumeric, hyphens)
- Sanitize learning focus input
- Validate file paths for blog repo

### External Data

- Validate all scraped data before storage
- Sanitize HTML entities from scraped content
- Handle malformed JSON gracefully

## Error Handling Strategy

| Error Type | Strategy |
|------------|----------|
| GitHub API rate limit | Use cached data, display warning |
| GitHub API auth failure | Clear cached token, prompt reconfig |
| Network timeout | Retry with exponential backoff (3 attempts) |
| Claude Code not found | Clear error message with install link |
| Good First Issues unavailable | Fall back to Up For Grabs only |
| Git push failure | Archive locally, warn user |

## Open Questions Resolved

All technical questions resolved through research. No NEEDS CLARIFICATION items remain.

## Changelog

- **2026-03-08**: Added research for linked PR detection and memory module fixes
- **2026-03-07**: Added enhanced analysis features research (issue status, recommendations, great projects)
- **2026-03-07**: Added performance optimization research
- **2026-03-07**: Removed goodfirstissue.dev (client-side rendering issue)
- **2026-03-07**: Renamed cache file to `goodfirstissues_tasks.json`

---

## Enhanced Analysis Features (Added 2026-03-07)

### Issue Status Checking

**Approach**: GitHub API to check issue status

**Key Endpoints**:
- `GET /repos/{owner}/{repo}/issues/{issue_number}` - Issue details including assignee
- `GET /repos/{owner}/{repo}/pulls` - Check for linked PRs

**Status Indicators**:
- `assignee` field: If present, issue is assigned
- `state` field: "open" or "closed"
- Labels: Check for "in progress", "assigned", "wip" etc.
- Linked PRs: Search for PRs mentioning the issue

**Rate Limit Consideration**:
- Batch check multiple issues
- Cache status for 1 hour
- Only check top candidates (after filtering)

### Recommendation Engine Design

**Scoring Factors** (weighted):

| Factor | Weight | Description |
|--------|--------|-------------|
| Language Match | 30% | User's top languages vs project language |
| Hotness Score | 20% | Stars / age (from existing calculation) |
| Issue Availability | 15% | Unassigned, no linked PRs |
| Learning Alignment | 15% | Matches user's stated learning goals |
| Skill Level Fit | 10% | Beginner/intermediate/advanced tag matching |
| Topic Relevance | 10% | Project topics match user interests |

**Rating Output**: 1-10 scale with breakdown

### Interactive Learning Interest Input

**Approach**: Prompt during analysis command

**Questions**:
1. "What are you currently learning or want to improve?" (free text)
2. "Any specific fields you'd like to explore?" (suggestions + free text)

**Integration**:
- Store in analysis session
- Include in Claude Code prompt
- Update LongTermMemory.learning_goals

### Great Open Source Projects Analysis

**Selection Criteria**:
- High code quality (stars > 1000, active maintenance)
- Well-documented codebase
- Relevant to user's skills
- Not necessarily beginner-friendly (advanced patterns)

**Analysis Content**:
- Project architecture overview
- Key patterns used
- Code organization
- Entry points for contribution

**Sources**:
- GitHub Trending (filtered by language)
- User's starred repos
- Projects with high "good first issue" ratio but also complex areas

### Automatic Report Archiving

**Approach**: Archive immediately after generation

**Implementation**:
1. Generate report to temp location
2. Copy to `state/reports/` with timestamp
3. Update `memory.json` with recommendations
4. No manual publish required

**Archive Naming**: `report_YYYYMMDD_HHMMSS.md`

### Claude Code Prompt Enhancement

**New Prompt Structure**:

```
## User Profile
[languages, activity, top repos]

## Learning Interests
[interactive input + historical goals]

## Available Tasks
[filtered, status-checked tasks with ratings]

## Great Projects for Learning
[advanced projects matching skills]

## Output Requirements
1. Skill assessment with learning advice
2. Field exploration recommendations
3. 5-10 issue recommendations with:
   - Rating (1-10)
   - Reason why it fits
   - Brief code analysis of project
4. 2-3 great open source projects with code analysis
5. Long-term memory updates
```

---

## Linked PR Detection (Added 2026-03-08)

### Problem

Issues may have linked pull requests that indicate work is already in progress. Current implementation only checks if the issue itself IS a PR, not if there's a separate PR linked to it.

### GitHub API Options

#### Option 1: Issue Timeline API (RECOMMENDED)

**Endpoint**: `GET /repos/{owner}/{repo}/issues/{issue_number}/timeline`

**Event Types to Check**:
- `cross-referenced` - When someone references this issue in a PR
- `connected` - When a PR is explicitly connected to close this issue

**Example Response**:
```json
[
  {
    "event": "cross-referenced",
    "actor": {...},
    "source": {
      "issue": {
        "number": 123,
        "pull_request": {
          "url": "https://api.github.com/repos/owner/repo/pulls/123"
        }
      }
    }
  }
]
```

**Pros**:
- Simple REST API
- Already authenticated
- No new dependencies

**Cons**:
- Requires extra API call per issue
- Rate limit concerns for bulk checks

**Rate Limit Strategy**:
- Only check timeline for top 10-15 candidates (after initial filtering)
- Cache results for 1 hour
- Use conditional requests with ETag

#### Option 2: GraphQL API

**Query**:
```graphql
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      timelineItems(itemTypes: [CROSS_REFERENCED_EVENT, CONNECTED_EVENT]) {
        nodes {
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                number
                state
                url
              }
            }
          }
        }
      }
    }
  }
}
```

**Pros**:
- More efficient for bulk queries
- Can get issue status and linked PRs in one call

**Cons**:
- Requires GraphQL client setup
- More complex implementation

#### Option 3: Search API

**Endpoint**: `GET /search/issues?q=repo:owner/repo type:pr "fixes #123" OR "closes #123"`

**Pros**:
- Can search multiple patterns
- Good for bulk discovery

**Cons**:
- Search API has separate rate limit (30 requests/min)
- Less reliable (depends on PR description format)

### Decision

Use **Issue Timeline API** for now:
1. Only check for top candidates (after initial scoring)
2. Implement caching to minimize API calls
3. Handle rate limits gracefully

### Implementation

```python
def check_linked_prs(
    self, owner: str, repo: str, issue_number: int
) -> tuple[bool, str | None]:
    """Check if an issue has any linked open PRs.

    Returns:
        Tuple of (has_open_pr, pr_url)
    """
    response = client.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/timeline",
        headers=self._get_headers(),
        params={"per_page": 100},
    )

    for event in response.json():
        if event.get("event") == "cross-referenced":
            source = event.get("source", {})
            issue = source.get("issue", {})
            pr = issue.get("pull_request", {})

            if pr:
                # Check if PR is open
                if issue.get("state") == "open":
                    return True, issue.get("html_url")

    return False, None
```

---

## Memory Module Fix (Added 2026-03-08)

### Problem Analysis

1. **Memory Not Created**: If `memory.json` doesn't exist, it's not created with defaults
2. **Memory Not Updated**: Update only happens with `--learn` flag
3. **Memory Not Fully Used**: Only `past_recommendations` shown in prompt

### Current Flow

```
cli.py:137 → memory = read_json(MEMORY_FILE)  # May be None
cli.py:194 → run_analysis(memory=memory)       # Passes None if missing
cli.py:199-203 → if learn: update_memory()     # Only updates with --learn
```

### Fix Strategy

1. **Always Initialize Memory**
   - In `update_memory_from_report`, create new memory if missing
   - Ensure `MEMORY_FILE` exists with defaults after first run

2. **Always Update Memory**
   - Remove `if learn:` condition
   - Update memory after every analysis
   - Track analysis count and last analysis date

3. **Enhance Memory Content**
   - Store GitHub profile summary
   - Track all learning goals (from prompts and --learn)
   - Record great projects discovered

4. **Enhance Prompt Integration**
   - Show skill history trends
   - Show previously discovered great projects
   - Show field exploration suggestions from history

### Memory Schema Enhancement

```python
class GitHubProfileSummary(BaseModel):
    """Cached summary of user's GitHub profile."""
    username: str
    primary_languages: dict[str, float]
    total_repos: int
    last_fetched: datetime


class LongTermMemory(BaseModel):
    # ... existing fields ...

    # NEW fields
    github_profile: Optional[GitHubProfileSummary] = None
    last_analysis_date: Optional[datetime] = None
    analysis_count: int = 0
```

### Memory Update Flow (Fixed)

```python
def run_analysis(...):
    # ... analysis ...

    # Always update memory
    memory = load_or_create_memory()
    memory = update_memory_from_report(memory, report, profile, learning_focus)
    save_memory(memory)

    return report
```
