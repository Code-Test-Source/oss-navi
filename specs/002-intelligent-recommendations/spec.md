# Feature Specification: Intelligent Recommendations & Learning Paths

**Feature Branch**: `002-intelligent-recommendations`
**Created**: 2026-03-08
**Updated**: 2026-03-08
**Status**: Draft
**Input**: User description: "Optimize recommendation algorithm with fallback strategy, integrate learning paths from csdiy.wiki and LeetCode/Codeforces, enable multi-round interactive recommendations with user personalization and blocking rules"

## Clarifications

### Session 2026-03-08

- Q: How should language matching work when no exact matches exist? → A: First scan the cached JSON for exact language matches. If found, recommend those projects. If not found, mark the language as a learning prerequisite. Then conduct a SECOND ROUND analysis recommending projects where language is NOT a prerequisite (adjacent technologies). Great project recommendations follow this same rule.
- Q: When should LeetCode/Codeforces recommendations appear? → A: LeetCode and Codeforces problems appear AUTOMATICALLY based on user's skill level and csdiy courses, even without explicit user request. If the user explicitly requests practice problems, refer to their specific requests.
- Q: What level of control should users have over the report during interactive sessions? → A: Users can ALWAYS determine where to stop, add items to report, delete parts of report, modify parts of report, or do another round of conversation.
- Q: Should there be a separate recommend command? → A: No. Recommendations are INTEGRATED into the existing `analysis` command. Recommendation logic is separated into `services/recommender.py` for clean architecture. Users run `oss-navi analysis` with recommendation options.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get Intelligent Project Recommendations (Priority: P1)

A developer wants to find open source projects that match their skills. When no exact language matches exist, the system intelligently recommends adjacent projects and identifies prerequisite skills to learn. Recommendations include relevance scores, skill gap analysis, and reasoning.

**Why this priority**: This is the core enhancement - transforming basic filtering into intelligent, algorithmic recommendations that handle edge cases gracefully.

**Independent Test**: Can be fully tested by running analysis with various language profiles (including obscure languages with no matches) and verifying recommendations include scores, reasoning, and fallback suggestions.

**Acceptance Scenarios**:

1. **Given** a user requests projects in Go, **When** the system scans cached task data, **Then** it first searches for Go projects and recommends them if found
2. **Given** a user requests projects in Rust but no Rust tasks exist in cache, **When** analysis completes, **Then** the system marks Rust as a learning prerequisite and conducts a second round recommending adjacent technologies (C/C++, Go)
3. **Given** a user requests great project recommendations, **When** the system searches, **Then** it follows the same language-first rule before suggesting projects in other languages
4. **Given** recommendations are generated, **When** user views the report, **Then** each recommendation includes skill gap analysis showing what they will learn
5. **Given** a user with limited GitHub activity, **When** analysis runs, **Then** the system uses explicitly stated interests and recommends popular beginner-friendly projects

---

### User Story 2 - Multi-Round Interactive Recommendations (Priority: P2)

A developer wants an interactive recommendation experience where they can provide feedback, select repositories for detailed analysis, refine results over multiple rounds, and have full control over the final report content.

**Why this priority**: Interactive experiences produce better outcomes by respecting user agency and allowing iterative refinement.

**Independent Test**: Can be fully tested by running analysis in interactive mode and completing a multi-round conversation that refines recommendations based on user feedback.

**Acceptance Scenarios**:

1. **Given** initial recommendations are displayed, **When** the user provides feedback (accept/reject/request alternatives), **Then** subsequent recommendations incorporate that feedback
2. **Given** a user sees an interesting project, **When** they select it for detailed analysis, **Then** the system performs code analysis and adds it to their report
3. **Given** a user rejects a recommendation, **When** they provide a reason, **Then** the system learns from this and adjusts future recommendations
4. **Given** a user wants to modify their report, **When** they delete or edit a section, **Then** the report is updated accordingly
5. **Given** a user wants to continue exploring, **When** they request another round, **Then** the system generates new recommendations based on accumulated context
6. **Given** a user is satisfied with results, **When** they choose to stop, **Then** the session ends and the final report is saved

---

### User Story 3 - Set Personalization Rules and Blocking (Priority: P2)

A developer wants to personalize their recommendation experience by specifying multiple languages, skill levels, and blocking rules for projects or topics they don't want to see.

**Why this priority**: Personalization transforms generic recommendations into actionable guidance tailored to individual needs.

**Independent Test**: Can be fully tested by configuring personalization rules and verifying they are respected in subsequent recommendations.

**Acceptance Scenarios**:

1. **Given** a user sets their profile with multiple languages (Python, Go, Rust), **When** analysis runs, **Then** recommendations span all specified languages with appropriate weighting
2. **Given** a user blocks "TypeScript" projects, **When** recommendations are generated, **Then** no TypeScript projects appear
3. **Given** a user sets skill level as "beginner" for Rust, **When** Rust projects are recommended, **Then** they are limited to beginner-friendly issues
4. **Given** a user blocks a specific maintainer or organization, **When** recommendations are generated, **Then** projects from that source are excluded

---

### User Story 4 - Discover Learning Paths (Priority: P3)

A developer wants recommendations connected to structured learning resources. The system automatically suggests LeetCode/Codeforces problems based on skill level, and when projects require unfamiliar skills, the system suggests courses and practice problems.

**Why this priority**: Learning path integration transforms OSS contributions into structured skill development.

**Independent Test**: Can be fully tested by running analysis and verifying LeetCode/Codeforces problems appear automatically based on skill level, with additional suggestions for skill gaps.

**Acceptance Scenarios**:

1. **Given** a user runs analysis, **When** the report is generated, **Then** LeetCode/Codeforces problems appear automatically based on the user's skill level and csdiy courses
2. **Given** a user explicitly requests practice problems, **When** they specify topics or difficulty, **Then** the system refers to their specific requests
3. **Given** a recommendation requires unfamiliar skills, **When** the user views the report, **Then** prerequisite courses from csdiy.wiki are suggested
4. **Given** a learning path is suggested, **When** the user follows it, **Then** they see progressive difficulty from beginner to advanced
5. **Given** a user completes a course or problem, **When** they update their profile, **Then** future recommendations reflect improved skills

---

### User Story 5 - Detailed Code Analysis on Demand (Priority: P3)

A developer wants to select specific repositories from recommendations for detailed code analysis and architecture review, which gets added to their personalized report.

**Why this priority**: On-demand analysis gives users agency to deep-dive into promising projects without overwhelming initial recommendations.

**Independent Test**: Can be fully tested by selecting repositories during interactive recommendations and verifying detailed analysis appears in the final report.

**Acceptance Scenarios**:

1. **Given** a list of recommendations, **When** the user selects a repository for analysis, **Then** detailed code analysis including architecture, key files, and contribution areas is generated
2. **Given** detailed analysis is complete, **When** the user adds it to their report, **Then** the final report includes the full analysis
3. **Given** multiple repositories are analyzed, **When** the user reviews the report, **Then** all selected analyses are included with clear organization
4. **Given** a user skips detailed analysis, **When** they proceed to report, **Then** the report contains only standard recommendations without detailed analysis

---

### Edge Cases

- What happens when all user's languages have no matches? System recommends the most popular beginner-friendly projects across all languages and suggests learning prerequisites
- What happens when csdiy.wiki or LeetCode APIs are unavailable? Gracefully degrade to only OSS project recommendations with a note about unavailable learning resources
- What happens when a user blocks all projects in a category? Inform the user that no recommendations match their constraints and suggest relaxing filters
- What happens when recommendation algorithms produce conflicting results? Use hybrid scoring to combine multiple algorithm outputs with configurable weights
- What happens when a user's profile is empty and no preferences are set? Prompt for interactive onboarding to gather initial interests and goals
- What happens when a user's blocking rules conflict (block TypeScript but want frontend projects)? Explain the conflict and suggest alternative preferences

## Requirements *(mandatory)*

### Functional Requirements

**Intelligent Recommendation Engine**
- **FR-001**: The system MUST implement multiple recommendation algorithms (collaborative filtering, Apriori, FP-Growth, content-based filtering)
- **FR-002**: The system MUST compute relevance scores (1-10 scale) for each recommendation with clear reasoning
- **FR-003**: The system MUST perform skill gap analysis showing what the user will learn from each project
- **FR-004**: The system MUST handle cold-start scenarios (limited profile data) by using explicit interests and popular beginner projects
- **FR-005**: The system MUST implement two-round language matching:
  - **Round 1**: Scan cached JSON for exact language matches; if found, recommend those projects
  - **Round 2**: If no matches, mark language as learning prerequisite and recommend adjacent technology projects
- **FR-006**: The system MUST apply the same language-first rule to great project recommendations

**Multi-Round Interactive Experience**
- **FR-007**: The system MUST support multi-round recommendation workflows where user feedback refines results
- **FR-008**: The system MUST allow users to accept, reject, or request alternatives for each recommendation
- **FR-009**: The system MUST track user feedback and use it to improve subsequent recommendations within a session
- **FR-010**: The system MUST persist session state so users can resume across multiple invocations
- **FR-011**: The system MUST allow users to delete parts of their report during interactive sessions
- **FR-012**: The system MUST allow users to modify parts of their report during interactive sessions
- **FR-013**: The system MUST allow users to request another round of recommendations at any point
- **FR-014**: The system MUST allow users to stop and finalize the report at any point

**User Personalization**
- **FR-015**: The system MUST support multiple languages per user with primary, secondary, and learning designations
- **FR-016**: The system MUST allow per-language skill levels (beginner, intermediate, advanced)
- **FR-017**: The system MUST allow users to block specific projects, maintainers, organizations, or topics
- **FR-018**: The system MUST persist user preferences locally with export, modify, and delete capabilities
- **FR-019**: The system MUST respect blocking rules in all recommendation outputs

**Learning Path Integration**
- **FR-020**: The system MUST integrate with csdiy.wiki for course recommendations organized by topic and difficulty
- **FR-021**: The system MUST integrate with LeetCode API for algorithm practice problem recommendations
- **FR-022**: The system MUST integrate with Codeforces API for competitive programming problem recommendations
- **FR-023**: The system MUST automatically include LeetCode/Codeforces problems in reports based on user's skill level and csdiy courses, even without explicit user request
- **FR-024**: The system MUST use explicit user requests for practice problems when provided, falling back to automatic skill-based recommendations otherwise
- **FR-025**: The system MUST suggest prerequisites when recommending projects requiring unfamiliar skills
- **FR-026**: The system MUST provide progressive difficulty paths from beginner to advanced

**Detailed Code Analysis**
- **FR-027**: The system MUST allow users to select repositories for detailed code analysis
- **FR-028**: The system MUST generate architecture analysis for selected repositories
- **FR-029**: The system MUST identify key files and contribution areas for selected repositories
- **FR-030**: The system MUST add detailed analyses to the final report upon user request

**Algorithm Enhancements**
- **FR-031**: The system MUST implement association rule mining (Apriori) to discover skill-project patterns from historical data
- **FR-032**: The system MUST implement FP-Growth for efficient pattern discovery in large datasets
- **FR-033**: The system MUST use collaborative filtering to find similar users and recommend projects they contributed to
- **FR-034**: The system MUST combine multiple algorithm outputs into hybrid recommendations with configurable weights

**Data Persistence**
- **FR-035**: The system MUST store user preferences (languages, skills, blocks) in `~/.oss-navi/state/preferences.json`
- **FR-036**: The system MUST store session state for multi-round interactions in `~/.oss-navi/state/sessions/`
- **FR-037**: The system MUST store learned patterns from recommendation algorithms in `~/.oss-navi/state/patterns.json`

### Testing Requirements

- **FR-038**: The system MUST have unit tests for all recommendation algorithms with known input/output pairs
- **FR-039**: The system MUST have integration tests for external API integrations (csdiy.wiki, LeetCode, Codeforces) with mocked responses
- **FR-040**: The system MUST have unit tests for personalization rule evaluation
- **FR-041**: The system MUST achieve minimum 80% test coverage

### Security Requirements

- **FR-042**: The system MUST validate all external API responses before processing
- **FR-043**: The system MUST handle external API failures gracefully with informative fallback messages
- **FR-044**: The system MUST NOT expose user preference data without explicit user action

### Key Entities

- **UserPreferences**: Represents user's language settings, skill levels, domain interests, and blocking rules. Persists across sessions and informs all recommendations.

- **Recommendation**: Represents a single project recommendation with relevance score, reasoning, skill gap analysis, and learning prerequisites. Generated by recommendation engine.

- **RecommendationSession**: Represents a multi-round interaction state including initial recommendations, user feedback, refined recommendations, selected projects for analysis, and report modifications.

- **LearningResource**: Represents an external learning resource (course, tutorial, practice problem) from csdiy.wiki, LeetCode, or Codeforces with topic, difficulty, and URL.

- **CodeAnalysis**: Represents detailed analysis of a selected repository including architecture overview, key files, contribution areas, and code reading hints.

- **BlockingRule**: Represents a user-defined rule to exclude specific projects, maintainers, organizations, or topics from recommendations.

- **RecommendationPattern**: Represents a discovered association between skills, languages, and successful project contributions. Used by Apriori and FP-Growth algorithms.

- **ReportSection**: Represents a section of the interactive report that can be added, deleted, or modified by the user during the session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive recommendations with relevance scores and reasoning within 90 seconds of analysis
- **SC-002**: When no language matches exist, users receive at least 3 alternative recommendations with prerequisite guidance
- **SC-003**: Multi-round sessions show measurable improvement in recommendation relevance after user feedback
- **SC-004**: Users can configure preferences (languages, skills, blocks) and see them reflected in recommendations within one session
- **SC-005**: Learning resource integration successfully suggests relevant courses/problems for 80% of skill gaps identified
- **SC-006**: Users who complete onboarding receive more relevant recommendations than users who skip it
- **SC-007**: Recommendation algorithm accuracy improves over time as user feedback accumulates
- **SC-008**: LeetCode/Codeforces problems appear in 100% of reports, automatically matched to user skill level

## Assumptions

- csdiy.wiki maintains a structured format for course data that can be scraped or accessed via API
- LeetCode and Codeforces APIs are publicly accessible with reasonable rate limits
- Users are willing to provide explicit preferences during onboarding for better recommendations
- Historical contribution data (from synced profiles) provides sufficient signal for collaborative filtering
- Users understand the difference between "primary", "secondary", and "learning" language designations
- Blocking rules are user-maintained and the user understands the implications of broad blocks
- Users understand the two-round recommendation process (exact match first, then adjacent)

## Out of Scope

- Machine learning model training for recommendations (use algorithmic approaches only)
- Real-time collaboration on recommendations
- Social features (sharing preferences, following users)
- Mobile platform support
- Integration with paid learning platforms (Coursera, Udemy paid courses)
- Automated project contribution (PR creation, issue claiming)
