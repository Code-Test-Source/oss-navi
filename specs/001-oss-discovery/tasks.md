# Tasks: OSS-Navi Performance & Documentation Improvements

**Input**: Design documents from `specs/001-oss-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED per constitution principle I (Test-First Development - NON-NEGOTIABLE). Each phase includes test tasks to be written BEFORE implementation.

**Organization**: Tasks are grouped by improvement area to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Area]**: Which improvement area this task belongs to (PERF, CLEANUP, DOCS, PROXY, POLISH)
- All file paths are relative to repository root

---

## Phase 1: Performance Improvements (PERF)

**Goal**: Optimize task fetching and search to reduce sync time from 60s+ to under 30s

**Independent Test**: Run `uv run oss-navi sync --tasks` and verify total time < 30s

### Tests for Performance

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T001 [P] [PERF] Create `tests/unit/test_services/test_scraper_performance.py` with timing assertions for async fetch
- [ ] T002 [PERF] Verify performance tests fail (current sync > 60s)

### Implementation for Performance

- [x] T003 [PERF] Add async httpx client support in `src/oss_navi/services/scraper.py` for parallel YAML fetches
- [x] T004 [PERF] Implement `fetch_upforgrabs_tasks_async()` with concurrent YAML file fetching (max 10 parallel)
- [ ] T005 [PERF] Optimize `select_diverse_tasks()` with pre-indexed language/source lookup in `src/oss_navi/services/scraper.py`
- [ ] T006 [PERF] Add streaming JSON parsing for large goodfirstissues response in `src/oss_navi/services/scraper.py`
- [x] T007 [PERF] Update `fetch_and_cache_tasks()` to use async fetchers in `src/oss_navi/services/scraper.py`
- [ ] T008 [PERF] Verify performance tests pass (sync < 30s)

**Checkpoint**: Task sync should now complete in under 30 seconds

---

## Phase 2: Source Cleanup (CLEANUP)

**Goal**: Remove non-working goodfirstissue.dev source and fix cache file naming

**Independent Test**: Run `uv run oss-navi sync --tasks` and verify only working sources are fetched

### Tests for Cleanup

- [x] T009 [P] [CLEANUP] Update `tests/integration/test_scraper.py` to remove goodfirstissue.dev tests
- [x] T010 [P] [CLEANUP] Update `tests/unit/test_services/test_scraper.py` source validation tests
- [x] T011 [CLEANUP] Verify tests fail (goodfirstissue references still exist)

### Implementation for Cleanup

- [x] T012 [CLEANUP] Remove `fetch_goodfirstissue_tasks()` function from `src/oss_navi/services/scraper.py`
- [x] T013 [CLEANUP] Remove `GOODFIRSTISSUE_URL` constant from `src/oss_navi/services/scraper.py`
- [x] T014 [CLEANUP] Rename cache file constant to `GOODFIRSTISSUES_TASKS_CACHE` in `src/oss_navi/utils/paths.py`
- [x] T015 [CLEANUP] Update `fetch_and_cache_tasks()` to use correct cache file name in `src/oss_navi/services/scraper.py`
- [x] T016 [CLEANUP] Update Task model source validation to allow only "upforgrabs" and "goodfirstissues" in `src/oss_navi/models/task.py`
- [x] T017 [CLEANUP] Update `load_cached_tasks()` to use correct cache file name in `src/oss_navi/services/scraper.py`
- [x] T018 [CLEANUP] Verify tests pass

**Checkpoint**: Only working sources (Up For Grabs, Good First Issues) should be used

---

## Phase 3: Proxy Support (PROXY)

**Goal**: Add HTTP/HTTPS proxy support for users behind corporate firewalls

**Independent Test**: Run `uv run oss-navi sync` with proxy environment variables and verify requests go through proxy

### Tests for Proxy

- [x] T019 [P] [PROXY] Create `tests/unit/test_services/test_proxy.py` with mocked proxy configuration
- [x] T020 [PROXY] Verify tests fail (proxy support not implemented)

### Implementation for Proxy

- [x] T021 [P] [PROXY] Add proxy configuration to Config model in `src/oss_navi/models/config.py`
- [x] T022 [PROXY] Implement proxy support in httpx client for `src/oss_navi/services/scraper.py`
- [x] T023 [PROXY] Implement proxy support in httpx client for `src/oss_navi/services/github.py`
- [x] T024 [PROXY] Add `--http-proxy`, `--https-proxy`, `--no-proxy` options to config command in `src/oss_navi/cli.py`
- [x] T025 [PROXY] Add environment variable support (HTTP_PROXY, HTTPS_PROXY, NO_PROXY) in `src/oss_navi/config.py`
- [x] T026 [PROXY] Update `specs/001-oss-discovery/quickstart.md` with proxy configuration instructions
- [x] T027 [PROXY] Verify tests pass

**Checkpoint**: Users should be able to configure HTTP/HTTPS proxy

---

## Phase 4: Documentation Updates (DOCS)

**Goal**: Update all documentation to be consistent and accurate

**Independent Test**: Follow README.md instructions and verify tool works as documented

### Implementation for Documentation

- [x] T028 [P] [DOCS] Update `README.md` with correct task sources (Up For Grabs, Good First Issues)
- [x] T029 [P] [DOCS] Update `README.md` with proxy configuration section
- [x] T030 [P] [DOCS] Update `README.md` cache directory structure to match actual implementation
- [x] T031 [P] [DOCS] Fix `README.md` installation instructions (use `uv run` prefix)
- [x] T032 [DOCS] Update implementation memory file
- [x] T033 [DOCS] Update `pyproject.toml` description and project URLs
- [x] T034 [DOCS] Add proxy environment variables to `specs/001-oss-discovery/contracts/cli.md`

**Checkpoint**: Documentation should accurately reflect current implementation

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and improvements

- [x] T035 Run full test suite: `uv run pytest tests/ -q --tb=short --cov=oss_navi --cov-report=term-missing`
- [x] T036 Verify 80%+ test coverage maintained
- [x] T037 Run ruff linting: `uv run ruff check src/`
- [ ] T038 Manual test: `uv run oss-navi sync --tasks` completes in < 30s
- [x] T039 Manual test: `uv run oss-navi sync` with proxy works correctly (proxy auto-detected from env)
- [ ] T040 Update CHANGELOG or release notes if applicable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Performance)**: Can start immediately - no dependencies
- **Phase 2 (Cleanup)**: Can run in parallel with Phase 1 - different files
- **Phase 3 (Proxy)**: Depends on Phase 2 cleanup (removes goodfirstissue references)
- **Phase 4 (Documentation)**: Depends on Phase 1, 2, 3 completion - documents final state
- **Phase 5 (Polish)**: Depends on all previous phases

### Parallel Opportunities

Phase 1 and Phase 2 tests can run in parallel.
Phase 4 documentation tasks can run in parallel.

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Core implementation before integration
- Documentation after implementation complete

---

## Implementation Strategy

### Sequential Approach (Recommended)

1. Complete Phase 1: Performance Improvements → Faster sync
2. Complete Phase 2: Source Cleanup → Remove dead code
3. Complete Phase 3: Proxy Support → Add new feature
4. Complete Phase 4: Documentation Updates → Accurate docs
5. Complete Phase 5: Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- Tests MUST be written before implementation (TDD)
- Each phase should be independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Proxy support should respect environment variables (HTTP_PROXY, HTTPS_PROXY, NO_PROXY)
- **All commands require `uv run` prefix when using uv installation**

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 40 |
| **Performance Phase** | 8 tasks (2 test + 6 implementation) |
| **Cleanup Phase** | 10 tasks (3 test + 7 implementation) |
| **Proxy Phase** | 9 tasks (2 test + 7 implementation) |
| **Documentation Phase** | 7 tasks (all implementation) |
| **Polish Phase** | 6 tasks |
| **Test Tasks** | 7 tasks |
| **Parallel Opportunities** | 15 tasks (marked [P]) |
