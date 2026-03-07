# Tasks: OSS-Navi CLI Tool

**Input**: Design documents from `/specs/001-oss-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/cli.md

**Tests**: Tests are REQUIRED per constitution principle I (Test-First Development - NON-NEGOTIABLE). Each user story phase includes test tasks to be written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow the single project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md (src/oss_navi/, tests/, etc.)
- [x] T002 Create pyproject.toml with Python 3.11+ and pinned dependencies (click, httpx, beautifulsoup4, pydantic, pytest, pytest-cov, ruff, pip-audit)
- [x] T003 [P] Create src/oss_navi/__init__.py with version and package metadata
- [x] T004 [P] Create tests/conftest.py with pytest fixtures and test configuration
- [x] T005 [P] Create README.md with project description and installation instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Path Utilities

- [x] T006 Create src/oss_navi/utils/__init__.py
- [x] T007 Create src/oss_navi/utils/paths.py with OSS_NAVI_HOME constant and subdirectory paths (cache/, state/, temp/)

### Cache Utilities

- [x] T008 Create src/oss_navi/utils/cache.py with JSON read/write functions and 24-hour expiration check

### Core Models

- [x] T009 Create src/oss_navi/models/__init__.py
- [x] T010 [P] Create src/oss_navi/models/config.py with Config and Filters Pydantic models
- [x] T011 [P] Create src/oss_navi/models/user_profile.py with UserProfile, Activity, Language Pydantic models
- [x] T012 [P] Create src/oss_navi/models/task.py with Task and Repository Pydantic models
- [x] T013 [P] Create src/oss_navi/models/report.py with AnalysisReport Pydantic model
- [x] T014 [P] Create src/oss_navi/models/memory.py with LongTermMemory, SkillSnapshot, PastRecommendation Pydantic models

### Test Infrastructure

- [x] T015 [P] Create tests/unit/__init__.py
- [x] T016 [P] Create tests/unit/test_models/__init__.py
- [x] T017 [P] Create tests/unit/test_services/__init__.py
- [x] T018 [P] Create tests/unit/test_utils/__init__.py
- [x] T019 Create pytest configuration in pyproject.toml with coverage settings (80% minimum)

### Services Base

- [x] T020 Create src/oss_navi/services/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Get Personalized Project Recommendations (Priority: P1) 🎯 MVP

**Goal**: Generate a Markdown report with skill assessment and 1-2 project recommendations using Claude Code

**Independent Test**: Run analysis command with sample cached data and verify Markdown report is generated with skill assessment and recommendations

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US1] Create tests/unit/test_models/test_report.py with AnalysisReport model tests
- [x] T022 [P] [US1] Create tests/unit/test_services/test_analyzer.py with mock Claude Code subprocess tests
- [x] T023 [US1] Verify tests fail (RED phase) before proceeding to implementation

### Implementation for User Story 1

- [x] T024 [P] [US1] Create src/oss_navi/services/analyzer.py with Claude Code subprocess invocation, 60-second timeout (FR-039), and validated prompt building (FR-040)
- [x] T025 [P] [US1] Create src/oss_navi/cli.py with analysis command implementation (click command)
- [x] T026 [US1] Implement task filtering by stars and recency in src/oss_navi/services/analyzer.py
- [x] T027 [US1] Implement hotness score calculation in src/oss_navi/services/analyzer.py
- [x] T028 [US1] Implement report generation and saving to temp directory in src/oss_navi/services/analyzer.py
- [x] T029 [US1] Add --learn flag support in analysis command in src/oss_navi/cli.py
- [x] T030 [US1] Add --output flag support in analysis command in src/oss_navi/cli.py
- [x] T031 [US1] Add error handling for Claude Code not found in src/oss_navi/services/analyzer.py
- [x] T032 [US1] Add error handling for no cached data in src/oss_navi/cli.py
- [x] T033 [US1] Verify tests pass (GREEN phase) after implementation

**Checkpoint**: At this point, User Story 1 should be fully functional with sample cached data

---

## Phase 4: User Story 2 - Sync Profile and Task Data (Priority: P2)

**Goal**: Fetch GitHub profile and scrape tasks from Up For Grabs and Good First Issue, caching locally

**Independent Test**: Run sync command with configured credentials and verify data is cached in ~/.oss-navi/cache/

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T034 [P] [US2] Create tests/unit/test_models/test_user_profile.py with UserProfile model tests
- [x] T035 [P] [US2] Create tests/unit/test_models/test_task.py with Task and Repository model tests
- [x] T036 [P] [US2] Create tests/integration/test_github.py with mocked GitHub API responses
- [x] T037 [P] [US2] Create tests/integration/test_scraper.py with mocked HTTP responses
- [x] T038 [US2] Verify tests fail (RED phase) before proceeding to implementation

### Implementation for User Story 2

- [x] T039 [P] [US2] Create src/oss_navi/services/github.py with GitHub API client using httpx
- [x] T040 [P] [US2] Create src/oss_navi/services/scraper.py with Up For Grabs JSON fetcher
- [x] T041 [US2] Add Good First Issue web scraper using beautifulsoup4 in src/oss_navi/services/scraper.py
- [x] T042 [US2] Implement GitHub profile fetching in src/oss_navi/services/github.py (repos, languages, activity)
- [x] T043 [US2] Implement cache storage for profile data in src/oss_navi/services/github.py
- [x] T044 [US2] Implement cache storage for task data in src/oss_navi/services/scraper.py
- [x] T045 [US2] Add sync command to src/oss_navi/cli.py with --github and --tasks flags
- [x] T046 [US2] Add --force flag to sync command to ignore cache in src/oss_navi/cli.py
- [x] T047 [US2] Add error handling for GitHub API rate limits in src/oss_navi/services/github.py
- [x] T048 [US2] Add error handling for Good First Issue unavailable in src/oss_navi/services/scraper.py
- [x] T049 [US2] Create cache metadata.json with timestamps in src/oss_navi/utils/cache.py
- [x] T050 [US2] Add GitHub API response validation (FR-036) in src/oss_navi/services/github.py
- [x] T051 [US2] Add HTML sanitization for scraped content (FR-037) in src/oss_navi/services/scraper.py
- [x] T052 [US2] Add URL validation for scraped task data (FR-038) in src/oss_navi/services/scraper.py
- [x] T053 [US2] Add graceful authentication failure handling (FR-042) in src/oss_navi/services/github.py
- [x] T054 [US2] Verify tests pass (GREEN phase) after implementation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Configure the Tool (Priority: P3)

**Goal**: Store GitHub credentials and filter preferences securely in ~/.oss-navi/

**Independent Test**: Run config commands and verify settings are persisted in ~/.oss-navi/state/config.json

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T055 [P] [US3] Create tests/unit/test_models/test_config.py with Config and Filters model tests
- [x] T056 [P] [US3] Create tests/unit/test_utils/test_paths.py with path utility tests
- [x] T057 [US3] Verify tests fail (RED phase) before proceeding to implementation

### Implementation for User Story 3

- [x] T058 [US3] Create src/oss_navi/config.py with configuration loading and saving functions
- [x] T059 [US3] Implement secure token storage with 0600 permissions in src/oss_navi/config.py
- [x] T060 [US3] Add config command to src/oss_navi/cli.py with --github-username option
- [x] T061 [US3] Add --github-token option to config command with token validation via test API call (FR-032) in src/oss_navi/cli.py
- [x] T062 [US3] Add --blog-repo option to config command in src/oss_navi/cli.py
- [x] T063 [US3] Add --min-stars and --max-age filter options to config command in src/oss_navi/cli.py
- [x] T064 [US3] Add --list option to display current configuration in src/oss_navi/cli.py
- [x] T065 [US3] Add --reset option to clear configuration in src/oss_navi/cli.py
- [x] T066 [US3] Implement directory structure creation (~/.oss-navi/ with cache/, state/, temp/) in src/oss_navi/config.py
- [x] T067 [US3] Add input validation for GitHub username in src/oss_navi/config.py
- [x] T068 [US3] Add input validation for GitHub token format in src/oss_navi/config.py
- [x] T069 [US3] Add descriptive error messages for invalid config values (FR-035) in src/oss_navi/config.py
- [x] T070 [US3] Ensure tokens are never logged or displayed in error messages (FR-034) across src/oss_navi/
- [x] T071 [US3] Verify tests pass (GREEN phase) after implementation

**Checkpoint**: At this point, all three core user stories should work independently

---

## Phase 6: User Story 4 - Publish Analysis Reports (Priority: P4)

**Goal**: Archive reports and optionally push to a configured blog repository

**Independent Test**: Run publish command and verify report is archived and/or pushed to git repository

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T072 [P] [US4] Create tests/unit/test_models/test_memory.py with LongTermMemory model tests
- [x] T073 [P] [US4] Create tests/unit/test_services/test_publisher.py with mocked git operations
- [x] T074 [US4] Verify tests fail (RED phase) before proceeding to implementation

### Implementation for User Story 4

- [x] T075 [US4] Create src/oss_navi/services/publisher.py with report archiving function
- [x] T076 [US4] Implement report archiving with timestamp naming in src/oss_navi/services/publisher.py
- [x] T077 [US4] Implement git operations (add, commit, push) in src/oss_navi/services/publisher.py
- [x] T078 [US4] Add publish command to src/oss_navi/cli.py with --push flag
- [x] T079 [US4] Add --message/-m option for commit message in src/oss_navi/cli.py
- [x] T080 [US4] Add --list option to show archived reports in src/oss_navi/cli.py
- [x] T081 [US4] Add error handling for missing blog repo configuration in src/oss_navi/cli.py
- [x] T082 [US4] Add error handling for git operation failures in src/oss_navi/services/publisher.py
- [x] T083 [US4] Verify tests pass (GREEN phase) after implementation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T084 [P] Add global --verbose/-v flag to CLI in src/oss_navi/cli.py
- [x] T085 [P] Add global --quiet/-q flag to CLI in src/oss_navi/cli.py
- [x] T086 [P] Add --version flag to CLI in src/oss_navi/cli.py
- [x] T087 Add consistent error output formatting (✓, ✗, ⚠ symbols) with no sensitive info leakage (FR-041) in src/oss_navi/cli.py
- [x] T088 [P] Update README.md with complete usage examples and installation steps
- [ ] T089 Add long-term memory update parsing from Claude Code output in src/oss_navi/services/analyzer.py
- [x] T090 Verify 80%+ test coverage with pytest --cov
- [ ] T091 Run pip-audit for dependency vulnerability scanning (FR-044)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 can be tested with sample/mocked cache data
  - US2 needs config from US3 for GitHub API authentication
  - US3 is fully independent
  - US4 needs reports from US1
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - Analysis**: Can start after Foundational; testable with sample cache data
- **User Story 2 (P2) - Sync**: Can start after Foundational; needs config (US3) for full functionality
- **User Story 3 (P3) - Config**: Can start after Foundational; fully independent
- **User Story 4 (P4) - Publish**: Can start after Foundational; needs reports from US1

### TDD Workflow Per Story

1. **RED**: Write test tasks (marked "Tests for User Story X")
2. **Verify Fail**: Run tests, confirm they fail
3. **GREEN**: Write implementation tasks
4. **Verify Pass**: Run tests, confirm they pass
5. **REFACTOR**: Clean up code while keeping tests green

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational model tasks marked [P] can run in parallel
- All test tasks within a user story marked [P] can run in parallel
- All US1 implementation tasks marked [P] can run in parallel
- All US2 implementation tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with integration testing after)

---

## Implementation Strategy

### TDD-Compliant MVP First (User Story 1 Only with Sample Data)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. **RED**: Complete tests for US1 (T021-T023)
4. **GREEN**: Complete implementation for US1 (T024-T033)
5. **STOP and VALIDATE**: Verify 80%+ coverage for US1
6. Deploy/demo if ready

### Full Flow (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. **RED**: Write US3 tests → **GREEN**: Implement US3 (Config) → Enables authentication
3. **RED**: Write US2 tests → **GREEN**: Implement US2 (Sync) → Enables data fetching
4. **RED**: Write US1 tests → **GREEN**: Implement US1 (Analysis) → Core MVP complete
5. **STOP and VALIDATE**: Verify 80%+ coverage, test full flow end-to-end
6. **RED**: Write US4 tests → **GREEN**: Implement US4 (Publish) → Extended features
7. Add Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- **TDD is NON-NEGOTIABLE**: Tests MUST be written before implementation
- Each user story should be independently completable and testable (with appropriate test data)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 91 |
| **Setup Phase** | 5 tasks |
| **Foundational Phase** | 15 tasks |
| **US1 (Analysis)** | 13 tasks (3 test + 10 implementation) |
| **US2 (Sync)** | 21 tasks (5 test + 16 implementation) |
| **US3 (Config)** | 17 tasks (3 test + 14 implementation) |
| **US4 (Publish)** | 12 tasks (3 test + 9 implementation) |
| **Polish Phase** | 8 tasks |
| **Test Tasks** | 17 tasks |
| **Parallel Opportunities** | 30 tasks (marked [P]) |
