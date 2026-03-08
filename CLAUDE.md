# oss-navi Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-08

## Active Technologies
- Python 3.11+ + Click (CLI), httpx (HTTP client), httpx[socks] (SOCKS proxy), Pydantic v2 (data models), PyYAML
- scikit-surprise (collaborative filtering), LightFM (hybrid recommendations), numpy (array operations)
- fake-useragent (user agent rotation for scraping)
- JSON files in `~/.oss-navi/` (cache/, state/, sessions/)

## Project Structure

```text
src/oss_navi/
├── cli.py                    # CLI entry point
├── config.py                 # Configuration
├── models/                   # Pydantic data models
│   ├── preferences.py        # UserPreferences, BlockingRule
│   ├── recommendation.py    # Recommendation, RecommendationMode
│   ├── session.py            # RecommendationSession, ReportSection
│   ├── learning.py           # LearningResource, Course, PracticeProblem
│   └── analysis.py           # CodeAnalysis, KeyFile
├── services/
│   ├── github.py             # GitHub API
│   ├── scraper.py            # Task scraping
│   ├── analyzer.py           # Claude Code analysis
│   ├── recommender.py        # Recommendation orchestration
│   ├── session.py            # Session management
│   ├── learning.py           # Learning resources
│   └── algorithms/           # Recommendation algorithms
│       ├── base.py           # BaseRecommender
│       ├── fast.py           # Fast mode (content-based)
│       ├── normal.py         # Normal mode (Surprise)
│       ├── thinking.py       # Thinking mode (LightFM + Apriori)
│       └── apriori.py        # Pattern mining
└── utils/
    ├── paths.py              # Path utilities
    ├── cache.py              # Cache management
    ├── datetime_utils.py     # Datetime utilities
    └── scraping.py           # Scraping utilities

tests/
├── unit/
│   ├── test_models/
│   └── test_services/
└── integration/
```

## Commands

```bash
# Run tests
pytest --cov=oss_navi --cov-report=term-missing

# Lint
ruff check src/

# Install with all extras
uv sync --all-extras
```

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 002-intelligent-recommendations: Intelligent recommendations with 3 modes (fast, normal, thinking)
- 002-intelligent-recommendations: Learning path integration (csdiy.wiki, LeetCode, Codeforces)
- 002-intelligent-recommendations: Multi-round interactive sessions with feedback tracking
- 002-intelligent-recommendations: User personalization with language profiles and blocking rules

<!-- MANUAL ADDITIONS START -->
remember to do git commit every time you make changes
<!-- MANUAL ADDITIONS END -->
