"""Cliente de IA del MVP (Google Gemini, nivel gratuito).

Los endpoints dependen solo de `LLMClient`; cambiar de proveedor significa escribir otra
implementación, no tocar #16 (ingesta) ni #17 (chat).
"""

import asyncio
import logging
import math
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Any, Literal, Protocol

import httpx
from fastapi import Depends
from google import genai
from google.genai import types

from app.core.config import Settings, get_settings
from app.services.retrieval import Relevance

logger = logging.getLogger(__name__)

# Gemini permite elegir la dimensión; con menos de 3072 hay que normalizar el vector.
_EMBED_BATCH = 100

# Seconds to wait before each retry: three attempts in total. The free tier throttles and has
# short outages; a couple of quick retries hides most of them from the student.
RETRY_DELAYS: tuple[float, ...] = (1.0, 2.0)
_TRANSIENT_CODES = {500, 502, 503, 504}

FailureKind = Literal["rate_limit", "unavailable", "other"]


class LLMError(Exception):
    """The AI provider failed. `kind` says how, so callers can tell the user what to do.

    It deliberately carries none of the provider's own message: that can include request details
    or the API key. The original error is chained (`__cause__`) for the logs.
    """

    def __init__(self, kind: FailureKind) -> None:
        super().__init__(f"AI provider failure: {kind}")
        self.kind: FailureKind = kind


def _classify(error: Exception) -> FailureKind:
    code = getattr(error, "code", None)  # google.genai APIError carries the HTTP status
    if code == 429:
        return "rate_limit"
    if code in _TRANSIENT_CODES or isinstance(
        error, httpx.TransportError | TimeoutError | ConnectionError
    ):
        return "unavailable"
    return "other"  # a bad request or a bug: retrying would just repeat it


async def _retrying[T](call: Callable[[], Awaitable[T]]) -> T:
    attempts = len(RETRY_DELAYS) + 1
    for attempt in range(attempts):
        try:
            return await call()
        except Exception as error:
            kind = _classify(error)
            if kind == "other" or attempt == attempts - 1:
                logger.warning("AI provider call failed (%s): %s", kind, type(error).__name__)
                raise LLMError(kind) from error
            await asyncio.sleep(RETRY_DELAYS[attempt])
    raise AssertionError("unreachable")  # pragma: no cover


class LLMClient(Protocol):
    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]: ...

    def generate_stream(self, prompt: str, *, system: str | None = None) -> AsyncIterator[str]: ...


def normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm else list(vector)


class GeminiClient:
    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        if client is None:
            if not self._settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY no está configurada (ver backend/.env.example).")
            client = genai.Client(api_key=self._settings.gemini_api_key)
        self._client = client

    @property
    def relevance(self) -> Relevance:
        """Cuándo un fragmento cuenta como «sobre la pregunta» con embeddings semánticos."""
        return Relevance(
            max_distance=self._settings.retrieval_max_distance,
            margin=self._settings.retrieval_margin,
        )

    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
        """Un vector normalizado de `embedding_dimensions` por texto."""
        config = types.EmbedContentConfig(
            output_dimensionality=self._settings.embedding_dimensions,
            task_type="RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT",
        )
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _EMBED_BATCH):
            batch = list(texts[start : start + _EMBED_BATCH])
            response = await _retrying(
                lambda batch=batch: self._client.aio.models.embed_content(
                    model=self._settings.embedding_model, contents=batch, config=config
                )
            )
            vectors.extend(normalize(e.values) for e in response.embeddings)
        return vectors

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        attempts = len(RETRY_DELAYS) + 1
        started = False
        for attempt in range(attempts):
            try:
                stream = await self._client.aio.models.generate_content_stream(
                    model=self._settings.llm_model, contents=prompt, config=config
                )
                async for chunk in stream:
                    if chunk.text:
                        started = True
                        yield chunk.text
                return
            except Exception as error:
                kind = _classify(error)
                # After the first token the student has seen text: retrying would repeat it.
                if started or kind == "other" or attempt == attempts - 1:
                    logger.warning("AI generation failed (%s): %s", kind, type(error).__name__)
                    raise LLMError(kind) from error
                await asyncio.sleep(RETRY_DELAYS[attempt])


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Gemini when `GEMINI_API_KEY` is set; otherwise the offline client (dev and tests)."""
    if settings.gemini_api_key:
        return GeminiClient(settings)
    from app.services.offline_llm import OfflineLLMClient

    return OfflineLLMClient(settings)
