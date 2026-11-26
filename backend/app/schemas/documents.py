from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

MimeType = Literal[
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
]


class DocumentStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class DocumentUploadResponse(BaseModel):
    document_id: str
    course_id: str
    filename: str
    mime_type: MimeType
    status: DocumentStatus


class CourseDocument(BaseModel):
    document_id: str
    course_id: str
    filename: str
    title: str | None = None
    mime_type: MimeType
    size_bytes: int = Field(ge=0)
    status: DocumentStatus
    error_message: str | None = None  # only meaningful when status is `failed`
    created_at: datetime


class DocumentListResponse(BaseModel):
    course_id: str
    documents: list[CourseDocument]
