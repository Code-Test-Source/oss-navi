<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.1.0
Modified principles:
  - None (existing principles unchanged)
Added sections:
  - VIII. Intelligent Recommendation System (NEW)
  - IX. User-Centric Personalization (NEW)
  - X. Learning Path Integration (NEW)
  - XI. Interactive User Experience (NEW)
  - Enhanced Technology Constraints (recommendation algorithms, data sources)
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section will auto-adapt)
  - .specify/templates/spec-template.md: ✅ Compatible (Requirements structure supports new principles)
  - .specify/templates/tasks-template.md: ✅ Compatible (Phase structure supports new features)
Follow-up TODOs:
  - Implement Apriori and FP-Growth recommendation algorithms
  - Integrate csdiy.wiki learning resources
  - Integrate LeetCode/Codeforces API
  - Design multi-round recommendation workflow
  - Implement user preference blocking system
-->

# OSS-Navi Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

All production code MUST be written following Test-Driven Development (TDD):

- Tests MUST be written before implementation
- Tests MUST fail initially (RED phase) before any implementation
- Minimal code is written to pass tests (GREEN phase)
- Code is refactored while keeping tests green (REFACTOR phase)
- Minimum 80% test coverage is required for all modules

**Rationale**: TDD ensures code correctness, provides living documentation, and enables confident refactoring. Tests written first capture requirements precisely.

### II. Clean Architecture

Code MUST be organized following clean architecture principles:

- **Separation of Concerns**: Business logic independent of frameworks, UI, and external systems
- **Dependency Rule**: Dependencies point inward toward higher-level policies
- **Modular Design**: Each module has a single, well-defined responsibility
- **Interface Segregation**: Prefer small, focused interfaces over large, general-purpose ones
- **Files < 800 lines**: Extract utilities from large modules; high cohesion, low coupling

**Rationale**: Clean architecture enables maintainability, testability, and flexibility to change external dependencies without affecting core business logic.

### III. Security-First

Security MUST be considered from the beginning of all development:

- **Input Validation**: All external inputs validated before processing
- **Secrets Management**: No hardcoded secrets; use environment variables or secret managers
- **Injection Prevention**: Parameterized queries, sanitized outputs, CSRF protection
- **Authentication/Authorization**: Verified for all protected resources
- **Audit Logging**: Security-relevant events logged with context

**Rationale**: Security vulnerabilities are expensive to fix post-deployment and can cause significant reputational and financial damage.

### IV. Code Quality & Simplicity

Code MUST prioritize clarity and simplicity:

- **YAGNI**: You Aren't Gonna Need It - implement only what is currently required
- **DRY**: Don't Repeat Yourself - extract common logic into reusable components
- **Self-Documenting**: Code should be readable without excessive comments
- **No Premature Abstraction**: Create abstractions only when patterns emerge
- **Immutable Patterns**: Prefer creating new objects over mutating existing ones

**Rationale**: Simple code is easier to understand, maintain, and debug. Premature complexity creates technical debt.

### V. Documentation Standards

Documentation MUST be maintained alongside code:

- **API Documentation**: All public APIs documented with purpose, parameters, return values, and examples
- **Architecture Decisions**: Significant decisions recorded with context and rationale
- **Setup Instructions**: Clear steps for development environment setup
- **Change Logs**: Notable changes documented for each release

**Rationale**: Documentation enables team members to understand, use, and maintain the codebase effectively. Undocumented systems become unmaintainable.

### VI. Observability & Debuggability

Systems MUST be designed for operational visibility:

- **Structured Logging**: Logs include context (timestamps, request IDs, user context)
- **Metrics**: Key performance indicators tracked and exposed
- **Error Handling**: Errors captured with full context; no silent failures
- **Tracing**: Request flows traceable across service boundaries (where applicable)

**Rationale**: Observable systems enable rapid debugging, performance optimization, and incident response.

### VII. Versioning & Breaking Changes

Changes MUST follow semantic versioning:

- **Format**: MAJOR.MINOR.PATCH (e.g., 1.0.0)
- **MAJOR**: Breaking changes requiring migration
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible
- **Deprecation Path**: Breaking changes require deprecation notice and migration guide

**Rationale**: Predictable versioning enables users to upgrade confidently and plan for breaking changes.

### VIII. Intelligent Recommendation System (NEW)

Recommendations MUST leverage advanced algorithms and handle edge cases gracefully:

- **Algorithm Diversity**: Use multiple recommendation strategies:
  - Collaborative filtering based on similar user profiles
  - Association rule mining (Apriori, FP-Growth) for skill-project patterns
  - Content-based filtering for language/topic matching
  - Hybrid approaches combining multiple signals
- **Fallback Strategy**: When no tasks match user's primary language:
  - Mark the language as a learning prerequisite
  - Recommend beginner-friendly projects in adjacent technologies
  - Suggest foundational learning resources before contribution
- **Ranking Quality**: Recommendations MUST include:
  - Relevance score (1-10 scale) with clear reasoning
  - Skill gap analysis showing what user will learn
  - Project health indicators (activity, maintainer responsiveness)
- **Cold Start Handling**: For users with limited GitHub activity:
  - Use explicitly stated interests and learning goals
  - Recommend popular, well-documented beginner projects
  - Provide onboarding questionnaires to gather preferences

**Rationale**: Intelligent recommendations maximize user success by matching projects to skills, learning goals, and preferences. Advanced algorithms discover non-obvious patterns that simple filtering misses.

### IX. User-Centric Personalization (NEW)

The system MUST adapt to individual user preferences and learning journeys:

- **Multi-Dimensional Profiles**: Support multiple languages and skills:
  - Users can specify primary, secondary, and learning languages
  - Skill levels (beginner, intermediate, advanced) per language
  - Domain interests (web, ML, systems, DevOps, etc.)
- **Preference Learning**: System learns from user interactions:
  - Track accepted/rejected recommendations with reasons
  - Allow users to block specific projects, maintainers, or topics
  - Respect user-defined rules (e.g., "no TypeScript projects", "prefer Rust")
  - Persist preferences across sessions with explicit user control
- **Recommendation Explanations**: Every recommendation MUST explain:
  - Why this project matches the user's profile
  - What skills the user will develop
  - Estimated difficulty based on user's current skill level
- **Privacy by Design**: User preference data:
  - Stored locally under user control
  - Never shared without explicit consent
  - Can be exported, modified, or deleted at any time

**Rationale**: Personalization transforms generic recommendations into actionable guidance. User control over preferences builds trust and improves recommendation quality over time.

### X. Learning Path Integration (NEW)

Recommendations MUST connect to structured learning resources:

- **Curated Learning Paths**: Integrate external learning resources:
  - **CSDIY.wiki**: Computer science courses organized by topic and difficulty
  - **LeetCode/Codeforces**: Algorithm and data structure practice problems
  - **Official Documentation**: Links to authoritative guides for each technology
- **Skill Prerequisites**: When recommending projects requiring unfamiliar skills:
  - Identify prerequisite knowledge needed
  - Link to relevant courses or tutorials
  - Suggest practice problems to build foundational skills
- **Progressive Difficulty**: Learning paths should:
  - Start with achievable tasks to build confidence
  - Gradually increase complexity as user demonstrates mastery
  - Celebrate milestones and learning achievements
- **Contextual Recommendations**: Based on user's goals:
  - Career-focused: Projects valued by employers in target domain
  - Learning-focused: Projects that teach specific concepts
  - Portfolio-building: Projects that demonstrate specific skills

**Rationale**: Connecting contributions to learning paths transforms OSS participation into structured skill development. Users can see clear progression from beginner to expert.

### XI. Interactive User Experience (NEW)

The system MUST provide an interactive, multi-round recommendation experience:

- **Multi-Round Workflow**: Support iterative refinement:
  - Initial recommendations based on profile analysis
  - User feedback drives subsequent recommendations
  - Converge on optimal matches through conversation
- **User Agency**: Users MUST be able to:
  - Select specific repositories for detailed code analysis
  - Add selected recommendations to their report
  - Request alternatives with specific criteria
  - Save interesting projects for later review
- **Transparency**: System MUST show:
  - What data informs recommendations
  - How recommendations are ranked
  - What filters are currently active
- **Session Continuity**: Across multiple sessions:
  - Resume previous recommendation conversations
  - Reference previously viewed projects
  - Build upon past decisions without starting over

**Rationale**: Interactive experiences respect user agency and produce better outcomes than one-shot recommendations. Users understand their options and make informed decisions.

## Technology Constraints

### Approved Technology Stack

- **Language**: Python 3.11+
- **CLI Framework**: Click
- **HTTP Client**: httpx with httpx[socks] for proxy support
- **Data Models**: Pydantic v2
- **Configuration**: PyYAML
- **Testing**: pytest with pytest-cov (80% minimum coverage)
- **Linting/Formatting**: ruff

### Data Sources

- **GitHub API**: User profiles, repository data, issue tracking
- **Up For Grabs**: YAML task data via GitHub API
- **Good First Issues**: JSON API from goodfirstissues.com
- **CSDIY.wiki**: Course catalog and learning paths
- **LeetCode API**: Algorithm problems and user progress
- **Codeforces API**: Competitive programming problems

### Recommendation Algorithms

- **Association Rule Mining**: Apriori, FP-Growth for skill-project patterns
- **Collaborative Filtering**: User similarity-based recommendations
- **Content-Based Filtering**: Language/topic matching
- **Hybrid Systems**: Combining multiple algorithmic approaches

### Compliance Requirements

- **License Compliance**: All dependencies must have compatible licenses
- **Vulnerability Scanning**: Dependencies scanned for known vulnerabilities
- **Accessibility**: UI components must meet WCAG 2.1 AA standards (where applicable)
- **Privacy**: User data stored locally with user control

### Deployment Standards

- **Environment Parity**: Development, staging, and production environments must be consistent
- **Infrastructure as Code**: Infrastructure changes version-controlled
- **Rollback Capability**: Deployments must support rollback to previous version

## Development Workflow

### Code Review Requirements

- All code changes require review before merge
- Reviews must verify compliance with constitution principles
- At least one approval required from a team member familiar with the area
- Automated checks (tests, linting) must pass

### Quality Gates

- **Pre-commit**: Linting and formatting checks
- **Pre-merge**: All tests passing, coverage threshold met
- **Pre-deploy**: Security scan, integration tests passing

### Branch Strategy

- **main/master**: Always deployable; protected branch
- **feature/***: Short-lived feature branches
- **fix/***: Bug fix branches
- **Conventional Commits**: Use conventional commit message format

## Governance

This constitution supersedes all other development practices and guidelines.

### Amendment Process

1. **Proposal**: Document proposed change with rationale
2. **Review**: Team reviews impact on existing code and workflows
3. **Approval**: Requires consensus from project stakeholders
4. **Migration Plan**: For breaking changes, document migration steps
5. **Update**: Increment constitution version per semantic versioning

### Compliance Review

- All pull requests must verify compliance with relevant principles
- Complexity introduced without necessity must be justified
- Exceptions to non-negotiable principles require documented approval

### Runtime Guidance

For implementation-specific guidance, refer to:
- Project README.md for setup and usage
- CLAUDE.md for AI assistant development guidance
- API documentation for interface contracts

**Version**: 1.1.0 | **Ratified**: 2026-03-07 | **Last Amended**: 2026-03-08
