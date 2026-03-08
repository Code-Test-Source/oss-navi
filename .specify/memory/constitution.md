<!--
Sync Impact Report
==================
Version change: N/A → 1.0.0 (Initial constitution creation)
Modified principles: N/A (initial version)
Added sections: All (initial version)
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section present)
  - .specify/templates/spec-template.md: ✅ Compatible (Requirements structure aligns)
  - .specify/templates/tasks-template.md: ✅ Compatible (Phase structure supports principles)
Follow-up TODOs: None
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

## Technology Constraints

### Approved Technology Stack

- **Language**: To be determined based on project requirements
- **Testing Framework**: Must support TDD workflow with fast feedback loops
- **Package Management**: Use project-appropriate package manager (npm, pip, cargo, etc.)
- **Linting/Formatting**: Automated code quality tools required

### Compliance Requirements

- **License Compliance**: All dependencies must have compatible licenses
- **Vulnerability Scanning**: Dependencies scanned for known vulnerabilities
- **Accessibility**: UI components must meet WCAG 2.1 AA standards (where applicable)

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

**Version**: 1.0.0 | **Ratified**: 2026-03-07 | **Last Amended**: 2026-03-07
