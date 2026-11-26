import asyncio

import pytest

from app.core.config import Settings
from app.services.llm import GeminiClient, get_llm_client
from app.services.offline_llm import OfflineLLMClient


def test_without_a_key_the_factory_returns_the_offline_client():
    client = get_llm_client(Settings(_env_file=None, gemini_api_key=""))

    assert isinstance(client, OfflineLLMClient)


def test_with_a_key_the_factory_returns_gemini():
    client = get_llm_client(Settings(_env_file=None, gemini_api_key="fake-key-for-test"))

    assert isinstance(client, GeminiClient)


def test_offline_embeddings_have_the_configured_dimension_and_are_deterministic():
    client = OfflineLLMClient(Settings(_env_file=None))

    first = asyncio.run(client.embed(["derivadas", "integrales"]))
    second = asyncio.run(client.embed(["derivadas", "integrales"], is_query=True))

    assert first == second
    assert [len(v) for v in first] == [1024, 1024]


def test_offline_tutor_is_not_available_until_17():
    client = OfflineLLMClient(Settings(_env_file=None))

    async def consume():
        return [chunk async for chunk in client.generate_stream("hola")]

    with pytest.raises(NotImplementedError):
        asyncio.run(consume())
