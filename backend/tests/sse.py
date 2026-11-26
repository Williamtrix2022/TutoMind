"""Helpers for the tutor tests: parse the SSE body and a spy LLM that records what it is sent."""

import json
from collections.abc import AsyncIterator, Sequence

from app.services.embeddings import HashingEmbedder


def parse_sse(body: str) -> list[dict]:
    """Every event must be framed exactly as `data: {json}` + blank line."""
    events = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        assert block.startswith("data: "), f"bad SSE frame: {block!r}"
        events.append(json.loads(block[len("data: ") :]))
    return events


class SpyLLM:
    """Records the prompts it receives and streams fixed tokens (optionally failing mid-way)."""

    def __init__(self, tokens: Sequence[str] = ("Hola ", "mundo"), fail_at: int | None = None):
        self.tokens = list(tokens)
        self.fail_at = fail_at
        self.calls: list[tuple[str, str | None]] = []
        self._embedder = HashingEmbedder(1024)

    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
        return self._embedder.embed(list(texts))

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        self.calls.append((prompt, system))
        for index, token in enumerate(self.tokens):
            if self.fail_at == index:
                raise RuntimeError("secret provider failure")
            yield token
