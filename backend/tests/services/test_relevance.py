"""Which retrieved chunks really talk about the question (and which are another subject's)."""

from app.services.retrieval import GENERIC_TERMS, Relevance, RetrievedChunk, select_relevant


def chunk(doc: str, content: str, distance: float | None = None) -> RetrievedChunk:
    return RetrievedChunk(doc, doc, 1, content, distance=distance)


CALCULUS = chunk("calculo", "La integral definida mide el área bajo una curva con la función.", 0.9)
PROGRAMMING = chunk(
    "python", "Una variable en Python se declara asignando un valor con igual.", 0.95
)
CHAIN = chunk("derivadas", "La regla de la cadena deriva funciones compuestas con cadena.", 0.9)
OFFLINE = Relevance(max_distance=0.985, lexical_min_score=0.8)


class TestDistance:
    def test_without_limits_everything_up_to_k_passes(self):
        pool = [chunk(f"d{i}", f"texto {i}", 0.1 * i) for i in range(6)]

        assert select_relevant(pool, "x", Relevance(), k=4) == pool[:4]

    def test_chunks_beyond_the_cap_are_dropped(self):
        near, far = chunk("a", "cerca", 0.3), chunk("b", "lejos", 0.8)

        assert select_relevant([near, far], "x", Relevance(max_distance=0.5)) == [near]

    def test_everything_beyond_the_cap_means_no_material(self):
        assert select_relevant([chunk("a", "lejos", 0.9)], "x", Relevance(max_distance=0.5)) == []

    def test_a_clear_winner_is_not_diluted_with_weaker_matches(self):
        best, close, weak = chunk("a", "1", 0.30), chunk("b", "2", 0.38), chunk("c", "3", 0.55)

        kept = select_relevant([best, close, weak], "x", Relevance(margin=0.12))

        assert kept == [best, close]

    def test_chunks_without_a_distance_are_not_filtered_by_it(self):
        unknown = chunk("a", "sin distancia")

        assert select_relevant([unknown], "x", Relevance(max_distance=0.1, margin=0.1)) == [unknown]


class TestLexical:
    def test_a_programming_question_gets_no_calculus_notes(self):
        question = "¿Cómo declaro una variable en Python?"

        assert select_relevant([CALCULUS], question, OFFLINE) == []

    def test_each_subject_gets_its_own_material(self):
        pool = [CALCULUS, PROGRAMMING, CHAIN]

        assert select_relevant(pool, "¿Cómo declaro una variable en Python?", OFFLINE) == [
            PROGRAMMING
        ]
        assert select_relevant(pool, "área bajo la curva con la integral", OFFLINE) == [CALCULUS]
        assert select_relevant(pool, "¿cuándo uso la regla de la cadena?", OFFLINE) == [CHAIN]

    def test_a_word_every_subject_uses_is_not_evidence(self):
        # "función" appears in calculus and in programming: it must not drag in the wrong notes.
        assert "funcion" in GENERIC_TERMS
        pool = [CALCULUS, PROGRAMMING]

        assert select_relevant(pool, "¿cómo escribo una función en JavaScript?", OFFLINE) == []

    def test_the_best_vocabulary_match_comes_first(self):
        weak = chunk("a", "La integral aparece en muchos temas distintos.", 0.90)
        strong = chunk("b", "La integral definida mide el área bajo una curva.", 0.95)

        kept = select_relevant([weak, strong], "integral definida área", OFFLINE)

        assert kept[0] is strong

    def test_chunks_far_weaker_than_the_best_are_dropped(self):
        strong = chunk("a", "La regla de la cadena para funciones compuestas con cadena.", 0.9)
        weak = chunk("b", "Otra regla distinta del temario general de cálculo.", 0.9)

        assert select_relevant([strong, weak], "regla de la cadena", OFFLINE) == [strong]

    def test_no_shared_vocabulary_means_no_material(self):
        assert select_relevant([CALCULUS], "capital de Francia", OFFLINE) == []

    def test_the_lexical_filter_needs_the_question(self):
        assert select_relevant([CALCULUS], None, OFFLINE) == [CALCULUS]


class TestFeelingsAndSecondaryDocuments:
    BOOK = chunk(
        "libro",
        "Sin duda esto es un libro sencillo de entender, imposible no agradecer a sus autores.",
        0.9,
    )

    def test_a_message_about_how_the_student_feels_gets_no_material(self):
        for message in ("sigo sin entender, esto es imposible, me rindo", "no entiendo nada"):
            assert select_relevant([self.BOOK, CALCULUS], message, OFFLINE) == []

    def test_another_document_matching_one_word_does_not_tag_along(self):
        both = chunk("derivadas", "La regla de la cadena deriva funciones compuestas.", 0.90)
        one_word = chunk("integrales", "Aplicar la regla de la potencia a 1/x da ln|x|.", 0.91)

        kept = select_relevant([both, one_word], "¿cuándo uso la regla de la cadena?", OFFLINE)

        assert kept == [both]

    def test_the_leading_document_still_brings_its_neighbouring_chunk(self):
        # The title «Regla de la cadena» is split across two chunks of the same document.
        explanation = chunk(
            "derivadas", "de la cadena Se usa cuando una función está dentro de otra.", 0.91
        )
        errors = chunk(
            "derivadas", "Olvidar la derivada interior en la regla de la cadena es común.", 0.90
        )

        kept = select_relevant([errors, explanation], "regla de la cadena", OFFLINE)

        assert set(kept) == {errors, explanation}
        assert kept[0] is errors  # the chunk with both words comes first
