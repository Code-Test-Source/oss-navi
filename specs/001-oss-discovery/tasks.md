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

- [ ] T074 [US1] Add tests for `prompt_learning_interests()` in `tests/unit/test_cli.py`
- [ ] T075 [US1] Add tests for `suggest_adjacent_fields()` in `tests/unit/test_services/test_analyzer.py`
- [ ] T076 [US1] Verify interactive prompt tests fail (functions not implemented)

### Implementation for Interactive Prompts

- [ ] T077 [US1] Implement `prompt_learning_interests()` using Click prompts in `src/oss_navi/cli.py`
- [ ] T078 [US1] Add `--explore` option for field exploration in `src/oss_navi/cli.py`
- [ ] T079 [US1] Add `--recommendations` / `-n` option for count in `src/oss_navi/cli.py`
- [ ] T080 [US1] Implement `suggest_adjacent_fields()` in `src/oss_navi/services/analyzer.py`
- [ ] T081 [US1] Verify interactive prompt tests pass

**Checkpoint**: Analysis command should prompt for learning interests interactively

---

## Phase 6: Report Archiver (US1)

**Goal**: Implement automatic report archiving after generation

**Independent Test**: Run `uv run oss-navi analysis` and verify report is auto-archived to `~/.oss-navi/state/reports/`

### Tests for Archiver

- [ ] T082 [US1] Create `tests/unit/test_services/test_archiver.py` with archiver tests
- [ ] T083 [US1] Add tests for archive naming format (YYYYMMDD_HHMMSS) in `tests/unit/test_services/test_archiver.py`
- [ ] T084 [US1] Verify archiver tests fail (module not implemented)

### Implementation for Archiver

- [ ] T085 [US1] Create `src/oss_navi/services/archiver.py` module
- [ ] T086 [US1] Implement `archive_report()` with timestamp naming in `src/oss_navi/services/archiver.py`
- [ ] T087 [US1] Implement `update_memory_with_recommendations()` in `src/oss_navi/services/archiver.py`
- [ ] T088 [US1] Integrate archiver into analysis command in `src/oss_navi/cli.py`
- [ ] T089 [US1] Add `--no-archive` option to skip auto-archiving in `src/oss_navi/cli.py`
- [ ] T090 [US1] Verify archiver tests pass

**Checkpoint**: Reports should be automatically archived after generation

---

## Phase 7: Analysis Command Integration (US1)

**Goal**: Integrate all enhanced analysis features into the analysis command

**Independent Test**: Run `uv run oss-navi analysis` and verify full enhanced report is generated

### Tests for Integration

- [ ] T091 [US1] Create `tests/integration/test_enhanced_analysis.py` with end-to-end tests
- [ ] T092 [US1] Add tests for full report structure (5-10 recommendations, great projects, field exploration) in `tests/integration/test_enhanced_analysis.py`
- [ ] T093 [US1] Verify integration tests fail (features not integrated)

### Implementation for Integration

- [ ] T094 [US1] Update `analysis` command to use new `analyzer.py` service in `src/oss_navi/cli.py`
- [ ] T095 [US1] Update Claude Code prompt template for enhanced report structure in `src/oss_navi/services/analyzer.py`
- [ ] T096 [US1] Integrate issue status checking before recommendations in `src/oss_navi/cli.py`
- [ ] T097 [US1] Add field exploration advice to report generation in `src/oss_navi/services/analyzer.py`
- [ ] T098 [US1] Verify integration tests pass

**Checkpoint**: Full enhanced analysis should produce comprehensive report

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

### Tests & Coverage

- [ ] T099 Run full test suite: `uv run pytest tests/ -q --tb=short --cov=oss_navi --cov-report=term-missing`
- [ ] T100 Verify 80%+ test coverage maintained for new modules
- [ ] T101 Run ruff linting: `uv run ruff check src/`

### Documentation Updates

- [ ] T102 [P] Update `README.md` with enhanced analysis features
- [ ] T103 [P] Update `README.md` with interactive prompts documentation
- [ ] T104 [P] Update `specs/001-oss-discovery/quickstart.md` with new analysis workflow

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

## Completed Tasks (Previous Phases)

The following phases from the original implementation are complete:

| Phase | Status | Description |
|-------|--------|-------------|
| Performance | ✅ Complete | Async fetching, parallel requests |
| Source Cleanup | ✅ Complete | Removed broken source, fixed naming |
| Proxy Support | ✅ Complete | HTTP/HTTPS/SOCKS proxy support |
| Documentation | ✅ Complete | README, contracts, quickstart updated |
| Polish | ✅ Complete | Tests passing, linting clean |
