"""The Gemini client must survive the free tier: retry what is transient, report the rest."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest

import app.services.llm as llm_module
from app.core.config import Settings
from app.services.llm import GeminiClient, LLMError

SECRET = "secret-api-key-123"


class ApiError(Exception):
    """Shaped like google.genai.errors.APIError: carries the HTTP status in `.code`."""

    def __init__(self, code: int):
        super().__init__(f"{code} error calling the API with key {SECRET}")
        self.code = code


class FlakyModels:
    """Fails the calls listed in `failures` (by call number, from 1), then works."""

    def __init__(self, failures=(), error=None):
        self.failures = set(failures)
        self.error = error or ApiError(503)
        self.embed_calls = 0
        self.stream_calls = 0

    def _maybe_fail(self, call: int) -> None:
        if call in self.failures:
            raise self.error

    async def embed_content(self, *, model, contents, config):
        self.embed_calls += 1
        self._maybe_fail(self.embed_calls)
        values = [3.0, 4.0] + [0.0] * 6
        return SimpleNamespace(embeddings=[SimpleNamespace(values=values) for _ in contents])

    async def generate_content_stream(self, *, model, contents, config):
        self.stream_calls += 1
        self._maybe_fail(self.stream_calls)

        async def chunks():
            for text in ("Ho", "la"):
                yield SimpleNamespace(text=text)

        return chunks()


def make(models: FlakyModels):
    settings = Settings(_env_file=None, embedding_dimensions=8, gemini_api_key=SECRET)
    return GeminiClient(settings, client=SimpleNamespace(aio=SimpleNamespace(models=models)))


@pytest.fixture(autouse=True)
def slept(monkeypatch):
    """Record the waits instead of really waiting."""
    waits: list[float] = []

    async def fake_sleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr(llm_module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(llm_module, "RETRY_DELAYS", (0.5, 1.5))
    return waits


def embed(client, texts=("a",)):
    return asyncio.run(client.embed(list(texts)))


def stream(client):
    async def collect():
        return [piece async for piece in client.generate_stream("hola")]

    return asyncio.run(collect())


class TestEmbeddings:
    def test_a_transient_failure_is_retried_with_backoff(self, slept):
        models = FlakyModels(failures={1, 2})

        vectors = embed(make(models))

        assert len(vectors) == 1
        assert models.embed_calls == 3
        assert slept == [0.5, 1.5]

    def test_it_gives_up_after_three_attempts_and_says_the_service_is_unavailable(self):
        models = FlakyModels(failures={1, 2, 3, 4, 5})

        with pytest.raises(LLMError) as error:
            embed(make(models))

        assert error.value.kind == "unavailable"
        assert models.embed_calls == 3

    def test_the_free_tier_limit_is_recognised(self):
        models = FlakyModels(failures={1, 2, 3}, error=ApiError(429))

        with pytest.raises(LLMError) as error:
            embed(make(models))

        assert error.value.kind == "rate_limit"

    def test_a_request_error_is_not_retried(self, slept):
        models = FlakyModels(failures={1}, error=ApiError(400))

        with pytest.raises(LLMError) as error:
            embed(make(models))

        assert error.value.kind == "other"
        assert models.embed_calls == 1 and slept == []

    def test_unexpected_errors_are_not_retried_either(self):
        models = FlakyModels(failures={1}, error=ValueError("bug"))

        with pytest.raises(LLMError) as error:
            embed(make(models))

        assert error.value.kind == "other" and models.embed_calls == 1

    @pytest.mark.parametrize(
        "network_error",
        [httpx.ConnectError("down"), httpx.ReadTimeout("slow"), TimeoutError(), ConnectionError()],
    )
    def test_network_problems_count_as_transient(self, network_error):
        models = FlakyModels(failures={1}, error=network_error)

        assert len(embed(make(models))) == 1
        assert models.embed_calls == 2

    def test_each_batch_is_retried_on_its_own(self):
        models = FlakyModels(failures={2})  # the second batch fails once

        vectors = embed(make(models), [str(i) for i in range(250)])

        assert len(vectors) == 250
        assert models.embed_calls == 4  # 3 batches + 1 retry

    def test_the_error_never_carries_the_provider_message_or_the_key(self):
        models = FlakyModels(failures={1, 2, 3}, error=ApiError(429))

        with pytest.raises(LLMError) as error:
            embed(make(models))

        assert SECRET not in str(error.value)


class TestGeneration:
    def test_a_failure_before_the_stream_starts_is_retried(self, slept):
        models = FlakyModels(failures={1})

        assert stream(make(models)) == ["Ho", "la"]
        assert models.stream_calls == 2 and slept == [0.5]

    def test_a_failure_before_the_first_token_is_retried(self):
        attempts = {"n": 0}

        class Models(FlakyModels):
            async def generate_content_stream(self, *, model, contents, config):
                attempts["n"] += 1

                async def chunks():
                    if attempts["n"] == 1:
                        raise ApiError(503)
                    yield SimpleNamespace(text="listo")

                return chunks()

        assert stream(make(Models())) == ["listo"]
        assert attempts["n"] == 2

    def test_a_failure_after_the_first_token_is_not_retried(self):
        class Models(FlakyModels):
            async def generate_content_stream(self, *, model, contents, config):
                self.stream_calls += 1

                async def chunks():
                    yield SimpleNamespace(text="Ho")
                    raise ApiError(503)

                return chunks()

        models = Models()
        received = []

        async def collect():
            async for piece in make(models).generate_stream("hola"):
                received.append(piece)

        with pytest.raises(LLMError) as error:
            asyncio.run(collect())

        assert received == ["Ho"]  # what the student already saw is not repeated
        assert models.stream_calls == 1
        assert error.value.kind == "unavailable"

    def test_it_gives_up_after_three_attempts(self):
        models = FlakyModels(failures={1, 2, 3, 4}, error=ApiError(429))

        with pytest.raises(LLMError) as error:
            stream(make(models))

        assert error.value.kind == "rate_limit" and models.stream_calls == 3

    def test_cancelling_a_stream_is_not_swallowed(self):
        """A client that disconnects must stop the work, not trigger a retry."""
        models = FlakyModels()

        async def run():
            generator = make(models).generate_stream("hola")
            await generator.__anext__()
            await generator.aclose()

        asyncio.run(run())

        assert models.stream_calls == 1
