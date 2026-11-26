from datetime import UTC, datetime, timedelta

import pytest

from app.services.retrieval import RetrievedChunk
from app.services.topics import (
    ALERT_THRESHOLD,
    MIN_QUESTIONS_FOR_ALERT,
    OTHER_TOPIC,
    TopicQuestion,
    compute_topics,
    topic_for,
)

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def chunk(title, content, doc="d1"):
    return RetrievedChunk(document_id=doc, title=title, page=1, content=content)


def question(student, topic="Derivadas", score=0.0, text="una pregunta", hours_ago=1):
    return TopicQuestion(
        student_id=student, topic=topic, content=text, score=score,
        asked_at=NOW - timedelta(hours=hours_ago),
    )  # fmt: skip


def stat(stats, topic):
    return next(s for s in stats if s.topic == topic)


class TestTopicFor:
    def test_uses_the_title_of_the_material_that_talks_about_the_question(self):
        chunks = [chunk("Guía de derivadas", "La derivada mide la razón de cambio.")]

        assert topic_for("¿Cómo se calcula la derivada?", chunks) == "Guía de derivadas"

    def test_picks_the_nearest_chunk_that_really_shares_vocabulary(self):
        chunks = [
            chunk("Biología", "La mitocondria produce energía.", "d1"),
            chunk("Cálculo", "Las integrales acumulan área bajo la curva.", "d2"),
        ]

        assert topic_for("¿Qué es una integral y el área?", chunks) == "Cálculo"

    def test_unrelated_material_is_not_a_topic(self):
        chunks = [chunk("Biología", "La mitocondria produce energía.")]

        assert topic_for("¿Cuándo es el examen final?", chunks) == OTHER_TOPIC

    def test_no_material_means_other_topics(self):
        assert topic_for("¿Qué es una derivada?", []) == OTHER_TOPIC

    def test_file_extensions_are_dropped_from_titles(self):
        chunks = [chunk("silabo-calculo.pdf", "La derivada mide el cambio.")]

        assert topic_for("derivada", chunks) == "silabo-calculo"

    def test_singular_and_plural_match(self):
        chunks = [chunk("Derivadas", "Las derivadas parciales se calculan por variable.")]

        assert topic_for("¿Qué es una derivada parcial?", chunks) == "Derivadas"

    def test_accents_and_case_do_not_matter(self):
        chunks = [chunk("Álgebra", "Las FUNCIONES lineales tienen pendiente.")]

        assert topic_for("¿Qué es una función lineal?", chunks) == "Álgebra"


class TestComputeTopics:
    def test_counts_questions_and_distinct_students(self):
        stats = compute_topics(
            [question("s1"), question("s1"), question("s2"), question("s3", topic="Límites")]
        )

        derivatives = stat(stats, "Derivadas")
        assert (derivatives.question_count, derivatives.unique_students) == (3, 2)
        assert stat(stats, "Límites").question_count == 1

    def test_calm_topic_has_zero_confusion_and_no_alert(self):
        stats = compute_topics([question(f"s{i}") for i in range(5)])

        derivatives = stat(stats, "Derivadas")
        assert derivatives.confusion_score == 0.0
        assert derivatives.confusion_alert is False

    def test_frustrated_questions_raise_the_confusion(self):
        calm = compute_topics([question("s1"), question("s2"), question("s3")])
        upset = compute_topics(
            [question("s1", score=0.8), question("s2", score=0.7), question("s3")]
        )

        assert stat(upset, "Derivadas").confusion_score > stat(calm, "Derivadas").confusion_score

    def test_students_coming_back_to_the_same_topic_raise_the_confusion(self):
        once = compute_topics([question("s1"), question("s2"), question("s3")])
        again = compute_topics([question("s1"), question("s1"), question("s2")])

        assert stat(again, "Derivadas").confusion_score > stat(once, "Derivadas").confusion_score

    def test_a_confused_group_triggers_the_alert(self):
        stats = compute_topics(
            [question("s1", score=0.8), question("s1", score=0.7), question("s2", score=0.9)]
        )

        derivatives = stat(stats, "Derivadas")
        assert derivatives.confusion_score >= ALERT_THRESHOLD
        assert derivatives.confusion_alert is True

    def test_too_few_questions_never_raise_an_alert(self):
        """One upset student is not "group confusion"."""
        assert MIN_QUESTIONS_FOR_ALERT >= 3
        stats = compute_topics([question("s1", score=1.0), question("s1", score=1.0)])

        derivatives = stat(stats, "Derivadas")
        assert derivatives.confusion_score >= ALERT_THRESHOLD
        assert derivatives.confusion_alert is False

    def test_questions_without_a_score_count_as_not_frustrated(self):
        stats = compute_topics([question("s1", score=None)] * 3)

        assert stat(stats, "Derivadas").confusion_score <= 0.4

    def test_threshold_boundary_is_inclusive_for_frustration(self):
        stats = compute_topics([question("s1", score=0.5), question("s2"), question("s3")])

        assert stat(stats, "Derivadas").confusion_score > 0

    def test_score_stays_between_0_and_1(self):
        stats = compute_topics([question("s1", score=1.0)] * 10)

        assert 0 <= stat(stats, "Derivadas").confusion_score <= 1

    def test_alerts_come_first_then_by_confusion_then_by_volume(self):
        stats = compute_topics(
            [
                *[question("s1", "Calmo", 0.0)] * 6,
                *[question(f"s{i}", "Confuso", 0.9) for i in range(3)],
                *[question(f"s{i}", "Medio", 0.0) for i in range(2)],
                question("s9", "Medio", 0.8),
            ]
        )

        assert [s.topic for s in stats][0] == "Confuso"
        assert stats[0].confusion_alert is True
        scores = [(s.confusion_alert, s.confusion_score) for s in stats]
        assert scores == sorted(scores, reverse=True)

    def test_sample_questions_prefer_the_frustrated_and_the_most_recent(self):
        stats = compute_topics(
            [
                question("s1", score=0.0, text="vieja y tranquila", hours_ago=50),
                question("s2", score=0.9, text="no entiendo la regla de la cadena", hours_ago=30),
                question("s3", score=0.0, text="reciente y tranquila", hours_ago=1),
                question("s4", score=0.8, text="me rindo con las derivadas", hours_ago=2),
            ]
        )

        samples = stat(stats, "Derivadas").sample_questions
        assert samples[:2] == ["me rindo con las derivadas", "no entiendo la regla de la cadena"]
        assert len(samples) <= 3

    def test_sample_questions_are_deduplicated_and_truncated(self):
        stats = compute_topics(
            [
                question("s1", text="igual"),
                question("s2", text="igual"),
                question("s3", text="x" * 500),
            ]
        )

        samples = stat(stats, "Derivadas").sample_questions
        assert samples.count("igual") == 1
        assert all(len(s) <= 200 for s in samples)

    def test_no_questions_no_topics(self):
        assert compute_topics([]) == []

    @pytest.mark.parametrize("count", [1, 3, 8])
    def test_counts_match_what_goes_in(self, count):
        stats = compute_topics([question(f"s{i}") for i in range(count)])

        assert stat(stats, "Derivadas").question_count == count
