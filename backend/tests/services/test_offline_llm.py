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


def material(*chunks: RetrievedChunk, solution=False, empathetic=False) -> str:
    return build_system_prompt("basic", list(chunks), empathetic, solution)


GUIDE = RetrievedChunk(
    "d1",
    "Guía de cálculo.pdf",
    2,
    "La derivada mide la razón de cambio instantánea de una función. "
    "Geométricamente es la pendiente de la recta tangente a la gráfica. "
    "Ejemplo. Para f(x) = x², la derivada es f'(x) = 2x. "
    "Entonces en x = 3 la pendiente vale 6.",
)


def test_offline_tutor_presents_the_material_cleanly_and_streams_it():
    client = OfflineLLMClient(settings())

    chunks = asyncio.run(collect(client, question("¿Qué es una derivada?"), material(GUIDE)))

    text = "".join(chunks)
    assert len(chunks) > 3  # streamed, not one block
    assert "### 📘 Lo esencial de «Guía de cálculo»" in text  # friendly heading, no ".pdf"
    assert "- La derivada mide la razón de cambio instantánea de una función." in text
    assert "**Ejemplo del material**" in text
    assert "> Ejemplo. Para f(x) = x²" in text
    assert "*Fuente: Guía de cálculo, página 2.*" in text
    assert text.rstrip().endswith(
        "¿Te queda claro este ejemplo o quieres que revisemos otra parte?"
    )


def test_offline_tutor_no_longer_uses_the_robotic_template():
    client = OfflineLLMClient(settings())

    text = "".join(asyncio.run(collect(client, question("¿Qué es una derivada?"), material(GUIDE))))

    assert "Vamos paso a paso" not in text
    assert "¿qué sabes ya sobre este tema?" not in text
    assert "¿Qué es una derivada?" not in text  # it does not echo the student's message back


def test_offline_tutor_says_so_when_the_course_has_nothing_on_the_subject():
    client = OfflineLLMClient(settings())

    text = "".join(asyncio.run(collect(client, question("¿Qué es un bucle for?"), material())))

    assert "no encontré nada sobre esto" in text
    assert "Vamos paso a paso" not in text
    assert "Lo esencial de" not in text


def test_offline_tutor_asks_what_part_is_hard_instead_of_searching_when_frustrated():
    client = OfflineLLMClient(settings())

    text = "".join(
        asyncio.run(collect(client, question("no entiendo nada"), material(empathetic=True)))
    )

    assert "Te entiendo" in text
    assert "qué parte exacta se te complica" in text
    assert "no encontré nada" not in text


def test_offline_tutor_varies_its_opening_by_question_but_is_deterministic():
    client = OfflineLLMClient(settings())

    def opening(q):
        return "".join(asyncio.run(collect(client, question(q), material()))).split(" Revisé")[0]

    assert opening("pregunta uno") == opening("pregunta uno")
    assert len({opening(f"pregunta {i}") for i in range(12)}) > 1


def test_offline_tutor_picks_the_sentences_that_answer_the_question():
    client = OfflineLLMClient(settings())
    notes = RetrievedChunk(
        "d1", "Apuntes", 1,
        "La integral definida mide el área bajo una curva en un intervalo. "
        "Una antiderivada se obtiene al invertir el proceso de derivación. "
        "El teorema fundamental conecta la derivada con la integral definida.",
    )  # fmt: skip

    text = "".join(asyncio.run(collect(client, question("área bajo la curva"), material(notes))))

    assert "- La integral definida mide el área bajo una curva en un intervalo." in text


def test_offline_tutor_drops_section_titles_stuck_to_a_sentence_and_cut_fragments():
    client = OfflineLLMClient(settings())
    messy = RetrievedChunk(
        "d1", "Notas", 1,
        "de la cadena Se usa cuando algo. Regla de la cadena Se usa cuando una función está "
        "dentro de otra función compuesta. Se deriva la función de afuera sin tocar la de",
    )  # fmt: skip

    text = "".join(asyncio.run(collect(client, question("regla de la cadena"), material(messy))))

    assert "- Se usa cuando una función está dentro de otra función compuesta." in text
    assert "Regla de la cadena Se usa" not in text  # the stuck title is gone
    assert "sin tocar la de\n" not in text  # the sentence cut mid-way is not shown


def test_offline_tutor_groups_chunks_of_the_same_document_under_one_heading():
    client = OfflineLLMClient(settings())
    first = RetrievedChunk(
        "d1", "Guía.pdf", 1, "El límite describe hacia dónde tiende una función."
    )
    second = RetrievedChunk(
        "d1", "Guía.pdf", 3, "Los límites laterales deben coincidir para existir."
    )

    text = "".join(asyncio.run(collect(client, question("límites"), material(second, first))))

    assert text.count("Lo esencial de «Guía»") == 1
    assert "*Fuente: Guía, páginas 1 y 3.*" in text


def test_offline_tutor_shows_at_most_two_documents():
    client = OfflineLLMClient(settings())
    chunks = [
        RetrievedChunk(
            f"d{i}", f"Documento {i}", 1, f"El tema número {i} se explica aquí con detalle."
        )
        for i in range(4)
    ]

    text = "".join(asyncio.run(collect(client, question("tema"), material(*chunks))))

    assert text.count("### 📘") == 2


def test_offline_tutor_quotes_the_course_material_when_there_is_some():
    client = OfflineLLMClient(settings())
    chunk = RetrievedChunk("d1", "Guía", 2, "La derivada mide la razón de cambio.")
    system = build_system_prompt("basic", [chunk], False, False)

    text = "".join(asyncio.run(collect(client, question("derivada"), system)))

    assert "La derivada mide la razón de cambio." in text


def test_offline_tutor_is_gentler_when_the_tone_must_adapt():
    client = OfflineLLMClient(settings())

    plain = "".join(asyncio.run(collect(client, question("hola"), material(GUIDE))))
    soft = "".join(asyncio.run(collect(client, question("hola"), material(GUIDE, empathetic=True))))

    assert "Te entiendo" in soft and "Te entiendo" not in plain


def test_offline_tutor_explains_instead_of_doing_the_work_when_asked_to():
    client = OfflineLLMClient(settings())

    text = "".join(
        asyncio.run(collect(client, question("hazme la tarea"), material(GUIDE, solution=True)))
    )

    assert "Te explico el concepto y un ejemplo" in text
    assert "No te daré la solución completa" not in text


def test_offline_relevance_relies_on_shared_rare_vocabulary_not_on_distance():
    relevance = OfflineLLMClient(settings()).relevance

    assert relevance.lexical_min_score is not None
    assert relevance.max_distance is not None and relevance.max_distance < 1.0


def test_gemini_relevance_comes_from_the_settings():
    client = GeminiClient(
        Settings(_env_file=None, retrieval_max_distance=0.5, retrieval_margin=0.1),
        client=object(),
    )

    assert (client.relevance.max_distance, client.relevance.margin) == (0.5, 0.1)
    assert client.relevance.lexical_min_score is None
