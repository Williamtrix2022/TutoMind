import pytest

from app.db.models import Course, Document, DocumentChunk
from app.services.embeddings import HashingEmbedder
from app.services.retrieval import retrieve_chunks

EMBEDDER = HashingEmbedder(1024)
PDF = "application/pdf"


@pytest.fixture
def material(session):
    session.add_all([Course(id="c1", name="Cálculo"), Course(id="c2", name="Otro")])
    session.flush()

    def add(doc_id, course, title, filename, texts, status="indexed"):
        session.add(
            Document(
                id=doc_id, course_id=course, filename=filename, title=title,
                mime_type=PDF, size_bytes=10, status=status,
            )
        )  # fmt: skip
        session.flush()
        for index, text in enumerate(texts):
            session.add(
                DocumentChunk(
                    document_id=doc_id, course_id=course, chunk_index=index, page=index + 1,
                    content=text, embedding=EMBEDDER.embed([text])[0],
                )
            )  # fmt: skip
        session.flush()

    add(
        "d1",
        "c1",
        "Guía de cálculo",
        "guia.pdf",
        ["la derivada mide el cambio", "la integral suma área"],
    )
    add("d2", "c1", None, "sin-titulo.pdf", ["los límites describen aproximaciones"])
    add("d3", "c2", "Biología", "bio.pdf", ["la derivada no aparece pero la mitocondria sí"])
    return add


def query(text):
    return EMBEDDER.embed([text])[0]


def test_nearest_chunks_come_first(session, material):
    found = retrieve_chunks(session, "c1", query("derivada y cambio"), k=3)

    assert found[0].content == "la derivada mide el cambio"
    assert found[0].page == 1


def test_only_the_requested_course_is_searched(session, material):
    found = retrieve_chunks(session, "c1", query("mitocondria"), k=10)

    assert all(c.document_id != "d3" for c in found)


def test_limit_is_respected(session, material):
    assert len(retrieve_chunks(session, "c1", query("derivada"), k=1)) == 1


def test_title_falls_back_to_the_filename(session, material):
    found = retrieve_chunks(session, "c1", query("límites aproximaciones"), k=1)

    assert found[0].title == "sin-titulo.pdf"


def test_chunks_of_documents_that_are_not_indexed_are_ignored(session, material):
    material("d4", "c1", "Fallido", "x.pdf", ["la derivada exacta"], status="failed")

    found = retrieve_chunks(session, "c1", query("la derivada exacta"), k=10)

    assert all(c.document_id != "d4" for c in found)


def test_course_without_material_returns_nothing(session, material):
    session.add(Course(id="c3", name="Vacío"))
    session.flush()

    assert retrieve_chunks(session, "c3", query("derivada"), k=4) == []
