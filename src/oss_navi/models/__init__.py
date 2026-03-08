"""Pydantic models for OSS-Navi."""

from oss_navi.models.config import Config, Filters
from oss_navi.models.learning import (
    Course,
    Difficulty,
    LearningPath,
    LearningResource,
    PracticeProblem,
    ResourceType,
)
from oss_navi.models.memory import LongTermMemory, PastRecommendation, SkillSnapshot
from oss_navi.models.preferences import (
    BlockingRule,
    BlockType,
    DomainInterest,
    LanguageProfile,
    LanguageType,
    SkillLevel,
    UserPreferences,
)
from oss_navi.models.recommendation import (
    ModeConfig,
    Recommendation,
    RecommendationMode,
    RecommendationPattern,
    check_mode_availability,
    get_mode_config,
)
from oss_navi.models.report import AnalysisReport
from oss_navi.models.session import (
    FeedbackType,
    RecommendationRound,
    RecommendationSession,
    ReportSection,
    SectionType,
    SessionStatus,
    UserFeedback,
)
from oss_navi.models.task import Repository, Task
from oss_navi.models.user_profile import Activity, Language, UserProfile

__all__ = [
    "Config",
    "Filters",
    "UserProfile",
    "Activity",
    "Language",
    "Task",
    "Repository",
    "AnalysisReport",
    "LongTermMemory",
    "SkillSnapshot",
    "PastRecommendation",
    # Preferences
    "SkillLevel",
    "LanguageType",
    "LanguageProfile",
    "BlockType",
    "BlockingRule",
    "DomainInterest",
    "UserPreferences",
    # Recommendation
    "RecommendationMode",
    "ModeConfig",
    "Recommendation",
    "RecommendationPattern",
    "get_mode_config",
    "check_mode_availability",
    # Session
    "FeedbackType",
    "UserFeedback",
    "RecommendationRound",
    "RecommendationSession",
    "ReportSection",
    "SectionType",
    "SessionStatus",
    # Learning
    "ResourceType",
    "Difficulty",
    "LearningResource",
    "Course",
    "PracticeProblem",
    "LearningPath",
]
