from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    green = "green"
    yellow = "yellow"
    red = "red"


class XaiFactor(BaseModel):
    key: str
    label: str
    impact: float = Field(ge=-1, le=1)  # positive = increases the risk
    value: float | str  # observed value
    explanation: str  # natural-language explanation for the teacher


class StudentRisk(BaseModel):
    student_id: str
    name: str
    risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=1)
    projected_grade: float
    grade_scale_max: float = 5
    # Project rule: every risk level ships with explicit XAI factors.
    factors: list[XaiFactor] = Field(min_length=1)
    updated_at: datetime


class RiskSummary(BaseModel):
    green: int = Field(ge=0)
    yellow: int = Field(ge=0)
    red: int = Field(ge=0)


class CourseRiskResponse(BaseModel):
    course_id: str
    summary: RiskSummary
    students: list[StudentRisk]


class TopicStat(BaseModel):
    topic: str
    question_count: int = Field(ge=0)
    unique_students: int | None = Field(default=None, ge=0)
    confusion_score: float = Field(ge=0, le=1)
    confusion_alert: bool
    sample_questions: list[str] | None = None


class CourseTopicsResponse(BaseModel):
    course_id: str
    period_start: datetime
    period_end: datetime
    topics: list[TopicStat]
