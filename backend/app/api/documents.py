from datetime import UTC, datetime
from pathlib import PurePosixPath

from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.errors import ApiError
from app.db.models import Course, Document, Enrollment, User
from app.db.session import SessionFactory, get_session, get_session_factory
from app.schemas import CourseDocument, DocumentListResponse, DocumentUploadResponse, ErrorResponse
from app.schemas.documents import DOCX_MIME, PDF_MIME, PPTX_MIME
from app.services.ingestion import ingest_document
from app.services.llm import LLMClient, get_llm_client

router = APIRouter(prefix="/api/v1/courses", tags=["documents"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB, same limit as the frontend

# mime -> (extension, magic bytes, label)
_TYPES = {
    PDF_MIME: (".pdf", b"%PDF-", "PDF"),
    DOCX_MIME: (".docx", b"PK", "DOCX"),
    PPTX_MIME: (".pptx", b"PK", "PPTX"),
}

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}


def _course_for_teacher(course_id: str, user: User, session: Session) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise ApiError(404, "not_found", "El curso no existe.")
    if session.get(Enrollment, (course_id, user.id)) is None:
        raise ApiError(403, "forbidden", "No tienes permiso sobre este curso.")
    return course


def _to_contract(row: Document) -> CourseDocument:
    return CourseDocument(
        document_id=row.id,
        course_id=row.course_id,
        filename=row.filename,
        title=row.title,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        status=row.status,
        error_message=row.error_message,
        created_at=row.created_at,
    )


def _resolve_mime(filename: str, content_type: str | None) -> str | None:
    """By MIME type, or by extension when the browser sends a generic or empty one."""
    if content_type in _TYPES:
        return content_type
    suffix = PurePosixPath(filename).suffix.lower()
    return next((mime for mime, (ext, _, _) in _TYPES.items() if ext == suffix), None)


def _safe_filename(raw: str | None) -> str:
    # Keep only the final path component (browsers may send "C:\\dir\\file.pdf" or "../x").
    name = PurePosixPath((raw or "").replace("\\", "/")).name.strip()
    if not name:
        raise ApiError(422, "invalid_request", "El archivo no tiene nombre.")
    return name[:255]


@router.post(
    "/{course_id}/documents",
    operation_id="uploadCourseDocument",
    summary="Subir documento del curso (PDF, DOCX, PPTX) para indexación RAG",
    status_code=202,
    response_model=DocumentUploadResponse,
    responses={**_ERRORS, 413: {"model": ErrorResponse}, 415: {"model": ErrorResponse},
               422: {"model": ErrorResponse}},
)  # fmt: skip
def upload_document(
    course_id: str,
    file: UploadFile,
    background: BackgroundTasks,
    title: str | None = Form(None, max_length=200),
    user: User = Depends(require_role("teacher")),
    session: Session = Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
    session_factory: SessionFactory = Depends(get_session_factory),
) -> DocumentUploadResponse:
    _course_for_teacher(course_id, user, session)

    filename = _safe_filename(file.filename)
    mime = _resolve_mime(filename, file.content_type)
    if mime is None:
        raise ApiError(415, "unsupported_media_type", "Solo se admiten archivos PDF, DOCX y PPTX.")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ApiError(413, "file_too_large", "El archivo supera el máximo de 20 MB.")
    if not data:
        raise ApiError(422, "invalid_request", "El archivo está vacío.")
    _, magic, label = _TYPES[mime]
    if not data.startswith(magic):
        raise ApiError(415, "unsupported_media_type", f"El contenido no es un {label} válido.")

    document = Document(
        course_id=course_id,
        filename=filename,
        title=title or None,
        mime_type=mime,
        size_bytes=len(data),
        status="queued",
        created_at=datetime.now(UTC),  # app clock: stays ordered even inside one transaction
    )
    session.add(document)
    session.commit()

    background.add_task(ingest_document, document.id, data, mime, llm, session_factory)
    return DocumentUploadResponse(
        document_id=document.id,
        course_id=course_id,
        filename=filename,
        mime_type=mime,
        status="queued",
    )


@router.get(
    "/{course_id}/documents",
    operation_id="listCourseDocuments",
    summary="Listar los documentos del curso y su estado de indexación",
    response_model=DocumentListResponse,
    responses={**_ERRORS, 422: {"model": ErrorResponse}},
)
def list_documents(
    course_id: str,
    user: User = Depends(require_role("teacher")),
    session: Session = Depends(get_session),
) -> DocumentListResponse:
    _course_for_teacher(course_id, user, session)
    rows = session.scalars(
        select(Document).where(Document.course_id == course_id).order_by(Document.created_at.desc())
    ).all()
    return DocumentListResponse(
        course_id=course_id,
        documents=[_to_contract(row) for row in rows],
    )
