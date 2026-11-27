"""Cliente de IA del MVP (Google Gemini, nivel gratuito).

Los endpoints dependen solo de `LLMClient`; cambiar de proveedor significa escribir otra
implementación, no tocar #16 (ingesta) ni #17 (chat).
"""

import math
from collections.abc import AsyncIterator, Sequence
from typing import Any, Protocol

from fastapi import Depends
from google import genai
from google.genai import types

from app.core.config import Settings, get_settings
from app.services.retrieval import Relevance

# Gemini permite elegir la dimensión; con menos de 3072 hay que normalizar el vector.
_EMBED_BATCH = 100


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
            response = await self._client.aio.models.embed_content(
                model=self._settings.embedding_model,
                contents=list(texts[start : start + _EMBED_BATCH]),
                config=config,
            )
            vectors.extend(normalize(e.values) for e in response.embeddings)
        return vectors

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        stream = await self._client.aio.models.generate_content_stream(
            model=self._settings.llm_model, contents=prompt, config=config
        )
        async for chunk in stream:
            if chunk.text:
                yield chunk.text


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Gemini when `GEMINI_API_KEY` is set; otherwise the offline client (dev and tests)."""
    if settings.gemini_api_key:
        return GeminiClient(settings)
    from app.services.offline_llm import OfflineLLMClient

    return OfflineLLMClient(settings)
