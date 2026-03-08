# Implementation Plan: Intelligent Recommendations & Learning Paths

**Branch**: `002-intelligent-recommendations` | **Date**: 2026-03-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-intelligent-recommendations/spec.md`

## Summary

Enhance OSS-Navi with intelligent recommendation algorithms (Apriori, FP-Growth, collaborative filtering), multi-round interactive sessions with full report control, automatic learning resource integration (csdiy.wiki, LeetCode, Codeforces), and comprehensive user personalization with blocking rules. The system will use a two-round language matching strategy and provide lightweight, fast CLI responses.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML (config)
**Storage**: JSON files in `~/.oss-navi/` (cache/, state/, sessions/)
**Testing**: pytest with pytest-cov (80% minimum coverage), pytest-httpx for API mocking
**Target Platform**: Linux, macOS, Windows (cross-platform CLI)
**Project Type**: CLI tool (extending existing oss-navi)
**Performance Goals**:
  - Initial recommendations: <90 seconds
  - Interactive round response: <5 seconds
  - Memory footprint: <100MB during analysis
  - Lightweight algorithm execution: Apriori/FP-Growth on cached data only
**Constraints**:
  - No external database dependencies (JSON-only storage)
  - Minimal memory overhead for algorithms
  - Offline-capable for cached data analysis
  - Single-threaded for simplicity (algorithms run on local data)
**Scale/Scope**:
  - Thousands of cached tasks
  - Hundreds of user sessions
  - Learning resource catalog (csdiy courses, LeetCode/Codeforces problems)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ Pass | TDD workflow planned; 80% coverage requirement |
| II. Clean Architecture | ✅ Pass | Services layer for algorithms; models for entities; CLI for interface |
| III. Security-First | ✅ Pass | Input validation for all external APIs; no secrets in code |
| IV. Code Quality & Simplicity | ✅ Pass | YAGNI applied - only implement specified algorithms |
| V. Documentation Standards | ✅ Pass | CLI help text; docstrings for public APIs |
| VI. Observability & Debuggability | ✅ Pass | Structured logging with context |
| VII. Versioning & Breaking Changes | ✅ Pass | Backward compatible additions to existing CLI |
| VIII. Intelligent Recommendation System | ✅ Pass | Core feature - algorithms specified in requirements |
| IX. User-Centric Personalization | ✅ Pass | Multi-language profiles; blocking rules; local storage |
| X. Learning Path Integration | ✅ Pass | csdiy.wiki, LeetCode, Codeforces integration |
| XI. Interactive User Experience | ✅ Pass | Multi-round sessions; report control; session persistence |

## Project Structure

### Documentation (this feature)

```text
specs/002-intelligent-recommendations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli.md           # CLI command contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/oss_navi/
├── __init__.py
├── cli.py               # Existing - extend with new commands
├── config.py            # Existing - extend with new settings
├── models/
│   ├── __init__.py
│   ├── config.py        # Existing
│   ├── user_profile.py  # Existing - extend
│   ├── task.py          # Existing
│   ├── report.py        # Existing - extend
│   ├── memory.py        # Existing
│   ├── preferences.py   # NEW - UserPreferences, BlockingRule
│   ├── session.py       # NEW - RecommendationSession, ReportSection
│   ├── learning.py      # NEW - LearningResource, Course, PracticeProblem
│   └── recommendation.py # NEW - Recommendation, RecommendationPattern
├── services/
│   ├── __init__.py
│   ├── github.py        # Existing
│   ├── scraper.py       # Existing
│   ├── recommender.py   # NEW - Main recommendation orchestration
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── apriori.py   # NEW - Apriori association rule mining
│   │   ├── fpgrowth.py  # NEW - FP-Growth pattern discovery
│   │   ├── collaborative.py # NEW - Collaborative filtering
│   │   └── content_based.py # NEW - Content-based filtering
│   ├── learning.py      # NEW - csdiy, LeetCode, Codeforces integration
│   └── session.py       # NEW - Multi-round session management
└── utils/
    ├── __init__.py
    ├── paths.py         # Existing
    └── cache.py         # Existing

tests/
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── test_models/
│   │   ├── test_preferences.py    # NEW
│   │   ├── test_session.py        # NEW
│   │   ├── test_learning.py       # NEW
│   │   └── test_recommendation.py # NEW
│   └── test_services/
│       ├── test_algorithms/        # NEW
│       │   ├── test_apriori.py
│       │   ├── test_fpgrowth.py
│       │   ├── test_collaborative.py
│       │   └── test_content_based.py
│       ├── test_recommender.py     # NEW
│       ├── test_learning.py        # NEW
│       └── test_session.py         # NEW
└── integration/
    ├── test_learning_apis.py       # NEW
    └── test_recommendation_flow.py # NEW
```

**Structure Decision**: Extend existing single-project structure. Add `services/algorithms/` subpackage for recommendation engines. Add new models for preferences, sessions, learning resources, and recommendations.

## Complexity Tracking

> No violations - design follows existing patterns and constitution principles.

| Decision | Rationale |
|----------|-----------|
| algorithms/ subpackage | Separates algorithm implementations from orchestration; enables independent testing |
| JSON-only storage | Maintains lightweight CLI; no database overhead; offline-capable |
| Single-threaded execution | Simplicity; local data size doesn't warrant parallelism; fast enough for CLI use |
| Cached data only for algorithms | Performance constraint; avoids network latency during analysis |

## Dependencies (New)

| Package | Version | Purpose |
|---------|---------|---------|
| (existing) | - | Click, httpx, Pydantic v2, PyYAML |
| (no new runtime deps) | - | Algorithms implemented in pure Python for lightness |

**Note**: Deliberately avoiding ML libraries (scikit-learn, numpy) to keep the CLI lightweight. Apriori and FP-Growth implementations will be simple, focused versions for the specific use case.
