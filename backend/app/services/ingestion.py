"""Turns an uploaded document into searchable chunks: extract, chunk, embed, store."""

import logging
from functools import partial

import anyio
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.db.session import SessionFactory
from app.services.chunking import chunk_pages
from app.services.extraction import ExtractionError, extract_pages
from app.services.llm import LLMClient

logger = logging.getLogger(__name__)

GENERIC_FAILURE = "No se pudo indexar el documento. Inténtalo de nuevo."


def _mark_failed(session: Session, document_id: str, reason: str) -> None:
    document = session.get(Document, document_id)
    if document is not None:
        document.status = "failed"
        document.error_message = reason
        session.commit()


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
        except Exception:
            # Internal details go to the log, never to the teacher.
            logger.exception("Indexing failed for document %s", document_id)
            session.rollback()
            _mark_failed(session, document_id, GENERIC_FAILURE)
