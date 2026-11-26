"""`LLMClient` that works with no API key: lexical embeddings and a stand-in tutor.

Used when `GEMINI_API_KEY` is empty, so the whole product can be developed and tested offline.
"""

from collections.abc import AsyncIterator, Sequence

from app.core.config import Settings
from app.services.embeddings import HashingEmbedder


class OfflineLLMClient:
    def __init__(self, settings: Settings) -> None:
        self._embedder = HashingEmbedder(settings.embedding_dimensions)

    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
        return self._embedder.embed(list(texts))

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError("The offline tutor arrives with #17.")
        yield  # pragma: no cover  (marks this as an async generator)
