# Tasks: OSS-Navi CLI Tool

**Input**: Design documents from `/specs/001-oss-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/cli.md

**Tests**: Tests are NOT explicitly requested in the feature specification. They are omitted per the spec.

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

- [ ] T001 Create project directory structure per plan.md (src/oss_navi/, tests/, etc.)
- [ ] T002 Create pyproject.toml with Python 3.11+ and dependencies (click, httpx, beautifulsoup4, pydantic, pytest, pytest-cov, ruff)
- [ ] T003 [P] Create src/oss_navi/__init__.py with version and package metadata
- [ ] T004 [P] Create tests/conftest.py with pytest fixtures and test configuration
- [ ] T005 [P] Create README.md with project description and installation instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Path Utilities

- [ ] T006 Create src/oss_navi/utils/__init__.py
- [ ] T007 Create src/oss_navi/utils/paths.py with OSS_NAVI_HOME constant and subdirectory paths (cache/, state/, temp/)

### Cache Utilities

- [ ] T008 Create src/oss_navi/utils/cache.py with JSON read/write functions and 24-hour expiration check

### Core Models

- [ ] T009 Create src/oss_navi/models/__init__.py
- [ ] T010 [P] Create src/oss_navi/models/config.py with Config and Filters Pydantic models
- [ ] T011 [P] Create src/oss_navi/models/user_profile.py with UserProfile, Activity, Language Pydantic models
- [ ] T012 [P] Create src/oss_navi/models/task.py with Task and Repository Pydantic models
- [ ] T013 [P] Create src/oss_navi/models/report.py with AnalysisReport Pydantic model
- [ ] T014 [P] Create src/oss_navi/models/memory.py with LongTermMemory, SkillSnapshot, PastRecommendation Pydantic models

### Services Base

- [ ] T015 Create src/oss_navi/services/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Get Personalized Project Recommendations (Priority: P1) 🎯 MVP

**Goal**: Generate a Markdown report with skill assessment and 1-2 project recommendations using Claude Code

**Independent Test**: Run analysis command with sample cached data and verify Markdown report is generated with skill assessment and recommendations

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create src/oss_navi/services/analyzer.py with Claude Code subprocess invocation and prompt building
- [ ] T017 [P] [US1] Create src/oss_navi/cli.py with analysis command implementation (click command)
- [ ] T018 [US1] Implement task filtering by stars and recency in src/oss_navi/services/analyzer.py
- [ ] T019 [US1] Implement hotness score calculation in src/oss_navi/services/analyzer.py
- [ ] T020 [US1] Implement report generation and saving to temp directory in src/oss_navi/services/analyzer.py
- [ ] T021 [US1] Add --learn flag support in analysis command in src/oss_navi/cli.py
- [ ] T022 [US1] Add --output flag support in analysis command in src/oss_navi/cli.py
- [ ] T023 [US1] Add error handling for Claude Code not found in src/oss_navi/services/analyzer.py
- [ ] T024 [US1] Add error handling for no cached data in src/oss_navi/cli.py

**Checkpoint**: At this point, User Story 1 should be fully functional with sample cached data

---

## Phase 4: User Story 2 - Sync Profile and Task Data (Priority: P2)

**Goal**: Fetch GitHub profile and scrape tasks from Up For Grabs and Good First Issue, caching locally

**Independent Test**: Run sync command with configured credentials and verify data is cached in ~/.oss-navi/cache/

### Implementation for User Story 2

- [ ] T025 [P] [US2] Create src/oss_navi/services/github.py with GitHub API client using httpx
- [ ] T026 [P] [US2] Create src/oss_navi/services/scraper.py with Up For Grabs JSON fetcher
- [ ] T027 [US2] Add Good First Issue web scraper using beautifulsoup4 in src/oss_navi/services/scraper.py
- [ ] T028 [US2] Implement GitHub profile fetching in src/oss_navi/services/github.py (repos, languages, activity)
- [ ] T029 [US2] Implement cache storage for profile data in src/oss_navi/services/github.py
- [ ] T030 [US2] Implement cache storage for task data in src/oss_navi/services/scraper.py
- [ ] T031 [US2] Add sync command to src/oss_navi/cli.py with --github and --tasks flags
- [ ] T032 [US2] Add --force flag to sync command to ignore cache in src/oss_navi/cli.py
- [ ] T033 [US2] Add error handling for GitHub API rate limits in src/oss_navi/services/github.py
- [ ] T034 [US2] Add error handling for Good First Issue unavailable in src/oss_navi/services/scraper.py
- [ ] T035 [US2] Create cache metadata.json with timestamps in src/oss_navi/utils/cache.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Configure the Tool (Priority: P3)

**Goal**: Store GitHub credentials and filter preferences securely in ~/.oss-navi/

**Independent Test**: Run config commands and verify settings are persisted in ~/.oss-navi/state/config.json

### Implementation for User Story 3

- [ ] T036 [US3] Create src/oss_navi/config.py with configuration loading and saving functions
- [ ] T037 [US3] Implement secure token storage with 0600 permissions in src/oss_navi/config.py
- [ ] T038 [US3] Add config command to src/oss_navi/cli.py with --github-username option
- [ ] T039 [US3] Add --github-token option to config command in src/oss_navi/cli.py
- [ ] T040 [US3] Add --blog-repo option to config command in src/oss_navi/cli.py
- [ ] T041 [US3] Add --min-stars and --max-age filter options to config command in src/oss_navi/cli.py
- [ ] T042 [US3] Add --list option to display current configuration in src/oss_navi/cli.py
- [ ] T043 [US3] Add --reset option to clear configuration in src/oss_navi/cli.py
- [ ] T044 [US3] Implement directory structure creation (~/.oss-navi/ with cache/, state/, temp/) in src/oss_navi/config.py
- [ ] T045 [US3] Add input validation for GitHub username in src/oss_navi/config.py
- [ ] T046 [US3] Add input validation for GitHub token format in src/oss_navi/config.py

**Checkpoint**: At this point, all three core user stories should work independently

---

## Phase 6: User Story 4 - Publish Analysis Reports (Priority: P4)

**Goal**: Archive reports and optionally push to a configured blog repository

**Independent Test**: Run publish command and verify report is archived and/or pushed to git repository

### Implementation for User Story 4

- [ ] T047 [US4] Create src/oss_navi/services/publisher.py with report archiving function
- [ ] T048 [US4] Implement report archiving with timestamp naming in src/oss_navi/services/publisher.py
- [ ] T049 [US4] Implement git operations (add, commit, push) in src/oss_navi/services/publisher.py
- [ ] T050 [US4] Add publish command to src/oss_navi/cli.py with --push flag
- [ ] T051 [US4] Add --message/-m option for commit message in src/oss_navi/cli.py
- [ ] T052 [US4] Add --list option to show archived reports in src/oss_navi/cli.py
- [ ] T053 [US4] Add error handling for missing blog repo configuration in src/oss_navi/cli.py
- [ ] T054 [US4] Add error handling for git operation failures in src/oss_navi/services/publisher.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T055 [P] Add global --verbose/-v flag to CLI in src/oss_navi/cli.py
- [ ] T056 [P] Add global --quiet/-q flag to CLI in src/oss_navi/cli.py
- [ ] T057 [P] Add --version flag to CLI in src/oss_navi/cli.py
- [ ] T058 Add consistent error output formatting (✓, ✗, ⚠ symbols) across all commands in src/oss_navi/cli.py
- [ ] T059 [P] Update README.md with complete usage examples and installation steps
- [ ] T060 Add long-term memory update parsing from Claude Code output in src/oss_navi/services/analyzer.py
- [ ] T061 Verify 80%+ test coverage (manual: pytest --cov)

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

### Recommended Implementation Order

For a working end-to-end flow, implement in this order:
1. **Foundational** → Core models and utilities
2. **US3 (Config)** → Enables authentication for US2
3. **US2 (Sync)** → Generates cache data for US1
4. **US1 (Analysis)** → Core MVP functionality
5. **US4 (Publish)** → Extended functionality
6. **Polish** → Final touches

### Within Each User Story

- Services before CLI commands
- Core implementation before error handling
- Story complete before moving to next

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational model tasks marked [P] can run in parallel
- All US1 tasks marked [P] can run in parallel
- All US2 tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with integration testing after)

---

## Parallel Example: User Story 1

```bash
# Launch all parallelizable tasks for User Story 1 together:
Task: "Create src/oss_navi/services/analyzer.py with Claude Code subprocess invocation"
Task: "Create src/oss_navi/cli.py with analysis command implementation"

# Then sequential tasks:
Task: "Implement task filtering by stars and recency"
Task: "Implement hotness score calculation"
# ... etc
```

---

## Implementation Strategy

### MVP First (User Story 1 Only with Sample Data)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (with sample cache data for testing)
4. **STOP and VALIDATE**: Test User Story 1 independently with mocked data
5. Deploy/demo if ready

### Full Flow (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 3 (Config) → Enables authentication
3. Add User Story 2 (Sync) → Enables data fetching
4. Add User Story 1 (Analysis) → Core MVP complete
5. **STOP and VALIDATE**: Test full flow end-to-end
6. Add User Story 4 (Publish) → Extended features
7. Add Polish → Production ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Analysis) - test with sample data
   - Developer B: User Story 3 (Config) - fully independent
3. After US3 complete:
   - Developer C: User Story 2 (Sync) - now has config support
4. After US1 and US2 complete:
   - Developer D: User Story 4 (Publish)
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable (with appropriate test data)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 61 |
| **Setup Phase** | 5 tasks |
| **Foundational Phase** | 10 tasks |
| **US1 (Analysis)** | 9 tasks |
| **US2 (Sync)** | 11 tasks |
| **US3 (Config)** | 11 tasks |
| **US4 (Publish)** | 8 tasks |
| **Polish Phase** | 7 tasks |
| **Parallel Opportunities** | 18 tasks (marked [P]) |
