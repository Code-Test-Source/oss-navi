# Implementation Plan: Enhanced Analysis & Recommendations

**Branch**: `001-oss-discovery` | **Date**: 2026-03-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-oss-discovery/spec.md` + Enhancement Request

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Enhance the OSS-Navi analysis feature with:
1. Issue status validation (check if assigned/under development)
2. More recommendations (5-10 instead of 1-2)
3. Detailed ratings and recommendation reasons
4. Brief code analysis of recommended projects
5. Interactive learning interest input during analysis
6. Advice on exploring adjacent fields
7. Great open source project analysis (beyond beginner-friendly issues)
8. Automatic report archiving

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML
**Storage**: JSON files in `~/.oss-navi/` (cache/, state/, temp/)
**Testing**: pytest + pytest-cov (80% coverage required)
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: CLI tool
**Performance Goals**: Analysis < 60s end-to-end, issue status checks < 5s per issue
**Constraints**: GitHub API rate limits, Claude Code subprocess timeout (60s)
**Scale/Scope**: Single user, ~1000 tasks cached, 5-10 recommendations per analysis

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | TDD workflow will be followed for new features |
| II. Clean Architecture | ✅ PASS | New services added to existing modular structure |
| III. Security-First | ✅ PASS | GitHub API calls authenticated, no new secrets |
| IV. Code Quality & Simplicity | ✅ PASS | Each new feature in focused modules |
| V. Documentation Standards | ✅ PASS | Update spec.md, contracts, README |
| VI. Observability & Debuggability | ✅ PASS | Add logging for issue status checks |
| VII. Versioning & Breaking Changes | ✅ PASS | Minor version bump (new features, backward compatible) |

**Gate Status**: ✅ PASSED - All constitution checks satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-oss-discovery/
├── plan.md              # This file
├── research.md          # Phase 0 output (updated for enhancements)
├── data-model.md        # Phase 1 output (updated for new entities)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli.md           # Updated CLI contracts
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/oss_navi/
├── cli.py               # Updated: interactive prompts, archive command
├── config.py            # Configuration management
├── models/
│   ├── config.py
│   ├── task.py          # Updated: IssueStatus, Recommendation
│   └── user_profile.py
├── services/
│   ├── github.py        # Updated: issue status checking
│   ├── scraper.py       # Existing task fetching
│   ├── analyzer.py      # NEW: recommendation engine
│   └── archiver.py      # NEW: report archiving
└── utils/
    ├── cache.py
    ├── paths.py
    └── memory.py        # Updated: great projects tracking

tests/
├── unit/
│   └── test_services/
│       ├── test_analyzer.py     # NEW
│       ├── test_archiver.py     # NEW
│       └── test_github.py       # Updated
└── integration/
    └── test_scraper.py
```

**Structure Decision**: Single project structure with new service modules added to `services/`. The `analyzer.py` will contain the recommendation engine, and `archiver.py` will handle report archiving.

## Complexity Tracking

> No violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | - | - |

## New Feature Requirements

### FR-048: Issue Status Validation
The system MUST check if recommended issues are:
- Already assigned to someone
- Closed or have linked PRs
- Marked as "in progress" via labels

### FR-049: Enhanced Recommendations
The system MUST provide 5-10 recommendations (up from 1-2) with:
- Detailed rating (1-10 scale)
- Recommendation reason (why this fits user)
- Brief code analysis of the project structure

### FR-050: Interactive Learning Interest
The system MUST prompt user for current learning interests during analysis:
- Ask for primary learning focus
- Ask for fields they want to explore
- Incorporate into skill analysis and recommendations

### FR-051: Great Open Source Project Analysis
The system MUST recommend great open source projects (not beginner-friendly):
- Projects with excellent code quality
- Relevant to user's skills and learning goals
- Include brief code analysis (architecture, patterns)

### FR-052: Automatic Report Archiving
The system MUST automatically archive reports after generation:
- Save to `~/.oss-navi/state/reports/` with timestamp
- Update memory with recommendations made
