# Implementation Plan: Optimize Recommend Algorithm & Fix Memory Module

**Branch**: `001-oss-discovery` | **Date**: 2026-03-08 | **Spec**: [spec.md](./spec.md)
**Input**: User request to optimize recommend algorithm, fix issue status detection, and fix memory module

## Summary

This plan addresses three critical issues:
1. **Recommend Algorithm Optimization**: Improve scoring accuracy and issue filtering
2. **Issue Status Detection Enhancement**: Detect issues that have linked PRs (work-in-progress)
3. **Memory Module Fix**: Ensure long-term memory is properly stored and used in analysis

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click (CLI), httpx (HTTP client), Pydantic v2 (data models), PyYAML
**Storage**: JSON files in `~/.oss-navi/` (cache/, state/, temp/)
**Testing**: pytest + pytest-cov
**Target Platform**: CLI tool (Linux, macOS, Windows)
**Project Type**: CLI application
**Performance Goals**: <60 seconds for full analysis, minimal GitHub API calls
**Constraints**: GitHub API rate limits (5000/hour authenticated), 24-hour cache validity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Test-First Development (TDD) | ✅ PASS | Will write tests before implementation |
| Clean Architecture | ✅ PASS | No architectural changes needed |
| Security-First | ✅ PASS | No new security concerns |
| Code Quality & Simplicity | ✅ PASS | Targeted fixes only |
| Documentation Standards | ✅ PASS | Will update relevant docs |
| Observability & Debuggability | ✅ PASS | No changes needed |
| Versioning & Breaking Changes | ✅ PASS | Bug fixes only, no API changes |

**Gate Status**: ✅ PASSED - All principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-oss-discovery/
├── plan.md              # This file
├── research.md          # Existing research (updated)
├── data-model.md        # Existing data model (updated)
├── quickstart.md        # Existing quickstart
├── contracts/           # CLI contracts
└── tasks.md             # Tasks from /speckit.tasks
```

### Source Code (repository root)

```text
src/oss_navi/
├── models/
│   ├── task.py          # IssueStatus model - ENHANCE
│   └── memory.py        # LongTermMemory model - ENHANCE
├── services/
│   ├── analyzer.py      # Recommendation logic - ENHANCE
│   └── github.py        # GitHub API client - ENHANCE
└── cli.py               # CLI entry point - MINOR FIX

tests/
├── unit/
│   ├── test_services/
│   │   ├── test_analyzer.py  # Tests for recommendation
│   │   └── test_issue_status.py  # Tests for status check
│   └── test_models/
│       └── test_memory.py    # Tests for memory module
└── integration/
    └── test_enhanced_analysis.py  # End-to-end tests
```

**Structure Decision**: Using existing single-project structure. Changes are targeted enhancements to existing modules.

## Problem Analysis

### Issue 1: Issue Status Detection Incomplete

**Current Behavior** (github.py:223-303):
- Checks if issue has `assignee`
- Checks if issue `state` is "closed"
- Checks if issue IS a PR (has `pull_request` key in response)

**Missing**:
- Does NOT check if there's a separate PR that mentions/closes this issue
- Issues with active PRs should be marked as "work in progress"

**Solution**:
- Use GitHub's GraphQL API or search API to find PRs linked to an issue
- Alternatively, use the issue's `timeline` endpoint to check for connected events
- Add `has_open_pr` field to `IssueStatus` model

### Issue 2: Memory Module Not Working

**Current Behavior**:
1. Memory is loaded in CLI (cli.py:137)
2. Memory is passed to `run_analysis` (cli.py:194)
3. Memory update only happens when `--learn` flag is provided (cli.py:199-203)
4. Memory is only partially used in `build_prompt` (analyzer.py:136-143)

**Problems**:
- Memory not updated when `--learn` is NOT provided
- Memory not created if doesn't exist
- Memory not fully utilized (skill_history, great_projects_discovered, field_exploration_history not shown)
- Memory not loaded with proper defaults

**Solution**:
- Always update memory after analysis
- Ensure memory file is created with defaults if missing
- Enhance prompt to include all memory sections
- Store GitHub profile summary in memory after each sync

### Issue 3: Recommend Algorithm Optimization

**Current Weights** (analyzer.py:473-557):
| Factor | Weight |
|--------|--------|
| Language Match | 30% |
| Hotness Score | 20% |
| Issue Availability | 15% |
| Learning Alignment | 15% |
| Skill Level Fit | 10% |
| Topic Relevance | 10% |

**Issues**:
- Availability score is binary (0 or 10) - wastes 15% weight before status check
- No penalty for issues that have been recommended before
- No consideration of user's past success patterns
- Topic relevance calculation is weak

**Solution**:
- Defer availability scoring until after status check
- Add "past recommendation penalty" for variety
- Improve topic relevance with semantic matching
- Add proper normalization for hotness score

## Phase 0: Research Summary

### Issue Status Detection Research

**GitHub API Options for Finding Linked PRs**:

1. **Issue Timeline API** (Recommended)
   - `GET /repos/{owner}/{repo}/issues/{issue_number}/timeline`
   - Look for `cross-referenced` events where `issue.pull_request` exists
   - Pros: Simple REST API, no new dependencies
   - Cons: Requires extra API call per issue

2. **GraphQL API**
   - Single query to get issue + connected PRs
   - Pros: More efficient for bulk checks
   - Cons: More complex, requires GraphQL client

3. **Search API**
   - `GET /search/issues?q=repo:owner/repo is:pr {issue_number}`
   - Pros: Can search multiple at once
   - Cons: Rate limits on search API (30/min)

**Decision**: Use Issue Timeline API for now, with rate limit protection.

### Memory Storage Research

**Current Schema** (memory.py):
```python
class LongTermMemory(BaseModel):
    version: int = 2
    created_at: datetime
    updated_at: datetime
    skill_history: list[SkillSnapshot]
    past_recommendations: list[PastRecommendation]
    learning_goals: list[str]
    great_projects_discovered: list[GreatProjectSummary]
    field_exploration_history: list[FieldExploration]
```

**Enhancements Needed**:
1. Add `github_profile_summary` field for quick reference
2. Add `last_analysis_date` field
3. Add `preferred_languages` cached from last profile

## Phase 1: Design Changes

### Data Model Changes

#### IssueStatus Enhancement (models/task.py)

```python
class IssueStatus(BaseModel):
    """Real-time status of an issue."""
    issue_url: str
    is_assigned: bool
    assignee: Optional[str] = None
    is_closed: bool
    has_linked_pr: bool  # Issue IS a PR (existing)
    has_open_pr: bool = False  # NEW: Has separate open PR linked
    linked_pr_url: Optional[str] = None  # NEW: URL of linked PR
    in_progress_labels: list[str] = Field(default_factory=list)
    checked_at: datetime

    @property
    def is_available(self) -> bool:
        """Check if issue is available for contribution."""
        return (
            not self.is_assigned
            and not self.is_closed
            and not self.has_linked_pr
            and not self.has_open_pr  # NEW condition
        )
```

#### LongTermMemory Enhancement (models/memory.py)

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

### Contract Changes

#### CLI `analysis` command output enhancements:
- Show memory status ("✓ Long-term memory updated" always, not just with --learn)
- Show if issue has linked PR in recommendation display
- Show "Previously recommended" warning for repeat suggestions

### Implementation Tasks

1. **Fix Memory Module** (Priority 1)
   - Create memory file with defaults if missing
   - Always update memory after analysis
   - Store GitHub profile summary in memory
   - Enhance prompt to include full memory context

2. **Enhance Issue Status Detection** (Priority 2)
   - Add `check_linked_prs()` function to GitHub client
   - Update `IssueStatus` model
   - Integrate into recommendation pipeline

3. **Optimize Recommendation Algorithm** (Priority 3)
   - Adjust scoring weights
   - Add past recommendation penalty
   - Improve topic relevance scoring

## Complexity Tracking

> No complexity violations - targeted enhancements only.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Next Steps

After this plan is approved:
1. Run `/speckit.tasks` to generate detailed task list
2. Implement Phase 1 (Memory Fix) with TDD
3. Implement Phase 2 (Issue Status Enhancement) with TDD
4. Implement Phase 3 (Algorithm Optimization) with TDD
5. Run full test suite
6. Update documentation
