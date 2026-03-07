# Implementation Plan: OSS-Navi CLI Tool

**Branch**: `001-oss-discovery` | **Date**: 2026-03-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-oss-discovery/spec.md`

## Summary

OSS-Navi is a CLI tool that helps programmers discover and contribute to open source projects. It fetches the user's GitHub profile, scrapes beginner-friendly issues from multiple sources, and uses Claude Code to generate personalized project recommendations with skill assessments and learning guidance.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: click (CLI), httpx (HTTP client), beautifulsoup4 (web scraping), pydantic (data validation)
**Storage**: JSON files in `~/.oss-navi/` (cache/, state/, temp/)
**Testing**: pytest with pytest-cov for coverage
**Target Platform**: Linux, macOS, Windows (Python cross-platform)
**Project Type**: CLI tool
**Performance Goals**: Analysis command completes within 60 seconds
**Constraints**: GitHub API rate limits (~5000 req/hour authenticated), offline-capable with cached data
**Scale/Scope**: Single-user CLI tool, handles ~1000 cached tasks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ Pass | pytest + pytest-cov, 80% coverage target, test tasks in each phase (TDD compliant) |
| II. Clean Architecture | ✅ Pass | Modular CLI with separate services for GitHub, scraping, analysis |
| III. Security-First | ✅ Pass | Token stored with 0600 permissions, input validation on all external data |
| IV. Code Quality & Simplicity | ✅ Pass | Single-project CLI, clear separation of concerns |
| V. Documentation Standards | ✅ Pass | CLI help text, README with setup instructions |
| VI. Observability & Debuggability | ✅ Pass | Structured logging, error context, cache files human-readable (JSON) |
| VII. Versioning & Breaking Changes | ✅ Pass | Semantic versioning from v0.1.0 |

**Gate Status**: PASSED - No violations

## Project Structure

### Documentation (this feature)

```text
specs/001-oss-discovery/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── oss_navi/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (click commands)
│   ├── config.py           # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_profile.py
│   │   ├── task.py
│   │   ├── report.py
│   │   └── memory.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github.py       # GitHub API client
│   │   ├── scraper.py      # Up For Grabs + Good First Issue scraping
│   │   ├── analyzer.py     # Claude Code integration
│   │   └── publisher.py    # Blog publishing (git operations)
│   └── utils/
│       ├── __init__.py
│       ├── cache.py        # Cache management with expiration
│       └── paths.py        # Path constants (~/.oss-navi/)
tests/
├── unit/
│   ├── test_models/
│   ├── test_services/
│   └── test_utils/
├── integration/
│   ├── test_github.py
│   ├── test_scraper.py
│   └── test_cli.py
└── conftest.py
pyproject.toml              # Project configuration (setuptools/poetry)
README.md
```

**Structure Decision**: Single-project CLI using standard Python package layout. Models contain Pydantic data classes, services handle external integrations and business logic, utils provide shared utilities.

## Complexity Tracking

> No violations detected - all constitution gates passed.
