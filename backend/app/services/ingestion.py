"""Turns an uploaded document into searchable chunks: extract, chunk, embed, store."""

import logging
from datetime import datetime, timedelta
from functools import partial

import anyio
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.db.session import SessionFactory
from app.services.chunking import chunk_pages
from app.services.extraction import ExtractionError, extract_pages
from app.services.llm import LLMClient, LLMError

logger = logging.getLogger(__name__)

GENERIC_FAILURE = "No se pudo indexar el documento. Inténtalo de nuevo."
RATE_LIMIT_FAILURE = (
    "Se alcanzó el límite de uso del servicio de IA. Vuelve a subir el documento en unos minutos."
)
UNAVAILABLE_FAILURE = "El servicio de IA no respondió. Vuelve a subir el documento en unos minutos."
STALE_MESSAGE = (
    "La indexación se interrumpió (el servidor se reinició). Vuelve a subir el documento."
)

# Indexing runs in memory (the file is not kept), so a restart loses the job for good. Anything
# still "in progress" afterwards would stay so forever; these limits turn it into a clear failure.
STARTUP_GRACE = timedelta(minutes=2)  # a boot only fails jobs older than this (a peer may be live)
STALE_AFTER = timedelta(minutes=10)  # when listing, anything this old cannot still be running


def fail_stale_documents(
    session: Session, now: datetime, older_than: timedelta, course_id: str | None = None
) -> int:
    """Mark documents stuck in `queued`/`processing` for longer than `older_than` as failed."""
    statement = (
        update(Document)
        .where(
            Document.status.in_(("queued", "processing")),
            Document.created_at < now - older_than,
        )
        .values(status="failed", error_message=STALE_MESSAGE)
    )
    if course_id is not None:
        statement = statement.where(Document.course_id == course_id)
    count = session.execute(statement).rowcount
    session.flush()
    return count


def _mark_failed(session: Session, document_id: str, reason: str) -> None:
    document = session.get(Document, document_id)
    if document is not None:
        document.status = "failed"
        document.error_message = reason
        session.commit()


def _failure_message(error: Exception) -> str:
    """What the teacher is told. Never the provider's own text."""
    if isinstance(error, LLMError) and error.kind == "rate_limit":
        return RATE_LIMIT_FAILURE
    if isinstance(error, LLMError) and error.kind == "unavailable":
        return UNAVAILABLE_FAILURE
    return GENERIC_FAILURE


def ingest_document(
    document_id: str,
    data: bytes,
    mime_type: str,
    llm: LLMClient,
    session_factory: SessionFactory,
) -> None:
    """Runs after the upload response. Never raises: a failure becomes `status = failed`."""
    with session_factory() as session:
        document = session.get(Document, document_id)
        if document is None:
            return
        course_id = document.course_id
        document.status = "processing"
        session.commit()

        try:
            chunks = chunk_pages(extract_pages(data, mime_type))
            # This runs in a worker thread; `llm.embed` is async, so hop back to the event loop.
            vectors = anyio.from_thread.run(partial(llm.embed, [c.content for c in chunks]))
            session.add_all(
                DocumentChunk(
                    document_id=document_id,
                    course_id=course_id,
                    chunk_index=chunk.index,
                    page=chunk.page,
                    content=chunk.content,
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, vectors, strict=True)
            )
            document.status = "indexed"
            document.error_message = None
            session.commit()
        except ExtractionError as error:
            session.rollback()
            _mark_failed(session, document_id, str(error))
        except Exception as error:
            # Internal details go to the log, never to the teacher.
            logger.exception("Indexing failed for document %s", document_id)
            session.rollback()
            _mark_failed(session, document_id, _failure_message(error))
