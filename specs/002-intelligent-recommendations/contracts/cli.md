# CLI Contract: Intelligent Recommendations & Learning Paths

**Feature**: 002-intelligent-recommendations
**Date**: 2026-03-08

## Overview

This document defines the CLI command contracts for the intelligent recommendations feature. Commands extend the existing `oss-navi` CLI.

## Command: `oss-navi recommend`

Start an interactive recommendation session.

### Usage

```
oss-navi recommend [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--language`, `-l` | TEXT | (from profile) | Primary language for recommendations |
| `--learn` | TEXT | None | Learning focus (language or skill) |
| `--mode`, `-m` | TEXT | normal | Recommendation mode: fast, normal, thinking |
| `--interactive`, `-i` | FLAG | True | Enable interactive mode |
| `--non-interactive` | FLAG | False | Disable interactive mode (one-shot) |
| `--rounds` | INT | 3 | Maximum recommendation rounds |
| `--output`, `-o` | PATH | stdout | Output file for final report |
| `--session` | TEXT | None | Resume existing session by ID |
| `--list-sessions` | FLAG | - | List active sessions |

### Recommendation Modes

| Mode | Algorithms | Time | Memory | Use Case |
|------|------------|------|--------|----------|
| `fast` | Content-based only | <30s | <50MB | Quick exploration, low-resource |
| `normal` | Surprise SVD/KNN | <90s | <200MB | Balanced quality and speed |
| `thinking` | LightFM + Apriori | <180s | <500MB | Maximum recommendation quality |

### Examples

```bash
# Start interactive recommendation session (normal mode)
oss-navi recommend

# Fast mode for quick exploration
oss-navi recommend --mode fast

# Thinking mode for best recommendations
oss-navi recommend --mode thinking

# Specify language focus
oss-navi recommend --language go

# Resume previous session
oss-navi recommend --session abc123

# Non-interactive (one-shot) mode
oss-navi recommend --non-interactive --output report.md

# Learning-focused recommendations with thinking mode
oss-navi recommend --learn rust --mode thinking
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | No recommendations found |
| 3 | Session not found |
| 4 | API failure (cached data used) |

### Output Format

Interactive mode produces markdown report to stdout or file:

```markdown
# OSS-Navi Recommendations

## Session: {session_id}

### Round 1: Language Match (Go)

#### Recommended Projects

1. **project-name** (Score: 8/10)
   - URL: https://github.com/owner/repo
   - Language: Go
   - Why: Matches your Go expertise and interests in distributed systems
   - Skills you'll develop: concurrency, microservices
   - [Issue: Fix handler timeout](https://github.com/...)

#### Learning Resources (Auto-suggested)

- LeetCode: Two Sum (Easy) - Arrays
- Codeforces: Problem 1234 (Rating 800) - Basics
- csdiy.wiki: MIT 6.006 - Introduction to Algorithms

---

### What would you like to do?
[A] Accept recommendation  [R] Reject  [D] Detailed analysis
[S] Request alternatives   [N] Next round   [F] Finalize report
```

---

## Command: `oss-navi prefs`

Manage user preferences (languages, skills, blocking rules).

### Usage

```
oss-navi prefs [COMMAND] [OPTIONS]
```

### Subcommands

#### `prefs set-language`

Set a language in your profile.

```
oss-navi prefs set-language LANG [OPTIONS]

Options:
  --type, -t       primary|secondary|learning  [default: primary]
  --level, -l      beginner|intermediate|advanced  [default: intermediate]
```

**Example**:
```bash
oss-navi prefs set-language python --type primary --level advanced
oss-navi prefs set-language rust --type learning --level beginner
```

#### `prefs remove-language`

Remove a language from your profile.

```
oss-navi prefs remove-language LANG
```

#### `prefs block`

Add a blocking rule.

```
oss-navi prefs block TYPE VALUE [OPTIONS]

Arguments:
  TYPE    project|maintainer|organization|topic|language
  VALUE   The value to block

Options:
  --reason, -r    Reason for blocking
```

**Example**:
```bash
oss-navi prefs block language typescript --reason "Not interested"
oss-navi prefs block organization some-org
```

#### `prefs unblock`

Remove a blocking rule.

```
oss-navi prefs unblock TYPE VALUE
```

#### `prefs show`

Display current preferences.

```
oss-navi prefs show
```

#### `prefs export`

Export preferences to JSON file.

```
oss-navi prefs export [FILE]

Arguments:
  FILE    Output file  [default: preferences.json]
```

#### `prefs import`

Import preferences from JSON file.

```
oss-navi prefs import FILE
```

---

## Command: `oss-navi session`

Manage recommendation sessions.

### Usage

```
oss-navi session [COMMAND] [OPTIONS]
```

### Subcommands

#### `session list`

List all sessions.

```
oss-navi session list [OPTIONS]

Options:
  --status    active|completed|all  [default: active]
```

#### `session show`

Show session details.

```
oss-navi session show SESSION_ID
```

#### `session delete`

Delete a session.

```
oss-navi session delete SESSION_ID
```

#### `session export`

Export session report.

```
oss-navi session export SESSION_ID [OPTIONS]

Options:
  --format, -f    markdown|json  [default: markdown]
  --output, -o    Output file (default: stdout)
```

---

## Command: `oss-navi analyze`

Request detailed code analysis for a specific repository.

### Usage

```
oss-navi analyze REPO [OPTIONS]

Arguments:
  REPO    Repository in owner/repo format

Options:
  --output, -o    Output file for analysis
  --add-to-session    Add to current/recent session
```

### Example

```bash
oss-navi analyze golang/go --output go-analysis.md
```

### Output Format

```markdown
# Code Analysis: golang/go

## Architecture Overview

The Go project is organized into...

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| src/cmd/compile/main.go | Compiler entry point | ~500 |
| src/runtime/proc.go | Scheduler implementation | ~2000 |

## Contribution Areas

| Area | Difficulty | Beginner-friendly |
|------|------------|-------------------|
| Documentation | Easy | Yes |
| Standard library | Medium | Yes |
| Compiler | Hard | No |

## Code Reading Hints

1. Start with `src/cmd/go/main.go` to understand the CLI
2. The runtime scheduler is in `src/runtime/`
3. ...
```

---

## Command: `oss-navi sync --learning`

Sync learning resources (csdiy.wiki, LeetCode, Codeforces).

### Usage

```
oss-navi sync --learning [OPTIONS]

Options:
  --csdiy        Sync csdiy.wiki courses
  --leetcode     Sync LeetCode problems
  --codeforces   Sync Codeforces problems
  --all          Sync all sources  [default]
  --force        Force re-sync even if cached
```

### Example

```bash
oss-navi sync --learning --leetcode --codeforces
```

---

## Interactive Mode Prompts

### Main Menu

```
What would you like to do?
  [A] Accept recommendation
  [R] Reject recommendation
  [D] Request detailed analysis
  [S] Request alternatives
  [M] Modify report
  [N] Next round
  [F] Finalize and save report
  [Q] Quit without saving
```

### After Accepting

```
Recommendation accepted! Added to your report.

Would you like to:
  [C] Continue reviewing
  [D] Request detailed analysis for this project
  [N] Next round
  [F] Finalize report
```

### After Rejecting

```
Why did you reject this recommendation?
  [L] Not interested in language
  [T] Not interested in topic
  [D] Too difficult
  [E] Too easy
  [O] Other (type reason)

This helps improve future recommendations.
```

### Report Modification

```
Report Sections:
  1. [Recommendation] project-a (Score: 8)
  2. [Recommendation] project-b (Score: 7)
  3. [Learning Path] Algorithm Practice

What would you like to do?
  [D] Delete section
  [E] Edit section
  [R] Reorder sections
  [A] Add custom section
  [B] Back to recommendations
```

---

## Error Messages

| Error | Message | Action |
|-------|---------|--------|
| No recommendations | "No projects found matching your criteria. Try broadening your search or adding more languages." | Suggest `--learn` flag or preference changes |
| Session not found | "Session {id} not found. Use `oss-navi session list` to see active sessions." | List sessions |
| API failure | "Unable to fetch {source} data. Using cached data from {date}." | Continue with cache |
| Blocked results | "All recommendations were blocked by your rules. Consider relaxing blocking rules." | Show blocking rules |
| Missing dependency | "Mode '{mode}' requires {library}. Install with: pip install oss-navi[recommend]" | Fall back to fast mode or suggest installation |
| Mode unavailable | "LightFM not installed. Falling back to normal mode." | Use fallback mode |

---

## Configuration File

Preferences are stored in `~/.oss-navi/state/preferences.json`:

```json
{
  "languages": [
    {"language": "python", "type": "primary", "skill_level": "advanced"},
    {"language": "go", "type": "secondary", "skill_level": "intermediate"},
    {"language": "rust", "type": "learning", "skill_level": "beginner"}
  ],
  "domain_interests": [
    {"domain": "web", "interest_level": 8},
    {"domain": "systems", "interest_level": 6}
  ],
  "blocking_rules": [
    {"block_type": "language", "value": "typescript", "reason": "Not interested"}
  ],
  "created_at": "2026-03-08T...",
  "updated_at": "2026-03-08T..."
}
```
