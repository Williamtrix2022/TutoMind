from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AnyUrl, BaseModel, Field


class StudentLevel(StrEnum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str  # Markdown with LaTeX and code


class TutorChatRequest(BaseModel):
    course_id: str
    conversation_id: str | None = None  # omit to start a new conversation
    student_level: StudentLevel
    messages: list[ChatMessage] = Field(min_length=1)
    request_human_help: bool = False


class SourceCitation(BaseModel):
    document_id: str
    title: str
    page: int | None = None
    moodle_url: AnyUrl | None = None


class FrustrationSignal(BaseModel):
    detected: bool
    score: float = Field(ge=0, le=1)
    adapted_tone: bool | None = None


class EscalationSignal(BaseModel):
    suggested: bool
    reason: Literal["student_requested", "persistent_frustration", "repeated_failure"]
    ticket_id: str | None = None


class TokenEvent(BaseModel):
    type: Literal["token"]
    content: str


class SourcesEvent(BaseModel):
    type: Literal["sources"]
    sources: list[SourceCitation]


class FrustrationEvent(BaseModel):
    type: Literal["frustration"]
    frustration: FrustrationSignal


class EscalationEvent(BaseModel):
    type: Literal["escalation"]
    escalation: EscalationSignal


class DoneEvent(BaseModel):
    type: Literal["done"]
    conversation_id: str


class ErrorEvent(BaseModel):
    type: Literal["error"]
    code: str
    message: str


# SSE event discriminated by `type`.
TutorStreamEvent = Annotated[
    TokenEvent | SourcesEvent | FrustrationEvent | EscalationEvent | DoneEvent | ErrorEvent,
    Field(discriminator="type"),
]
