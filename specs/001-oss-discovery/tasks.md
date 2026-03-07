# Tasks: OSS-Navi Enhanced Analysis Features

**Input**: Design documents from `specs/001-oss-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED per constitution principle I (Test-First Development - NON-NEGOTIABLE). Each phase includes test tasks to be written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US#]**: User story this task belongs to (US1, US2, US3, US4)
- All file paths are relative to repository root

---

## Phase 1: Setup & Models (FOUNDATION)

**Goal**: Add new data models for enhanced analysis features

**Independent Test**: Run `uv run pytest tests/unit/test_models/` and verify all model tests pass

### Tests for Models

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T041 [P] Create `tests/unit/test_models/test_issue_status.py` with IssueStatus model tests
- [x] T042 [P] Create `tests/unit/test_models/test_recommendation.py` with Recommendation and RatingBreakdown model tests
- [x] T043 [P] Create `tests/unit/test_models/test_great_project.py` with GreatProject model tests
- [x] T044 [P] Create `tests/unit/test_models/test_learning_session.py` with LearningSession model tests
- [x] T045 Verify model tests fail (models not yet implemented)

### Implementation for Models

- [x] T046 [P] Add `IssueStatus` model to `src/oss_navi/models/task.py`
- [x] T047 [P] Add `Recommendation` and `RatingBreakdown` models to `src/oss_navi/models/task.py`
- [x] T048 [P] Add `GreatProject` model to `src/oss_navi/models/task.py`
- [x] T049 [P] Add `LearningSession` model to `src/oss_navi/models/task.py`
- [x] T050 Update `LongTermMemory` model with `great_projects_discovered` and `field_exploration_history` in `src/oss_navi/models/memory.py`
- [x] T051 Verify model tests pass

**Checkpoint**: All new models should be validated and tested

---

## Phase 2: Issue Status Service (US1)

**Goal**: Implement issue status checking to validate recommended issues are available

**Independent Test**: Run `uv run pytest tests/unit/test_services/test_github.py -k issue_status` and verify status checking works

### Tests for Issue Status

- [x] T052 [US1] Create `tests/unit/test_services/test_issue_status.py` with mocked GitHub API responses
- [x] T053 [US1] Verify issue status tests fail (function not implemented)

### Implementation for Issue Status

- [x] T054 [US1] Add `check_issue_status()` method to `GitHubClient` in `src/oss_navi/services/github.py`
- [x] T055 [US1] Add `check_multiple_issues()` batch method for efficiency in `src/oss_navi/services/github.py`
- [x] T056 [US1] Add rate limit handling for issue status checks in `src/oss_navi/services/github.py`
- [x] T057 [US1] Verify issue status tests pass

**Checkpoint**: Issue status checking should work for single and batch requests

---

## Phase 3: Recommendation Engine (US1)

**Goal**: Build the recommendation scoring engine with detailed ratings

**Independent Test**: Run `uv run pytest tests/unit/test_services/test_analyzer.py` and verify recommendation scoring works

### Tests for Recommendation Engine

- [x] T058 [US1] Create `tests/unit/test_services/test_analyzer.py` with recommendation scoring tests
- [x] T059 [US1] Add tests for `calculate_rating_breakdown()` scoring weights
- [x] T060 [US1] Add tests for `generate_recommendations()` returning 5-10 items
- [x] T061 [US1] Verify analyzer tests fail (module not implemented)

### Implementation for Recommendation Engine

- [x] T062 [US1] Create `src/oss_navi/services/analyzer.py` module
- [x] T063 [US1] Implement `calculate_rating_breakdown()` with weighted scoring in `src/oss_navi/services/analyzer.py`
- [x] T064 [US1] Implement `generate_recommendations()` that returns 5-10 scored recommendations in `src/oss_navi/services/analyzer.py`
- [x] T065 [US1] Implement `generate_recommendation_reason()` for personalized explanations in `src/oss_navi/services/analyzer.py`
- [x] T066 [US1] Verify analyzer tests pass

**Checkpoint**: Recommendation engine should produce scored recommendations with reasons

---

## Phase 4: Great Projects Discovery (US1)

**Goal**: Add discovery of great open source projects for learning (not beginner-friendly)

**Independent Test**: Run `uv run pytest tests/unit/test_services/test_analyzer.py -k great_project` and verify great project discovery works

### Tests for Great Projects

- [x] T067 [US1] Add tests for `find_great_projects()` matching user skills in `tests/unit/test_services/test_analyzer.py`
- [x] T068 [US1] Add tests for `analyze_project_architecture()` in `tests/unit/test_services/test_analyzer.py`
- [x] T069 [US1] Verify great project tests fail (functions not implemented)

### Implementation for Great Projects

- [x] T070 [US1] Implement `find_great_projects()` using GitHub search API in `src/oss_navi/services/analyzer.py`
- [x] T071 [US1] Implement `analyze_project_architecture()` for code analysis in `src/oss_navi/services/analyzer.py`
- [x] T072 [US1] Add great project caching to avoid repeated API calls in `src/oss_navi/utils/cache.py`
- [x] T073 [US1] Verify great project tests pass

**Checkpoint**: Great projects should be discovered and analyzed with architecture overview

---

## Phase 5: Interactive Learning Prompts (US1)

**Goal**: Add interactive prompts for learning interests and field exploration

**Independent Test**: Run `uv run oss-navi analysis` without `--no-interactive` and verify prompts appear

### Tests for Interactive Prompts

- [x] T074 [US1] Add tests for `prompt_learning_interests()` in `tests/unit/test_cli.py`
- [x] T075 [US1] Add tests for `suggest_adjacent_fields()` in `tests/unit/test_services/test_analyzer.py`
- [x] T076 [US1] Verify interactive prompt tests fail (functions not implemented)

### Implementation for Interactive Prompts

- [x] T077 [US1] Implement `prompt_learning_interests()` using Click prompts in `src/oss_navi/cli.py`
- [x] T078 [US1] Add `--explore` option for field exploration in `src/oss_navi/cli.py`
- [x] T079 [US1] Add `--recommendations` / `-n` option for count in `src/oss_navi/cli.py`
- [x] T080 [US1] Implement `suggest_adjacent_fields()` in `src/oss_navi/services/analyzer.py`
- [x] T081 [US1] Verify interactive prompt tests pass

**Checkpoint**: Analysis command should prompt for learning interests interactively

---

## Phase 6: Report Archiver (US1) - SKIPPED

**Note**: User requested to skip automatic archive feature as the `publish` command already handles archiving.

**Goal**: ~~Implement automatic report archiving after generation~~

### Skipped Tasks

- [~] T082-T090 - Skipped per user request (existing `publish` command handles archiving)

---

## Phase 7: Analysis Command Integration (US1)

**Goal**: Integrate all enhanced analysis features into the analysis command

**Independent Test**: Run `uv run oss-navi analysis` and verify full enhanced report is generated

### Tests for Integration

- [x] T091 [US1] Create `tests/integration/test_enhanced_analysis.py` with end-to-end tests
- [x] T092 [US1] Add tests for full report structure (5-10 recommendations, great projects, field exploration) in `tests/integration/test_enhanced_analysis.py`
- [x] T093 [US1] Verify integration tests fail (features not integrated)

### Implementation for Integration

- [x] T094 [US1] Update `analysis` command to use new `analyzer.py` service in `src/oss_navi/cli.py`
- [x] T095 [US1] Update Claude Code prompt template for enhanced report structure in `src/oss_navi/services/analyzer.py`
- [x] T096 [US1] Integrate issue status checking before recommendations in `src/oss_navi/cli.py`
- [x] T097 [US1] Add field exploration advice to report generation in `src/oss_navi/services/analyzer.py`
- [x] T098 [US1] Verify integration tests pass

**Checkpoint**: Full enhanced analysis should produce comprehensive report

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

### Tests & Coverage

- [x] T099 Run full test suite: `uv run pytest tests/ -q --tb=short --cov=oss_navi --cov-report=term-missing`
- [x] T100 Verify 80%+ test coverage maintained for new modules
- [x] T101 Run ruff linting: `uv run ruff check src/`

### Documentation Updates

- [x] T102 [P] Update `README.md` with enhanced analysis features
- [x] T103 [P] Update `README.md` with interactive prompts documentation
- [x] T104 [P] Update `specs/001-oss-discovery/quickstart.md` with new analysis workflow

### Manual Testing

- [ ] T105 Manual test: `uv run oss-navi analysis` produces 5-10 recommendations with ratings
- [ ] T106 Manual test: Interactive prompts work correctly
- [ ] T107 Manual test: Great projects section appears in report
- [ ] T108 Manual test: Report is auto-archived
- [ ] T109 Manual test: Issue status checked and unavailable issues flagged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Models)**: No dependencies - can start immediately
- **Phase 2 (Issue Status)**: Depends on Phase 1 models
- **Phase 3 (Recommendation Engine)**: Depends on Phase 1 models, Phase 2 for status integration
- **Phase 4 (Great Projects)**: Depends on Phase 1 models
- **Phase 5 (Interactive Prompts)**: No strict dependencies - can run parallel with Phase 2-4
- **Phase 6 (Archiver)**: Depends on Phase 1 models
- **Phase 7 (Integration)**: Depends on Phases 1-6
- **Phase 8 (Polish)**: Depends on all previous phases

### Parallel Opportunities

Phases 2, 3, 4, 5, 6 can partially run in parallel:
- Phase 2 (Issue Status) and Phase 4 (Great Projects) are independent
- Phase 5 (Interactive Prompts) and Phase 6 (Archiver) are independent
- Phase 3 (Recommendation Engine) can start once Phase 1 is done

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Core implementation before integration
- Documentation after implementation complete

---

## Implementation Strategy

### Recommended Approach

1. **Complete Phase 1**: Models → Foundation for all features
2. **Parallelize Phases 2-4**: Issue Status, Recommendation Engine, Great Projects
3. **Parallelize Phases 5-6**: Interactive Prompts, Archiver
4. **Complete Phase 7**: Integration → All features working together
5. **Complete Phase 8**: Polish → Final validation

### MVP Scope

For a minimal viable enhancement:
- Phase 1: Models (required)
- Phase 2: Issue Status (high value)
- Phase 3: Recommendation Engine (core feature)
- Phase 7: Integration (minimal, without great projects)

This delivers: 5-10 recommendations with ratings and issue status checking.

---

## Notes

- [P] tasks = different files, no dependencies
- Tests MUST be written before implementation (TDD)
- Each phase should be independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- **All commands require `uv run` prefix when using uv installation**
- **Proxy settings are centralized in `config.py`** - see `specs/001-oss-discovery/ARCHITECTURE.md`

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 69 |
| **Setup Phase** | 11 tasks |
| **Issue Status Phase** | 6 tasks |
| **Recommendation Engine Phase** | 9 tasks |
| **Great Projects Phase** | 7 tasks |
| **Interactive Prompts Phase** | 8 tasks |
| **Archiver Phase** | 9 tasks |
| **Integration Phase** | 8 tasks |
| **Polish Phase** | 11 tasks |
| **Test Tasks** | 27 tasks |
| **Parallel Opportunities** | 21 tasks (marked [P]) |

---

---

## Phase 9: Test Fixtures Setup (Real GitHub Data) 🆕 ✅

**Purpose**: Fetch real GitHub data for integration testing of new features

- [x] T110 [P] Create test fixtures directory at `tests/fixtures/`
- [x] T111 [P] Fetch real GitHub issue data for testing linked PR detection - save to `tests/fixtures/issue_with_linked_pr.json`
- [x] T112 [P] Fetch real GitHub issue data for assigned issue - save to `tests/fixtures/issue_assigned.json`
- [x] T113 [P] Fetch real GitHub issue data for closed issue - save to `tests/fixtures/issue_closed.json`
- [x] T114 [P] Fetch real GitHub issue timeline data (cross-referenced PR) - save to `tests/fixtures/issue_timeline_linked_pr.json`
- [x] T115 [P] Create sample memory.json fixture at `tests/fixtures/memory_sample.json`
- [x] T116 [P] Create sample profile.json fixture at `tests/fixtures/profile_sample.json`
- [x] T117 [P] Create sample tasks.json fixture at `tests/fixtures/tasks_sample.json`

---

## Phase 10: Model Updates for Enhancement (FOUNDATION) 🆕 ✅

**Purpose**: Core model changes that MUST be complete before implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Model Updates (TDD)

- [x] T118 [P] Write unit test for IssueStatus.has_open_pr field in `tests/unit/test_models/test_issue_status.py`
- [x] T119 [P] Write unit test for IssueStatus.is_available with linked PR in `tests/unit/test_models/test_issue_status.py`
- [x] T120 [P] Write unit test for GitHubProfileSummary model in `tests/unit/test_models/test_memory.py`
- [x] T121 [P] Write unit test for LongTermMemory.github_profile field in `tests/unit/test_models/test_memory.py`
- [x] T122 [P] Write unit test for LongTermMemory.analysis_count field in `tests/unit/test_models/test_memory.py`

### Implementation for Model Updates

- [x] T123 Add has_open_pr and linked_pr_url fields to IssueStatus model in `src/oss_navi/models/task.py`
- [x] T124 Update IssueStatus.is_available property to check has_open_pr in `src/oss_navi/models/task.py`
- [x] T125 Create GitHubProfileSummary model in `src/oss_navi/models/memory.py`
- [x] T126 Add github_profile, last_analysis_date, analysis_count fields to LongTermMemory in `src/oss_navi/models/memory.py`
- [x] T127 Increment version to 3 in LongTermMemory model in `src/oss_navi/models/memory.py`

**Checkpoint**: ✅ Models updated and tests passing - user story implementation can begin

---

## Phase 11: User Story 1 - Fix Memory Module (Priority: P1) 🎯 MVP 🆕 ✅

**Goal**: Ensure long-term memory is properly stored, updated, and used in analysis

**Independent Test**:
1. Run `oss-navi analysis` without --learn flag
2. Verify memory.json is created/updated
3. Run second analysis and verify memory content appears in prompt

### Tests for User Story 1 (TDD)

- [x] T128 [P] [US1] Write test for memory creation when missing in `tests/unit/test_services/test_analyzer.py`
- [x] T129 [P] [US1] Write test for memory update after analysis (without --learn) in `tests/unit/test_services/test_analyzer.py`
- [x] T130 [P] [US1] Write test for memory prompt includes skill_history in `tests/unit/test_services/test_analyzer.py`
- [x] T131 [P] [US1] Write test for memory prompt includes past_recommendations in `tests/unit/test_services/test_analyzer.py`
- [x] T132 [P] [US1] Write test for memory prompt includes great_projects_discovered in `tests/unit/test_services/test_analyzer.py`
- [x] T133 [P] [US1] Write test for GitHub profile summary stored in memory in `tests/unit/test_services/test_analyzer.py`
- [ ] T134 [P] [US1] Write integration test for full memory workflow in `tests/integration/test_memory_workflow.py`

### Implementation for User Story 1

- [x] T135 [US1] Add load_or_create_memory() helper function in `src/oss_navi/services/analyzer.py`
- [x] T136 [US1] Update build_prompt() to include full memory context (skill_history, great_projects, field_exploration) in `src/oss_navi/services/analyzer.py`
- [x] T137 [US1] Update update_memory_from_report() to always update (remove --learn condition) in `src/oss_navi/services/analyzer.py`
- [x] T138 [US1] Add github_profile summary update in update_memory_from_report() in `src/oss_navi/services/analyzer.py`
- [x] T139 [US1] Increment analysis_count in update_memory_from_report() in `src/oss_navi/services/analyzer.py`
- [x] T140 [US1] Update CLI analysis command to always update memory in `src/oss_navi/cli.py`
- [x] T141 [US1] Remove "if learn:" condition from memory update in `src/oss_navi/cli.py`

**Checkpoint**: ✅ Memory module fully functional - analysis updates memory every time

---

## Phase 12: User Story 2 - Enhanced Issue Status Detection (Priority: P2) 🆕

**Goal**: Detect issues that have linked pull requests (work-in-progress)

**Independent Test**:
1. Create test with issue that has cross-referenced PR
2. Verify has_open_pr is True
3. Verify issue is marked as unavailable

### Tests for User Story 2 (TDD)

- [ ] T142 [P] [US2] Write test for check_issue_timeline() with linked PR in `tests/unit/test_services/test_github.py`
- [ ] T143 [P] [US2] Write test for check_issue_timeline() without linked PR in `tests/unit/test_services/test_github.py`
- [ ] T144 [P] [US2] Write test for check_issue_timeline() with closed PR in `tests/unit/test_services/test_github.py`
- [ ] T145 [P] [US2] Write test for check_multiple_issues() rate limit handling in `tests/unit/test_services/test_github.py`
- [ ] T146 [P] [US2] Write test for generate_recommendations() with linked PR issue in `tests/unit/test_services/test_analyzer.py`
- [ ] T147 [P] [US2] Write integration test for issue status detection with real fixtures in `tests/integration/test_issue_status.py`

### Implementation for User Story 2

- [ ] T148 [US2] Add check_issue_timeline() method to GitHubClient in `src/oss_navi/services/github.py`
- [ ] T149 [US2] Implement linked PR detection via cross-referenced events in `src/oss_navi/services/github.py`
- [ ] T150 [US2] Update check_issue_status() to call check_issue_timeline() in `src/oss_navi/services/github.py`
- [ ] T151 [US2] Add rate limit protection (only check top candidates) in `src/oss_navi/services/github.py`
- [ ] T152 [US2] Update generate_recommendations() to use new IssueStatus fields in `src/oss_navi/services/analyzer.py`
- [ ] T153 [US2] Update CLI output to show linked PR status in recommendations in `src/oss_navi/cli.py`

**Checkpoint**: Issues with linked PRs correctly detected as unavailable

---

## Phase 13: User Story 3 - Optimize Recommendation Algorithm (Priority: P3) 🆕

**Goal**: Improve scoring accuracy and issue filtering

**Independent Test**:
1. Run analysis with specific learning focus
2. Verify scoring breakdown is accurate
3. Verify past recommendations get lower score (variety)

### Tests for User Story 3 (TDD)

- [ ] T154 [P] [US3] Write test for calculate_rating_breakdown() with past recommendation penalty in `tests/unit/test_services/test_analyzer.py`
- [ ] T155 [P] [US3] Write test for calculate_rating_breakdown() with normalized hotness score in `tests/unit/test_services/test_analyzer.py`
- [ ] T156 [P] [US3] Write test for calculate_rating_breakdown() with improved topic relevance in `tests/unit/test_services/test_analyzer.py`
- [ ] T157 [P] [US3] Write test for generate_recommendations() excludes past recommendations in `tests/unit/test_services/test_analyzer.py`
- [ ] T158 [P] [US3] Write test for generate_recommendations() prioritizes available issues in `tests/unit/test_services/test_analyzer.py`
- [ ] T159 [P] [US3] Write test for recommendation variety across multiple runs in `tests/unit/test_services/test_analyzer.py`

### Implementation for User Story 3

- [ ] T160 [US3] Add past_recommendation_penalty to calculate_rating_breakdown() in `src/oss_navi/services/analyzer.py`
- [ ] T161 [US3] Improve hotness score normalization (log scale) in `src/oss_navi/services/analyzer.py`
- [ ] T162 [US3] Enhance topic relevance scoring with semantic matching in `src/oss_navi/services/analyzer.py`
- [ ] T163 [US3] Update generate_recommendations() to check past recommendations from memory in `src/oss_navi/services/analyzer.py`
- [ ] T164 [US3] Defer availability scoring until after status check in `src/oss_navi/services/analyzer.py`
- [ ] T165 [US3] Add recommendation reason explaining the fit in `src/oss_navi/services/analyzer.py`

**Checkpoint**: Algorithm produces better, more varied recommendations

---

## Phase 14: Final Polish & Validation 🆕

**Purpose**: Final validation, documentation, and cleanup for enhancement

- [ ] T166 [P] Update README.md with memory module documentation
- [ ] T167 [P] Update README.md with linked PR detection documentation
- [ ] T168 [P] Update specs/001-oss-discovery/spec.md with resolved issues
- [ ] T169 Run full test suite and verify 80%+ coverage: `pytest --cov=oss_navi tests/`
- [ ] T170 Fix any failing tests
- [ ] T171 Run ruff linting: `ruff check .`
- [ ] T172 Run integration test with real GitHub API (if rate limit allows)
- [ ] T173 Validate quickstart.md scenarios work end-to-end
- [ ] T174 Update specs/001-oss-discovery/tasks.md with completion status

---

## Dependencies & Execution Order (Updated)

### New Phase Dependencies

- **Phase 9 (Fixtures)**: No dependencies - can start immediately
- **Phase 10 (Model Updates)**: Depends on Phase 9 test fixtures - BLOCKS all user stories
- **Phase 11 (US1 Memory Fix)**: Can start after Phase 10
- **Phase 12 (US2 Linked PRs)**: Can start after Phase 10 (parallel with US1)
- **Phase 13 (US3 Algorithm)**: Depends on Phase 11 and Phase 12 completion
- **Phase 14 (Polish)**: Depends on all user stories being complete

### Parallel Opportunities

**Phase 9 (Test Fixtures)** - All tasks can run in parallel:
```
T110, T111, T112, T113, T114, T115, T116, T117
```

**Phase 10 (Model Tests)** - All tests can run in parallel:
```
T118, T119, T120, T121, T122
```

**User Story 1 & 2** - Can run in parallel (different files):
```
US1: T128-T141 (analyzer.py, cli.py)
US2: T142-T153 (github.py, analyzer.py)
```

---

## Real GitHub Test Cases

The following real GitHub issues should be used for testing:

### Linked PR Detection Test Cases

1. **Issue with open linked PR**: Find an issue with a cross-referenced open PR
2. **Issue with closed linked PR**: Find an issue where PR was merged
3. **Issue without linked PR**: Any open issue without cross-references

### Memory Test Cases

1. **Fresh install**: No memory.json exists → Created with defaults
2. **After first analysis**: Memory updated with learning_goals, past_recommendations
3. **After multiple analyses**: Memory accumulates, analysis_count > 1

---

## Completed Tasks (Previous Phases)

The following phases from the original implementation are complete:

| Phase | Status | Description |
|-------|--------|-------------|
| Performance | ✅ Complete | Async fetching, parallel requests |
| Source Cleanup | ✅ Complete | Removed broken source, fixed naming |
| Proxy Support | ✅ Complete | HTTP/HTTPS/SOCKS proxy support |
| Documentation | ✅ Complete | README, contracts, quickstart updated |
| Polish | ✅ Complete | Tests passing, linting clean |

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks (All Phases)** | 174 |
| **Completed Tasks (Phases 1-8)** | 109 |
| **New Tasks (Phases 9-14)** | 65 |
| **Test Tasks** | 48 tasks |
| **Parallel Opportunities** | 35 tasks (marked [P]) |
