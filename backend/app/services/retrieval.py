"""Vector search over a course's indexed material, keeping only what is really about the question.

The nearest chunks are always *some* chunks, even when the course has nothing on the subject (a
Python question would get calculus notes). `Relevance` says how close a chunk must be to count:

- `max_distance`: absolute cap on the cosine distance (meaningful for semantic embeddings).
- `margin`: also drop chunks farther than the best one plus this margin, so a clear winner is not
  diluted with weaker matches from other subjects.
- `lexical_min_score`: for the offline hashing embedder, whose distances barely separate topics,
  require shared *rare* vocabulary. A word counts more the fewer candidate chunks contain it, so
  "función" (everywhere) says little and "integrales" or "cadena" say a lot.
"""

import math
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.services.lexical import vocabulary

DEFAULT_TOP_K = 4
POOL_FACTOR = 3  # candidates fetched per chunk finally returned, before the relevance filter
_MIN_POOL_FOR_IDF = 10  # with a tiny course every word looks rare: do not over-trust the counts
_LEXICAL_KEEP_RATIO = 0.6  # keep chunks scoring at least this fraction of the best one
# Words that appear in every subject ("una función en JavaScript", "una función lineal"): sharing
# one says nothing about the topic, so they never count as evidence for the lexical filter.
GENERIC_TERMS = frozenset(
    "funcion ejemplo ejercicio problema metodo valor concepto tema forma caso resultado "
    "explica explicame ayuda ayudame repasar escribe escribir escribo hace hacer usar usa uso "
    "sirve cuando".split()
)


@dataclass(frozen=True)
class Relevance:
    max_distance: float | None = None
    margin: float | None = None
    lexical_min_score: float | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    title: str
    page: int | None
    content: str
    moodle_url: str | None = None
    distance: float | None = None  # cosine distance to the question (0 = identical)


def _lexical_scores(question: str, pool: list[RetrievedChunk]) -> list[float]:
    """Sum of the rarity of each question word that the chunk also contains."""
    asked = vocabulary(question) - GENERIC_TERMS
    vocabularies = [vocabulary(chunk.content) for chunk in pool]
    size = max(len(pool), _MIN_POOL_FOR_IDF)

    def rarity(term: str) -> float:
        containing = sum(term in words for words in vocabularies)
        return math.log((size + 1) / (containing + 0.5))

    return [sum(rarity(term) for term in asked & words) for words in vocabularies]


def select_relevant(
    pool: list[RetrievedChunk],
    question: str | None,
    relevance: Relevance,
    k: int = DEFAULT_TOP_K,
) -> list[RetrievedChunk]:
    """The chunks of `pool` (nearest first) that are really about `question`, at most `k`."""
    kept = list(pool)

    if relevance.max_distance is not None:
        kept = [c for c in kept if c.distance is None or c.distance <= relevance.max_distance]

    if relevance.margin is not None:
        distances = [c.distance for c in kept if c.distance is not None]
        if distances:
            limit = min(distances) + relevance.margin
            kept = [c for c in kept if c.distance is None or c.distance <= limit]

    if relevance.lexical_min_score is not None and question is not None and kept:
        scores = dict(zip(map(id, pool), _lexical_scores(question, pool), strict=True))
        best = max(scores[id(c)] for c in kept)
        floor = max(relevance.lexical_min_score, best * _LEXICAL_KEEP_RATIO)
        kept = [c for c in kept if scores[id(c)] >= floor]
        # Best vocabulary match first; ties keep the vector order (nearest first).
        kept.sort(key=lambda c: -scores[id(c)])

    return kept[:k]


def retrieve_chunks(
    session: Session,
    course_id: str,
    query_vector: list[float],
    k: int = DEFAULT_TOP_K,
    course_url: str | None = None,
    question: str | None = None,
    relevance: Relevance | None = None,
) -> list[RetrievedChunk]:
    """Up to `k` chunks of this course that are close to the query *and* relevant, nearest first.

    Only the given course is searched and only documents that finished indexing count. Each chunk
    carries its document's Moodle link, or `course_url` (the course page) when it has none.
    """
    relevance = relevance or Relevance()
    distance = DocumentChunk.embedding.cosine_distance(query_vector)
    rows = session.execute(
        select(DocumentChunk, Document, distance.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.course_id == course_id, Document.status == "indexed")
        .order_by(distance)
        .limit(k * POOL_FACTOR)
    ).all()
    pool = [
        RetrievedChunk(
            document_id=document.id,
            title=document.title or document.filename,
            page=chunk.page,
            content=chunk.content,
            moodle_url=document.moodle_url or course_url,
            distance=float(dist),
        )
        for chunk, document, dist in rows
    ]
    return select_relevant(pool, question, relevance, k)
