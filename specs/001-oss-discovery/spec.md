# Feature Specification: OSS-Navi CLI Tool

**Feature Branch**: `001-oss-discovery`
**Created**: 2026-03-07
**Status**: Draft
**Input**: User description: "OSS-Navi is a CLI tool that helps programmers discover and contribute to open source projects"

## Clarifications

### Session 2026-03-07

- Q: How should the GitHub token be stored securely? → A: File with restricted permissions (0600) in `~/.oss-navi/`
- Q: How long should cached data remain valid? → A: Cache expires after 24 hours
- Q: What format should cached data be stored in? → A: JSON files (human-readable, easy debugging)
- Q: What structure should long-term memory use? → A: Single JSON file with skill evolution history and past recommendations
- Q: What are the default task filter values? → A: 50+ stars, issues from last 90 days

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get Personalized Project Recommendations (Priority: P1)

A developer wants to find open source projects that match their skills and learning goals. They run the analysis command and receive a curated list of beginner-friendly issues with personalized recommendations.

**Why this priority**: This is the core value proposition - helping developers find the right OSS projects to contribute to. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by running the analysis command with a configured GitHub username and verifying that a Markdown report is generated with skill assessment and project recommendations.

**Acceptance Scenarios**:

1. **Given** a user has configured their GitHub username, **When** they run the analysis command, **Then** a Markdown report is generated containing their skill assessment and 1-2 project recommendations
2. **Given** a user runs analysis with `--learn python`, **When** the report is generated, **Then** recommendations prioritize projects matching their learning focus
3. **Given** the analysis completes, **When** the user views the report, **Then** it includes code reading hints for recommended projects
4. **Given** the analysis completes, **When** the user views the report, **Then** it includes an updated long-term memory section

---

### User Story 2 - Sync Profile and Task Data (Priority: P2)

A developer wants to refresh their GitHub profile data and fetch the latest open source tasks. They run the sync command to pull their latest activity and scrape current opportunities.

**Why this priority**: Fresh data is essential for accurate recommendations. This enables the core analysis feature to work with current information.

**Independent Test**: Can be fully tested by running the sync command and verifying that profile data is stored locally and task data is fetched from both sources.

**Acceptance Scenarios**:

1. **Given** a user has configured their GitHub credentials, **When** they run the sync command, **Then** their GitHub profile data (commits, languages, activity) is fetched and cached locally
2. **Given** the sync command runs, **When** task scraping completes, **Then** tasks from Up For Grabs and Good First Issues are stored in the local cache
3. **Given** tasks are scraped, **When** filtering is applied, **Then** tasks are ranked by a "hotness" score based on stars and recency
4. **Given** the sync completes, **When** the user checks the cache directory, **Then** data is persisted under `~/.oss-navi/cache/`

---

### User Story 3 - Configure the Tool (Priority: P3)

A new user wants to set up OSS-Navi with their GitHub credentials and preferences. They run the config command to store their settings securely.

**Why this priority**: Configuration is a one-time setup that enables all other features. Required before the tool can be used effectively.

**Independent Test**: Can be fully tested by running config commands and verifying settings are persisted correctly.

**Acceptance Scenarios**:

1. **Given** a user runs the config command with their GitHub username, **When** the command completes, **Then** the username is stored in the configuration
2. **Given** a user runs the config command with their GitHub token, **When** the command completes, **Then** the token is stored securely
3. **Given** a user runs the config command without arguments, **When** the command completes, **Then** current configuration values are displayed
4. **Given** configuration is set, **When** the user checks `~/.oss-navi/`, **Then** the directory structure is created with `cache/`, `state/`, and `temp/` subdirectories

---

### User Story 4 - Publish Analysis Reports (Priority: P4)

A developer wants to share their OSS contribution journey. They run the publish command to archive their report and optionally push it to their blog repository.

**Why this priority**: Publishing extends the tool's value but is not required for the core functionality of getting recommendations.

**Independent Test**: Can be fully tested by running the publish command and verifying the report is archived and/or pushed to a git repository.

**Acceptance Scenarios**:

1. **Given** an analysis report exists, **When** the user runs the publish command, **Then** the report is archived in the state directory
2. **Given** a blog repository is configured, **When** the user runs publish with push enabled, **Then** the report is committed and pushed to the blog repository
3. **Given** no blog repository is configured, **When** the user runs publish, **Then** the report is archived locally only

---

### Edge Cases

- What happens when GitHub API rate limits are reached? Display informative error and use cached data if available
- What happens when Good First Issues API is unavailable? Gracefully fall back to Up For Grabs data only
- What happens when Claude Code is not installed or not in PATH? Display clear error message with installation instructions
- What happens when no matching tasks are found for the user's criteria? Report indicates no matches and suggests broadening filters
- What happens when the user has no public GitHub activity? Report notes limited profile data and recommendations are more generic
- What happens when `--learn` is provided with an unrecognized technology? Accept any input and use it as-is for matching

## Requirements *(mandatory)*

### Functional Requirements

**GitHub Integration**
- **FR-001**: The system MUST fetch the user's GitHub profile including commits, languages, and activity via the GitHub API
- **FR-002**: The system MUST authenticate with GitHub using a personal access token stored in a file with restricted permissions (0600) under `~/.oss-navi/`
- **FR-003**: The system MUST cache GitHub profile data locally with a 24-hour expiration to minimize API calls

**Task Discovery**
- **FR-004**: The system MUST scrape open source tasks from Up For Grabs (YAML files via GitHub API)
- **FR-005**: The system MUST scrape open source tasks from Good First Issues (JSON API from goodfirstissues.com)
- **FR-006**: The system MUST filter tasks by minimum star count (default: 50 stars, configurable)
- **FR-007**: The system MUST filter tasks by recency (default: issues from last 90 days, configurable)
- **FR-008**: The system MUST compute a "hotness" score calculated as stars divided by age in days
- **FR-009**: The system MUST cache scraped task data locally with timestamps and a 24-hour expiration

**Learning Focus**
- **FR-010**: The system MUST accept a learning focus via the `--learn` CLI flag
- **FR-011**: The system MUST incorporate the learning focus into the analysis prompt

**Analysis & Reporting**
- **FR-012**: The system MUST combine user profile, learning focus, filtered tasks, and past memory into a structured prompt
- **FR-013**: The system MUST invoke Claude Code as a local subprocess to generate analysis
- **FR-014**: The system MUST generate a Markdown report containing:
  - Skill assessment based on GitHub profile
  - Learning direction guidance
  - Top 1-2 project recommendations with code reading hints
  - Long-term memory update section
- **FR-015**: The system MUST save generated reports to the state directory

**Publishing**
- **FR-016**: The system MUST archive analysis reports with timestamps
- **FR-017**: The system MUST support publishing reports to a configured git repository
- **FR-018**: The system MUST support git push for blog publication

**CLI Commands**
- **FR-019**: The system MUST provide a `config` command for managing settings
- **FR-020**: The system MUST provide a `sync` command for fetching profile and task data
- **FR-021**: The system MUST provide an `analysis` command for generating recommendations
- **FR-022**: The system MUST provide a `publish` command for archiving and sharing reports

**Data Management**
- **FR-023**: The system MUST store all data under `~/.oss-navi/`
- **FR-024**: The system MUST organize data into `cache/`, `state/`, and `temp/` subdirectories
- **FR-025**: The system MUST persist long-term memory as a single JSON file in the state directory, containing skill evolution history and past recommendations
- **FR-026**: The system MUST store cached data as JSON files for human readability and debugging

### Testing Requirements

- **FR-027**: The system MUST have unit tests for all core models (Config, UserProfile, Task, AnalysisReport, LongTermMemory)
- **FR-028**: The system MUST have integration tests for GitHub API client with mocked responses
- **FR-029**: The system MUST have integration tests for web scraper with mocked HTTP responses
- **FR-030**: The system MUST achieve minimum 80% test coverage as verified by pytest-cov
- **FR-031**: All tests MUST be written before implementation code (TDD Red-Green-Refactor cycle)

### Security Requirements

**Token & Credentials**
- **FR-032**: The system MUST validate GitHub tokens at configuration time by making a test API call
- **FR-033**: The system MUST display a clear error message (without revealing the token) when authentication fails due to invalid or expired tokens
- **FR-034**: The system MUST NEVER log, display, or include GitHub tokens in error messages, debug output, or reports

**Input Validation**
- **FR-035**: The system MUST reject invalid configuration values with a descriptive error message explaining the expected format
- **FR-036**: The system MUST validate GitHub API response structure before processing (handle malformed JSON gracefully)

**External Data Handling**
- **FR-037**: The system MUST sanitize HTML entities from scraped content to prevent injection issues in reports
- **FR-038**: The system MUST validate URLs from scraped task data to ensure they are well-formed GitHub URLs

**Subprocess Security**
- **FR-039**: The system MUST enforce a 60-second timeout for Claude Code subprocess invocation
- **FR-040**: The system MUST only pass validated, structured data to Claude Code subprocess (no arbitrary user input directly to CLI)

**Error Handling**
- **FR-041**: The system MUST ensure error messages do not reveal sensitive information (tokens, file paths with usernames, etc.)
- **FR-042**: The system MUST handle authentication failures gracefully with actionable error messages

**Dependencies**
- **FR-043**: The system MUST pin all dependency versions in requirements.txt or pyproject.toml
- **FR-044**: The system MUST support dependency vulnerability scanning via pip-audit or similar tool

### Key Entities

- **UserProfile**: Represents the user's GitHub profile with commit history, language statistics, and activity metrics. Used to assess skills and match with projects.

- **Task**: Represents an open source contribution opportunity with title, description, repository info, star count, age, and hotness score. Sourced from Up For Grabs and Good First Issue.

- **LearningFocus**: Represents what the user is currently learning. Provided via CLI flag and used to personalize recommendations.

- **AnalysisReport**: Represents the generated Markdown output containing skill assessment, recommendations, and memory updates. Timestamped and archived.

- **Configuration**: Represents user settings including GitHub credentials, blog repository path, and filter preferences.

- **LongTermMemory**: Represents accumulated insights about the user's OSS journey. Persists across sessions and informs future recommendations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive personalized project recommendations within 60 seconds of running the analysis command
- **SC-002**: The tool successfully fetches data from at least one task source (Up For Grabs or Good First Issues) in 95% of sync attempts
- **SC-003**: Generated reports include actionable code reading hints for all recommended projects
- **SC-004**: Users can configure the tool and run their first analysis within 5 minutes of installation
- **SC-005**: Memory persistence works correctly - insights from previous analyses appear in subsequent reports
- **SC-006**: The tool gracefully handles API failures or source unavailability without crashing

## Assumptions

- The user has a GitHub account with some public activity (commits, repositories)
- The user has Claude Code installed locally and it's available in PATH
- The user has a GitHub Personal Access Token for API authentication (required for higher rate limits)
- Good First Issues JSON API structure remains relatively stable; if it changes significantly, data fetching may need updates
- The user's blog repository (if configured) uses git and is accessible from the local machine
- Default filter values (minimum stars, recency thresholds) are reasonable starting points that can be adjusted via configuration

## Out of Scope

- Authentication via OAuth flow (personal access token only)
- Multi-user or team support
- Web interface or GUI
- Direct issue assignment or pull request creation
- Integration with issue trackers beyond GitHub
- Real-time notifications or background sync
- Mobile platform support
