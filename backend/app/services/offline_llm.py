"""`LLMClient` that works with no API key: lexical embeddings and a stand-in Socratic tutor.

Used when `GEMINI_API_KEY` is empty, so the whole product can be developed and tested offline.
The stand-in does not reason: it guides with questions about what the student asked and quotes
the course material it was given.
"""

import html
import re
from collections.abc import AsyncIterator, Sequence

from app.core.config import Settings
from app.services.embeddings import HashingEmbedder
from app.services.tutor_prompt import EMPATHY_MARKER, QUESTION_MARKER, SOLUTION_GUARD_MARKER

_FIRST_SOURCE = re.compile(r"<fuente[^>]*>\n(.*?)\n</fuente>", re.DOTALL)
_SNIPPET_CHARS = 220


class OfflineLLMClient:
    def __init__(self, settings: Settings) -> None:
        self._embedder = HashingEmbedder(settings.embedding_dimensions)

    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
        return self._embedder.embed(list(texts))

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        system = system or ""
        question = prompt.split(QUESTION_MARKER, 1)[-1].strip()

        parts = []
        if EMPATHY_MARKER in system:
            parts.append("Entiendo que puede ser frustrante; vamos con calma.")
        if SOLUTION_GUARD_MARKER in system:
            parts.append("No te daré la solución completa, pero sí te guío para que la encuentres.")
        parts.append(f"Vamos paso a paso con tu pregunta: «{question}».")
        source = _FIRST_SOURCE.search(system)
        if source:
            snippet = html.unescape(source.group(1))[:_SNIPPET_CHARS]
            parts.append(f"En el material del curso aparece: «{snippet}».")
        parts.append(
            "Para guiarte mejor: ¿qué sabes ya sobre este tema? "
            "¿Cuál sería el primer paso que intentarías?"
        )

        for piece in re.split(r"(\s+)", "\n\n".join(parts)):
            if piece:
                yield piece
