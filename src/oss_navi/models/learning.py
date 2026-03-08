"""Learning resource models for csdiy.wiki, LeetCode, and Codeforces."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field

from oss_navi.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    pass


class ResourceType(str, Enum):
    """Type of learning resource."""

    COURSE = "course"  # csdiy.wiki course
    PRACTICE_PROBLEM = "practice_problem"  # LeetCode/Codeforces
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"


class Difficulty(str, Enum):
    """Difficulty level for learning resources."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningResource(BaseModel):
    """Base model for external learning resources."""

    resource_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique resource identifier"
    )
    resource_type: ResourceType = Field(..., description="Type of resource")
    title: str = Field(..., description="Resource title")
    url: str = Field(..., description="Resource URL")
    source: str = Field(..., description="Source: csdiy, leetcode, codeforces")
    topics: list[str] = Field(..., description="Topics covered")
    difficulty: Difficulty = Field(..., description="Difficulty level")
    description: str | None = Field(None, description="Brief description")
    metadata: dict = Field(default_factory=dict, description="Source-specific metadata")

    def to_markdown(self) -> str:
        """Convert resource to markdown format."""
        lines = [
            f"**{self.title}** ({self.source})",
            f"- Type: {self.resource_type.value}",
            f"- Difficulty: {self.difficulty.value}",
            f"- Topics: {', '.join(self.topics)}",
            f"- URL: [{self.url}]({self.url})",
        ]
        if self.description:
            lines.insert(1, self.description)
        return "\n".join(lines)


class Course(LearningResource):
    """A csdiy.wiki course."""

    resource_type: ResourceType = ResourceType.COURSE
    institution: str | None = Field(None, description="Institution offering the course")
    course_code: str | None = Field(None, description="Course code, e.g., '6.006'")
    prerequisites: list[str] = Field(default_factory=list, description="Prerequisites")

    def to_markdown(self) -> str:
        """Convert course to markdown format."""
        lines = [
            f"### {self.title}",
        ]
        if self.institution:
            lines.append(f"**Institution**: {self.institution}")
        if self.course_code:
            lines.append(f"**Course Code**: {self.course_code}")
        lines.extend([
            f"**Difficulty**: {self.difficulty.value}",
            f"**Topics**: {', '.join(self.topics)}",
            f"**URL**: [{self.url}]({self.url})",
        ])
        if self.prerequisites:
            lines.append(f"**Prerequisites**: {', '.join(self.prerequisites)}")
        if self.description:
            lines.append(f"\n{self.description}")
        return "\n".join(lines)


class PracticeProblem(LearningResource):
    """A LeetCode or Codeforces practice problem."""

    resource_type: ResourceType = ResourceType.PRACTICE_PROBLEM
    problem_id: str = Field(..., description="LeetCode slug or Codeforces ID")
    acceptance_rate: float | None = Field(None, description="Acceptance rate (0.0-1.0)")
    rating: int | None = Field(None, description="Codeforces rating")

    def get_leetcode_url(self) -> str:
        """Get LeetCode URL for this problem."""
        if self.source == "leetcode":
            return f"https://leetcode.com/problems/{self.problem_id}/"
        return self.url

    def get_codeforces_url(self) -> str:
        """Get Codeforces URL for this problem."""
        if self.source == "codeforces":
            return f"https://codeforces.com/problemset/problem/{self.problem_id}"
        return self.url

    def to_markdown(self) -> str:
        """Convert problem to markdown format."""
        lines = [
            f"**{self.title}** ({self.source})",
            f"- Difficulty: {self.difficulty.value}",
            f"- Topics: {', '.join(self.topics)}",
        ]
        if self.acceptance_rate is not None:
            lines.append(f"- Acceptance Rate: {self.acceptance_rate:.1%}")
        if self.rating is not None:
            lines.append(f"- Rating: {self.rating}")
        lines.append(f"- URL: [{self.url}]({self.url})")
        return "\n".join(lines)


class LearningPath(BaseModel):
    """A curated learning path combining courses and problems."""

    path_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(..., description="Learning path title")
    description: str = Field(..., description="Path description")
    target_skills: list[str] = Field(..., description="Skills this path develops")
    resources: list[LearningResource] = Field(default_factory=list)
    estimated_hours: int | None = Field(None, description="Estimated completion time")
    created_at: datetime = Field(default_factory=utc_now)

    def to_markdown(self) -> str:
        """Convert learning path to markdown."""
        lines = [
            f"# Learning Path: {self.title}",
            "",
            self.description,
            "",
            f"**Target Skills**: {', '.join(self.target_skills)}",
        ]
        if self.estimated_hours:
            lines.append(f"**Estimated Time**: {self.estimated_hours} hours")
        lines.append("")

        # Group resources by type
        courses = [r for r in self.resources if isinstance(r, Course)]
        problems = [r for r in self.resources if isinstance(r, PracticeProblem)]

        if courses:
            lines.append("## Courses\n")
            for course in courses:
                lines.append(course.to_markdown())
                lines.append("")

        if problems:
            lines.append("## Practice Problems\n")
            for problem in problems:
                lines.append(f"- {problem.to_markdown()}")

        return "\n".join(lines)
