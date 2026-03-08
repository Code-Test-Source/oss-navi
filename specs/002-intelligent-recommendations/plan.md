# Implementation Plan: Intelligent Recommendations & Learning Paths

**Branch**: `002-intelligent-recommendations` | **Date**: 2026-03-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-intelligent-recommendations/spec.md`

## Summary

Enhance OSS-Navi with intelligent recommendation algorithms integrated into the existing `analysis` command. The system uses Surprise (scikit-surprise) and LightFM libraries with three recommendation modes (fast, normal, thinking) of varying algorithm complexity. Recommendation logic is separated into `services/recommender.py` for clean architecture. Features include multi-round interactive sessions with full report control, automatic learning resource integration (csdiy.wiki, LeetCode, Codeforces), and comprehensive user personalization with blocking rules.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- Click (CLI)
- httpx (HTTP client, with httpx[socks] for proxy support)
- Pydantic v2 (data models)
- PyYAML (config)
- **scikit-surprise** (collaborative filtering, SVD, KNN)
- **LightFM** (hybrid recommendations, implicit feedback)
- numpy (required by Surprise/LightFM)
- **fake-useragent** (user agent rotation for scraping)
**Storage**: JSON files in `~/.oss-navi/` (cache/, state/, sessions/)
**Testing**: pytest with pytest-cov (80% minimum coverage), pytest-httpx for API mocking
**Target Platform**: Linux, macOS, Windows (cross-platform CLI)
**Project Type**: CLI tool (extending existing oss-navi)
**Performance Goals**:
  - **Fast mode**: <30 seconds (simple content-based filtering)
  - **Normal mode**: <90 seconds (Surprise collaborative filtering)
  - **Thinking mode**: <180 seconds (LightFM hybrid + pattern mining)
**Constraints**:
  - No external database dependencies (JSON-only storage)
  - Mode-dependent memory usage (fast <50MB, normal <200MB, thinking <500MB)
  - Offline-capable for cached data analysis
**Scale/Scope**:
  - Thousands of cached tasks
  - Hundreds of user sessions
  - Learning resource catalog (csdiy courses, LeetCode/Codeforces problems)

**Data Source Strategy**:
  - Primary: Third-party datasets (avoid rate limits)
  - Secondary: API calls for verification only
  - LeetCode: https://github.com/neenza/leetcode-problems
  - Codeforces: Kaggle/HuggingFace datasets or minimal API
  - GitHub: GitHub Archive (https://www.gharchive.org/)
  - Rate limiting enforced: GitHub 1/s, LeetCode 1/2s, Codeforces 5/s

## Recommendation Modes

### Fast Mode
- **Algorithm**: Content-based filtering only
- **Dependencies**: Pure Python (no Surprise/LightFM)
- **Time**: <30 seconds
- **Memory**: <50MB
- **Use case**: Quick exploration, low-resource environments

### Normal Mode
- **Algorithm**: Surprise collaborative filtering (SVD, KNN)
- **Dependencies**: scikit-surprise, numpy
- **Time**: <90 seconds
- **Memory**: <200MB
- **Use case**: Balanced quality and speed

### Thinking Mode
- **Algorithm**: LightFM hybrid + Apriori pattern mining
- **Dependencies**: LightFM, numpy, scikit-surprise
- **Time**: <180 seconds
- **Memory**: <500MB
- **Use case**: Maximum recommendation quality

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ Pass | TDD workflow planned; 80% coverage requirement |
| II. Clean Architecture | ✅ Pass | Services layer for algorithms; models for entities; CLI for interface |
| III. Security-First | ✅ Pass | Input validation for all external APIs; no secrets in code |
| IV. Code Quality & Simplicity | ✅ Pass | YAGNI applied - mode-based algorithm selection |
| V. Documentation Standards | ✅ Pass | CLI help text; docstrings for public APIs |
| VI. Observability & Debuggability | ✅ Pass | Structured logging with context |
| VII. Versioning & Breaking Changes | ✅ Pass | Backward compatible additions to existing CLI |
| VIII. Intelligent Recommendation System | ✅ Pass | Surprise + LightFM provide advanced algorithms |
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
│   └── recommendation.py # NEW - Recommendation, RecommendationMode
├── services/
│   ├── __init__.py
│   ├── github.py        # Existing
│   ├── scraper.py       # Existing
│   ├── recommender.py   # NEW - Main recommendation orchestration
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── base.py      # NEW - Abstract base class for algorithms
│   │   ├── fast.py      # NEW - Fast mode (content-based only)
│   │   ├── normal.py    # NEW - Normal mode (Surprise)
│   │   ├── thinking.py  # NEW - Thinking mode (LightFM + Apriori)
│   │   ├── content_based.py # NEW - Content-based filtering
│   │   └── apriori.py   # NEW - Apriori pattern mining
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
│       │   ├── test_fast.py
│       │   ├── test_normal.py
│       │   ├── test_thinking.py
│       │   └── test_apriori.py
│       ├── test_recommender.py     # NEW
│       ├── test_learning.py        # NEW
│       └── test_session.py         # NEW
└── integration/
    ├── test_learning_apis.py       # NEW
    └── test_recommendation_flow.py # NEW
```

**Structure Decision**: Extend existing single-project structure. Add `services/algorithms/` subpackage with mode-specific implementations. Use factory pattern to select algorithm based on mode.

## Complexity Tracking

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|-------------------------------------|
| Surprise library | SVD/KNN algorithms provide quality collaborative filtering | Pure Python implementations less accurate |
| LightFM library | Hybrid recommendations combining content + collaborative | Single algorithm approach less effective |
| Three modes | Different use cases (quick vs quality) | Single mode doesn't serve all needs |
| numpy dependency | Required by Surprise/LightFM | Cannot avoid for ML algorithms |

## Dependencies (New)

| Package | Version | Purpose | Mode Required |
|---------|---------|---------|---------------|
| scikit-surprise | >=1.1.0 | Collaborative filtering (SVD, KNN) | Normal, Thinking |
| lightfm | >=1.17 | Hybrid recommendations | Thinking |
| numpy | >=1.24.0 | Array operations (required by above) | Normal, Thinking |
| fake-useragent | >=1.4.0 | User agent rotation for scraping | All modes |

**Optional dependencies**:
- Users who only need fast mode can skip Surprise/LightFM installation
- `httpx[socks]` already included for proxy support

## Scraping Best Practices

When scraping data, follow these principles:

1. **User Agent Rotation**: Use `fake_useragent` to rotate user agents
2. **Cache First**: Always check local cache before network request
3. **Public Metadata Only**: Never use cookies, CSRF tokens, or authentication
4. **Proxy Support**: Allow proxy configuration for IP rotation
5. **Rate Limiting**: Respect service rate limits (default 2s between requests)

```bash
# Proxy configuration via environment variables
export HTTPS_PROXY=http://localhost:8118
oss-navi sync --learning

# Or via CLI option
oss-navi sync --learning --proxy http://localhost:8118
```
