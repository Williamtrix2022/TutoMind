import math

import pytest

from app.services.embeddings import HashingEmbedder


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_vectors_have_the_configured_dimension_and_unit_length():
    vector = HashingEmbedder(64).embed(["derivadas de funciones"])[0]

    assert len(vector) == 64
    assert math.isclose(math.sqrt(sum(x * x for x in vector)), 1.0, rel_tol=1e-9)


def test_embedding_is_deterministic():
    embedder = HashingEmbedder(64)

    assert embedder.embed(["hola mundo"]) == embedder.embed(["hola mundo"])


def test_related_texts_are_closer_than_unrelated_ones():
    embedder = HashingEmbedder(256)
    query, related, unrelated = embedder.embed(
        [
            "cómo se calcula la derivada de una función",
            "la derivada de una función mide su razón de cambio",
            "la mitocondria produce energía en la célula",
        ]
    )

    assert cosine(query, related) > cosine(query, unrelated)


def test_accents_and_case_do_not_matter():
    a, b = HashingEmbedder(128).embed(["Función Límite", "funcion limite"])

    assert cosine(a, b) == pytest.approx(1.0)


def test_empty_text_yields_a_valid_zero_free_vector():
    vector = HashingEmbedder(32).embed([""])[0]

    assert len(vector) == 32 and not any(math.isnan(x) for x in vector)
