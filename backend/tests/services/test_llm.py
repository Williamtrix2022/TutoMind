import asyncio
import math
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.llm import GeminiClient, normalize


class FakeModels:
    def __init__(self, dim: int):
        self.dim = dim
        self.calls: list[dict] = []

    async def embed_content(self, *, model, contents, config):
        self.calls.append({"model": model, "n": len(contents), "task": config.task_type})
        values = [3.0, 4.0] + [0.0] * (self.dim - 2)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=values) for _ in contents])

    async def generate_content_stream(self, *, model, contents, config):
        async def gen():
            for text in ["Hola", None, " mundo"]:
                yield SimpleNamespace(text=text)

        return gen()


def make(dim=8):
    models = FakeModels(dim)
    settings = Settings(_env_file=None, embedding_dimensions=dim, gemini_api_key="k")
    client = GeminiClient(settings, client=SimpleNamespace(aio=SimpleNamespace(models=models)))
    return client, models


def test_normalize_gives_unit_length():
    assert math.isclose(math.sqrt(sum(x * x for x in normalize([3.0, 4.0]))), 1.0)


def test_normalize_keeps_a_zero_vector():
    assert normalize([0.0, 0.0]) == [0.0, 0.0]


def test_embed_returns_one_unit_vector_per_text():
    client, models = make()
    vectors = asyncio.run(client.embed(["a", "b"]))
    assert len(vectors) == 2 and len(vectors[0]) == 8
    assert math.isclose(sum(x * x for x in vectors[0]), 1.0)
    assert models.calls[0]["task"] == "RETRIEVAL_DOCUMENT"


def test_embed_query_uses_the_query_task():
    client, models = make()
    asyncio.run(client.embed(["pregunta"], is_query=True))
    assert models.calls[0]["task"] == "RETRIEVAL_QUERY"


def test_embed_splits_large_inputs_into_batches():
    client, models = make()
    vectors = asyncio.run(client.embed([str(i) for i in range(250)]))
    assert len(vectors) == 250
    assert [c["n"] for c in models.calls] == [100, 100, 50]


def test_stream_skips_empty_chunks():
    client, _ = make()

    async def collect():
        return [t async for t in client.generate_stream("hola", system="s")]

    assert asyncio.run(collect()) == ["Hola", " mundo"]


def test_missing_key_fails_with_a_clear_message():
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        GeminiClient(Settings(_env_file=None, gemini_api_key=""))
