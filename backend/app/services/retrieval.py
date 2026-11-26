"""Vector search over a course's indexed material."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk

DEFAULT_TOP_K = 4


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    title: str
    page: int | None
    content: str
    moodle_url: str | None = None


def retrieve_chunks(
    session: Session,
    course_id: str,
    query_vector: list[float],
    k: int = DEFAULT_TOP_K,
    course_url: str | None = None,
) -> list[RetrievedChunk]:
    """The `k` chunks of this course closest to the query (cosine distance), nearest first.

    Only the given course is searched and only documents that finished indexing count. Each chunk
    carries its document's Moodle link, or `course_url` (the course page) when it has none.
    """
    rows = session.execute(
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.course_id == course_id, Document.status == "indexed")
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(k)
    ).all()
    return [
        RetrievedChunk(
            document_id=document.id,
            title=document.title or document.filename,
            page=chunk.page,
            content=chunk.content,
            moodle_url=document.moodle_url or course_url,
        )
        for chunk, document in rows
    ]
