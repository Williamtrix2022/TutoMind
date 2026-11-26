"""Pydantic models, one per schema in `docs/openapi.json` (the single source of truth)."""

from typing import Any

from app.schemas.analytics import (
    CourseRiskResponse,
    CourseTopicsResponse,
    RiskLevel,
    RiskSummary,
    StudentRisk,
    TopicStat,
    XaiFactor,
)
from app.schemas.auth import LoginRequest, LoginResponse, User
from app.schemas.common import ErrorResponse, Role
from app.schemas.documents import (
    CourseDocument,
    DocumentListResponse,
    DocumentStatus,
    DocumentUploadResponse,
)
from app.schemas.tutor import (
    ChatMessage,
    DoneEvent,
    ErrorEvent,
    EscalationEvent,
    EscalationSignal,
    FrustrationEvent,
    FrustrationSignal,
    SourceCitation,
    SourcesEvent,
    StudentLevel,
    TokenEvent,
    TutorChatRequest,
    TutorStreamEvent,
)

# Contract schema name -> Python type. A test keeps this in sync with the contract.
CONTRACT_TYPES: dict[str, Any] = {
    "ErrorResponse": ErrorResponse,
    "Role": Role,
    "User": User,
    "LoginRequest": LoginRequest,
    "LoginResponse": LoginResponse,
    "DocumentStatus": DocumentStatus,
    "DocumentUploadResponse": DocumentUploadResponse,
    "CourseDocument": CourseDocument,
    "DocumentListResponse": DocumentListResponse,
    "StudentLevel": StudentLevel,
    "ChatMessage": ChatMessage,
    "TutorChatRequest": TutorChatRequest,
    "SourceCitation": SourceCitation,
    "FrustrationSignal": FrustrationSignal,
    "EscalationSignal": EscalationSignal,
    "TutorStreamEvent": TutorStreamEvent,
    "RiskLevel": RiskLevel,
    "XaiFactor": XaiFactor,
    "StudentRisk": StudentRisk,
    "CourseRiskResponse": CourseRiskResponse,
    "TopicStat": TopicStat,
    "CourseTopicsResponse": CourseTopicsResponse,
}

__all__ = [
    "CONTRACT_TYPES",
    "ChatMessage",
    "CourseDocument",
    "CourseRiskResponse",
    "CourseTopicsResponse",
    "DocumentListResponse",
    "DocumentStatus",
    "DocumentUploadResponse",
    "DoneEvent",
    "ErrorEvent",
    "ErrorResponse",
    "EscalationEvent",
    "EscalationSignal",
    "FrustrationEvent",
    "FrustrationSignal",
    "LoginRequest",
    "LoginResponse",
    "RiskLevel",
    "RiskSummary",
    "Role",
    "SourceCitation",
    "SourcesEvent",
    "StudentLevel",
    "StudentRisk",
    "TokenEvent",
    "TopicStat",
    "TutorChatRequest",
    "TutorStreamEvent",
    "User",
    "XaiFactor",
]
