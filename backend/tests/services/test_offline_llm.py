import asyncio

from app.core.config import Settings
from app.services.llm import GeminiClient, get_llm_client
from app.services.offline_llm import OfflineLLMClient
from app.services.retrieval import RetrievedChunk
from app.services.tutor_prompt import QUESTION_MARKER, build_system_prompt


def settings() -> Settings:
    return Settings(_env_file=None)


def question(text: str) -> str:
    return f"{QUESTION_MARKER}\n{text}"


async def collect(client, prompt, system=None):
    return [chunk async for chunk in client.generate_stream(prompt, system=system)]


def test_without_a_key_the_factory_returns_the_offline_client():
    client = get_llm_client(Settings(_env_file=None, gemini_api_key=""))

    assert isinstance(client, OfflineLLMClient)


def test_with_a_key_the_factory_returns_gemini():
    client = get_llm_client(Settings(_env_file=None, gemini_api_key="fake-key-for-test"))

    assert isinstance(client, GeminiClient)


def test_offline_embeddings_have_the_configured_dimension_and_are_deterministic():
    client = OfflineLLMClient(settings())

    first = asyncio.run(client.embed(["derivadas", "integrales"]))
    second = asyncio.run(client.embed(["derivadas", "integrales"], is_query=True))

    assert first == second
    assert [len(v) for v in first] == [1024, 1024]


def test_offline_tutor_streams_a_socratic_reply_about_the_question():
    client = OfflineLLMClient(settings())

    chunks = asyncio.run(collect(client, question("¿Qué es una derivada?")))

    text = "".join(chunks)
    assert len(chunks) > 3  # streamed, not one block
    assert "¿Qué es una derivada?" in text
    assert text.count("?") >= 2  # it guides with questions instead of answering outright


def test_offline_tutor_quotes_the_course_material_when_there_is_some():
    client = OfflineLLMClient(settings())
    chunk = RetrievedChunk("d1", "Guía", 2, "La derivada mide la razón de cambio.")
    system = build_system_prompt("basic", [chunk], False, False)

    text = "".join(asyncio.run(collect(client, question("derivada"), system)))

    assert "La derivada mide la razón de cambio." in text


def test_offline_tutor_is_gentler_when_the_tone_must_adapt():
    client = OfflineLLMClient(settings())
    calm = build_system_prompt("basic", [], False, False)
    gentle = build_system_prompt("basic", [], True, False)

    plain = "".join(asyncio.run(collect(client, question("hola"), calm)))
    soft = "".join(asyncio.run(collect(client, question("hola"), gentle)))

    assert "frustrante" in soft and "frustrante" not in plain


def test_offline_tutor_declines_to_give_the_solution_when_asked_to_do_the_work():
    client = OfflineLLMClient(settings())
    guarded = build_system_prompt("basic", [], False, True)

    text = "".join(asyncio.run(collect(client, question("hazme la tarea"), guarded)))

    assert "No te daré la solución completa" in text
