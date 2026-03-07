# Implementation Plan: OSS-Navi Performance & Documentation Improvements

**Branch**: `001-oss-discovery` | **Date**: 2026-03-07 | **Spec**: [spec.md](./spec.md)
**Input**: User feedback on slow search, non-working goodfirstissue.dev, and outdated README

## Summary

Fix performance issues in task searching, remove non-functional goodfirstissue.dev source, and update all documentation to be consistent and accurate for users.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML
**Storage**: JSON files in `~/.oss-navi/` (cache/, state/, temp/)
**Testing**: pytest + pytest-cov (80% minimum coverage)
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: CLI tool
**Performance Goals**: Task fetch < 30s total, search < 1s for 1000 tasks
**Constraints**: HTTP requests should be parallelized, minimize external API calls
**Scale/Scope**: ~100-500 tasks from 2 working sources

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Existing tests at 80.59% coverage |
| II. Clean Architecture | ✅ PASS | Well-structured services and models |
| III. Security-First | ✅ PASS | Token storage, URL validation in place |
| IV. Code Quality & Simplicity | ✅ PASS | Code is clean, needs performance optimization |
| V. Documentation Standards | ✅ FIXED | README and specs updated |
| VI. Observability & Debuggability | ✅ PASS | Good error handling |
| VII. Versioning & Breaking Changes | ✅ PASS | Removing non-working source is a fix, not breaking |

## Project Structure

### Documentation (this feature)

```text
specs/001-oss-discovery/
├── plan.md              # This file
├── research.md          # Updated with performance findings
├── data-model.md        # Updated with correct sources
├── quickstart.md        # Updated usage examples
├── contracts/
│   └── cli.md           # CLI contracts
└── tasks.md             # Updated task list
```

### Source Code (repository root)

```text
src/oss_navi/
├── __init__.py
├── cli.py               # CLI commands
├── config.py            # Configuration management
├── models/
│   ├── __init__.py
│   ├── config.py        # Config and Filters models
│   ├── task.py          # Task and Repository models
│   ├── user_profile.py  # UserProfile model
│   ├── report.py        # AnalysisReport model
│   └── memory.py        # Long-term memory models
├── services/
│   ├── __init__.py
│   ├── scraper.py       # Task fetching and search
│   ├── analyzer.py      # Claude Code integration
│   ├── github.py        # GitHub API client
│   └── publisher.py     # Report publishing
└── utils/
    ├── __init__.py
    ├── cache.py         # Cache utilities
    └── paths.py         # Path constants

tests/
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── test_models/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_task.py
│   │   ├── test_user_profile.py
│   │   ├── test_report.py
│   │   └── test_memory.py
│   └── test_services/
│       ├── __init__.py
│       ├── test_analyzer.py
│       └── test_scraper.py
└── integration/
    ├── __init__.py
    ├── test_github.py
    └── test_scraper.py
```

**Structure Decision**: Single project structure with services for external integrations.

## Key Files Modified

| File Path | Changes |
|-----------|---------|
| `src/oss_navi/services/scraper.py` | Removed `fetch_goodfirstissue_tasks()`, added proxy support, renamed cache file |
| `src/oss_navi/services/github.py` | Added proxy support |
| `src/oss_navi/models/config.py` | Added http_proxy, https_proxy, no_proxy fields |
| `src/oss_navi/models/task.py` | Updated source validation |
| `src/oss_navi/utils/paths.py` | Renamed `GOODFIRSTISSUE_TASKS_CACHE` to `GOODFIRSTISSUES_TASKS_CACHE` |
| `src/oss_navi/cli.py` | Added proxy CLI options, fixed cache file references |
| `src/oss_navi/config.py` | Added `get_proxy_settings()` function |
| `README.md` | Complete rewrite with detailed instructions |
| `pyproject.toml` | Updated URLs, removed unused dependencies |

## Issues Identified and Resolved

### 1. Slow Search Performance

**Root Causes**:
- `fetch_upforgrabs_tasks()`: Sequential HTTP requests (1 list + up to 50 YAML fetches)
- `fetch_goodfirstissues_tasks()`: 1.1MB JSON file with 60s timeout
- `select_diverse_tasks()`: Inefficient iteration for diversity selection

**Solutions**:
- Use `httpx` async client for parallel requests (deferred to Phase 1)
- Cache aggressively with proper expiration
- Optimize search algorithm with pre-indexing

### 2. Non-Working goodfirstissue.dev

**Issue**: The site (goodfirstissue.dev) is a Nuxt.js SPA with client-side rendering. The HTML scraper returns empty results because content is loaded via JavaScript.

**Solution**: ✅ DONE - Removed `fetch_goodfirstissue_tasks()` function and all references. Now using only:
- Up For Grabs (YAML-based, working)
- Good First Issues (JSON API, working)

### 3. Outdated Documentation

**Issues**:
- README mentioned "Good First Issue (goodfirstissue.dev)" which doesn't work
- Task sources list was incorrect
- Cache file names didn't match actual implementation
- No `uv run` prefix in command examples

**Solution**: ✅ DONE - Updated all documentation files to reflect actual working sources and correct usage.

## Complexity Tracking

No constitution violations requiring justification.
