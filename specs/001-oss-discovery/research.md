# Research: OSS-Navi CLI Tool

**Date**: 2026-03-07
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

**Alternatives Considered**:
- **requests**: Battle-tested but synchronous only, older API design
- **aiohttp**: Async-only, more complex for mixed sync/async needs

### Web Scraping: BeautifulSoup4 + lxml

**Decision**: BeautifulSoup4 with lxml parser

**Rationale**:
- Industry standard for Python web scraping
- Forgiving parser handles imperfect HTML
- lxml backend is fast and robust
- Easy to extract data from Good First Issue website

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

**Source**: https://up-for-grabs.net/data.json

**Approach**: Direct JSON fetch (no scraping needed)

**Data Structure**:
- Array of projects with labels for "up-for-grabs"
- Each project has name, url, description, tags
- Link to GitHub issues with specific labels

### Good First Issue Integration

**Source**: https://goodfirstissue.dev/

**Approach**: Web scraping (static site generation)

**Scraping Strategy**:
- Fetch HTML via httpx
- Parse with BeautifulSoup4
- Extract issue data from page content
- Handle pagination if present

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
│   ├── goodfirstissue_tasks.json # Good First Issue tasks
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
  "version": 1,
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
  ]
}
```

## Performance Considerations

### API Call Optimization

- Batch GitHub API calls where possible
- Use field filtering (`?fields=...`) to reduce response size
- Cache aggressively with 24-hour expiration
- Implement conditional requests for GitHub API

### Scraping Efficiency

- Single fetch per source per sync
- Parse in-memory, no intermediate files
- Handle large responses with streaming if needed

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
| Good First Issue unavailable | Fall back to Up For Grabs only |
| Git push failure | Archive locally, warn user |

## Open Questions Resolved

All technical questions resolved through research. No NEEDS CLARIFICATION items remain.
