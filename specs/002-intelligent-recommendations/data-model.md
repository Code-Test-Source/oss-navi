# Data Model: Intelligent Recommendations & Learning Paths

**Feature**: 002-intelligent-recommendations
**Date**: 2026-03-08

## Overview

This document defines the data entities for the intelligent recommendations feature. All entities are implemented as Pydantic v2 models for validation and JSON serialization.

## Entities

### RecommendationMode

Represents the algorithm complexity mode for recommendations.

```python
class RecommendationMode(str, Enum):
    FAST = "fast"         # Content-based only, <30s
    NORMAL = "normal"     # Surprise SVD/KNN, <90s
    THINKING = "thinking" # LightFM + Apriori, <180s

class ModeConfig(BaseModel):
    """Configuration for each recommendation mode."""
    mode: RecommendationMode
    max_time_seconds: int
    max_memory_mb: int
    algorithms: list[str]
    requires_numpy: bool
    requires_surprise: bool
    requires_lightfm: bool

# Predefined configurations
MODE_CONFIGS: dict[RecommendationMode, ModeConfig] = {
    RecommendationMode.FAST: ModeConfig(
        mode=RecommendationMode.FAST,
        max_time_seconds=30,
        max_memory_mb=50,
        algorithms=["content_based"],
        requires_numpy=False,
        requires_surprise=False,
        requires_lightfm=False,
    ),
    RecommendationMode.NORMAL: ModeConfig(
        mode=RecommendationMode.NORMAL,
        max_time_seconds=90,
        max_memory_mb=200,
        algorithms=["surprise_svd", "surprise_knn"],
        requires_numpy=True,
        requires_surprise=True,
        requires_lightfm=False,
    ),
    RecommendationMode.THINKING: ModeConfig(
        mode=RecommendationMode.THINKING,
        max_time_seconds=180,
        max_memory_mb=500,
        algorithms=["lightfm", "apriori"],
        requires_numpy=True,
        requires_surprise=True,
        requires_lightfm=True,
    ),
}
```

**File**: `src/oss_navi/models/recommendation.py`

---

### UserPreferences

Represents user's language settings, skill levels, domain interests, and blocking rules.

```python
class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class LanguageType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    LEARNING = "learning"

class LanguageProfile(BaseModel):
    language: str  # e.g., "python", "rust", "go"
    type: LanguageType
    skill_level: SkillLevel

class DomainInterest(BaseModel):
    domain: str  # e.g., "web", "ml", "systems", "devops"
    interest_level: int  # 1-10 scale

class UserPreferences(BaseModel):
    languages: list[LanguageProfile] = []
    domain_interests: list[DomainInterest] = []
    blocking_rules: list[BlockingRule] = []
    created_at: datetime
    updated_at: datetime

    def get_primary_languages(self) -> list[str]: ...
    def get_learning_languages(self) -> list[str]: ...
    def is_blocked(self, project: dict) -> bool: ...
```

**File**: `src/oss_navi/models/preferences.py`

**Storage**: `~/.oss-navi/state/preferences.json`

---

### BlockingRule

Represents a user-defined rule to exclude specific projects, maintainers, organizations, or topics from recommendations.

```python
class BlockType(str, Enum):
    PROJECT = "project"        # Block specific repository
    MAINTAINER = "maintainer"  # Block by maintainer username
    ORGANIZATION = "organization"  # Block by org name
    TOPIC = "topic"            # Block by topic/tag
    LANGUAGE = "language"      # Block by language

class BlockingRule(BaseModel):
    block_type: BlockType
    value: str  # The value to block
    reason: str | None = None  # Optional user-provided reason
    created_at: datetime

    def matches(self, project: dict) -> bool: ...
```

**File**: `src/oss_navi/models/preferences.py`

---

### RecommendationSession

Represents a multi-round interaction state including initial recommendations, user feedback, refined recommendations, and selected projects for analysis.

```python
class FeedbackType(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    REQUEST_ALTERNATIVE = "request_alternative"

class UserFeedback(BaseModel):
    recommendation_id: str
    feedback_type: FeedbackType
    reason: str | None = None
    timestamp: datetime

class RecommendationRound(BaseModel):
    round_number: int
    recommendations: list["Recommendation"]
    user_feedback: list[UserFeedback] = []
    selected_for_analysis: list[str] = []  # recommendation IDs
    generated_at: datetime

class RecommendationSession(BaseModel):
    session_id: str  # UUID
    mode: RecommendationMode = RecommendationMode.NORMAL  # Recommendation mode
    user_preferences: UserPreferences
    rounds: list[RecommendationRound] = []
    report_sections: list["ReportSection"] = []
    status: str  # "active", "completed", "abandoned"
    created_at: datetime
    updated_at: datetime

    def add_round(self, round: RecommendationRound) -> None: ...
    def add_feedback(self, feedback: UserFeedback) -> None: ...
    def get_all_rejected_ids(self) -> set[str]: ...
    def get_all_accepted_ids(self) -> set[str]: ...
    def get_mode_config(self) -> ModeConfig: ...
```

**File**: `src/oss_navi/models/session.py`

**Storage**: `~/.oss-navi/state/sessions/{session_id}.json`

---

### ReportSection

Represents a section of the interactive report that can be added, deleted, or modified by the user during the session.

```python
class SectionType(str, Enum):
    RECOMMENDATION = "recommendation"
    CODE_ANALYSIS = "code_analysis"
    LEARNING_PATH = "learning_path"
    SUMMARY = "summary"
    CUSTOM = "custom"

class ReportSection(BaseModel):
    section_id: str  # UUID
    section_type: SectionType
    title: str
    content: str  # Markdown content
    order: int
    created_at: datetime
    modified_at: datetime

    def to_markdown(self) -> str: ...
```

**File**: `src/oss_navi/models/session.py`

---

### Recommendation

Represents a single project recommendation with relevance score, reasoning, skill gap analysis, and learning prerequisites.

```python
class Recommendation(BaseModel):
    recommendation_id: str  # UUID
    project_name: str
    project_url: str
    language: str
    relevance_score: int  # 1-10 scale
    reasoning: str  # Why this project matches user
    skill_gap_analysis: list[str]  # Skills user will develop
    learning_prerequisites: list[str]  # Prerequisites if language not matched
    issue_url: str | None = None
    issue_title: str | None = None
    stars: int
    is_great_project: bool = False  # True for "great projects" section
    algorithm_source: str  # Which algorithm generated this
    mode: RecommendationMode  # Which mode generated this
    confidence_score: float | None = None  # Algorithm confidence (0.0-1.0)
    generated_at: datetime

    def to_markdown(self) -> str: ...
```

**File**: `src/oss_navi/models/recommendation.py`

---

### RecommendationPattern

Represents a discovered association between skills, languages, and successful project contributions.

```python
class RecommendationPattern(BaseModel):
    pattern_id: str
    antecedent: list[str]  # e.g., ["python", "web"]
    consequent: list[str]  # e.g., ["django", "fastapi"]
    support: float  # Frequency of pattern
    confidence: float  # P(consequent | antecedent)
    algorithm: str  # "apriori" or "fpgrowth"
    created_at: datetime
```

**File**: `src/oss_navi/models/recommendation.py`

**Storage**: `~/.oss-navi/state/patterns.json`

---

### LearningResource

Represents an external learning resource (course, tutorial, practice problem) from csdiy.wiki, LeetCode, or Codeforces.

```python
class ResourceType(str, Enum):
    COURSE = "course"           # csdiy.wiki course
    PRACTICE_PROBLEM = "practice_problem"  # LeetCode/Codeforces
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"

class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class LearningResource(BaseModel):
    resource_id: str
    resource_type: ResourceType
    title: str
    url: str
    source: str  # "csdiy", "leetcode", "codeforces"
    topics: list[str]  # e.g., ["algorithms", "arrays"]
    difficulty: Difficulty
    description: str | None = None
    metadata: dict = {}  # Source-specific metadata

    def to_markdown(self) -> str: ...
```

**File**: `src/oss_navi/models/learning.py`

---

### Course (extends LearningResource)

Represents a csdiy.wiki course.

```python
class Course(LearningResource):
    resource_type: ResourceType = ResourceType.COURSE
    institution: str | None = None  # e.g., "MIT", "Stanford"
    course_code: str | None = None  # e.g., "6.006"
    prerequisites: list[str] = []
```

**File**: `src/oss_navi/models/learning.py`

---

### PracticeProblem (extends LearningResource)

Represents a LeetCode or Codeforces problem.

```python
class PracticeProblem(LearningResource):
    resource_type: ResourceType = ResourceType.PRACTICE_PROBLEM
    problem_id: str  # LeetCode slug or Codeforces ID
    acceptance_rate: float | None = None
    rating: int | None = None  # Codeforces rating

    def get_leetcode_url(self) -> str: ...
    def get_codeforces_url(self) -> str: ...
```

**File**: `src/oss_navi/models/learning.py`

**Storage**: `~/.oss-navi/cache/leetcode.json`, `~/.oss-navi/cache/codeforces.json`

---

### CodeAnalysis

Represents detailed analysis of a selected repository including architecture overview, key files, contribution areas, and code reading hints.

```python
class KeyFile(BaseModel):
    path: str
    purpose: str
    lines_of_code: int | None = None

class ContributionArea(BaseModel):
    area: str  # e.g., "API endpoints", "Data models"
    difficulty: Difficulty
    good_for_beginners: bool
    suggested_issues: list[str] = []

class CodeAnalysis(BaseModel):
    analysis_id: str
    repository: str  # "owner/repo"
    architecture_overview: str
    key_files: list[KeyFile]
    contribution_areas: list[ContributionArea]
    code_reading_hints: list[str]
    tech_stack: list[str]
    generated_at: datetime

    def to_markdown(self) -> str: ...
```

**File**: `src/oss_navi/models/analysis.py`

---

## Entity Relationships

```
UserPreferences
    ├── LanguageProfile (1:N)
    ├── DomainInterest (1:N)
    └── BlockingRule (1:N)

RecommendationSession
    ├── UserPreferences (1:1)
    ├── RecommendationRound (1:N)
    │   ├── Recommendation (1:N)
    │   └── UserFeedback (1:N)
    └── ReportSection (1:N)

Recommendation
    └── CodeAnalysis (0:1) - if user requests detailed analysis

LearningResource (abstract)
    ├── Course (csdiy.wiki)
    └── PracticeProblem (LeetCode/Codeforces)

RecommendationPattern
    └── Used by recommendation algorithms
```

## Data Volume Estimates

| Entity | Typical Size | Storage |
|--------|--------------|---------|
| UserPreferences | ~2-5 KB | JSON file |
| RecommendationSession | ~10-50 KB per session | JSON file |
| Recommendation | ~1 KB each | Within session |
| LearningResource | ~0.5 KB each | Cached JSON |
| RecommendationPattern | ~0.2 KB each | Cached JSON |
| CodeAnalysis | ~5-10 KB each | Within session |

## Validation Rules

### UserPreferences
- At least one primary language required
- Skill level must match valid enum
- No duplicate blocking rules

### Recommendation
- Relevance score: 1-10
- At least one skill gap or prerequisite
- Valid GitHub URL format

### RecommendationSession
- session_id must be valid UUID
- rounds must be sequential (1, 2, 3, ...)
- status must be valid enum

### LearningResource
- URL must be valid HTTP/HTTPS
- topics must be non-empty list
- difficulty must match valid enum

### CodeAnalysis
- repository must be "owner/repo" format
- key_files must be non-empty
- contribution_areas must be non-empty
