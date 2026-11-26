import pytest

from app.schemas import ChatMessage
from app.services.frustration import (
    DETECTION_THRESHOLD,
    assess,
    message_score,
)


def user(text: str) -> ChatMessage:
    return ChatMessage(role="user", content=text)


def tutor(text: str = "Veamos paso a paso.") -> ChatMessage:
    return ChatMessage(role="assistant", content=text)


class TestScore:
    @pytest.mark.parametrize(
        "text",
        [
            "¿Cómo se calcula la derivada de x^2?",
            "Entiendo perfecto, gracias. ¿Y la integral?",
            "Explícame el teorema del valor medio",
            "",
        ],
    )
    def test_neutral_messages_score_low(self, text):
        assert message_score(text) < DETECTION_THRESHOLD

    @pytest.mark.parametrize(
        "text",
        [
            "no entiendo",
            "No entendí nada de esto",
            "ya no puedo más",
            "estoy frustrado con este tema",
            "esto es imposible",
        ],
    )
    def test_frustrated_messages_are_detected(self, text):
        assert message_score(text) >= DETECTION_THRESHOLD

    def test_giving_up_scores_higher_than_a_plain_doubt(self):
        assert message_score("me rindo, no puedo más") > message_score("no entiendo")

    def test_accents_do_not_matter(self):
        assert message_score("no entendí") == pytest.approx(message_score("no entendi"))

    def test_uppercase_is_still_detected(self):
        assert message_score("NO ENTENDI") >= DETECTION_THRESHOLD

    def test_shouting_and_exclamations_raise_the_score(self):
        assert message_score("NO ENTIENDO NADA!!!") > message_score("no entiendo nada")

    def test_score_is_always_between_0_and_1(self):
        extreme = "me rindo odio esto estoy harto frustrado imposible no puedo no entiendo!!!"

        assert 0.0 <= message_score(extreme) <= 1.0

    def test_code_and_math_do_not_trigger_it(self):
        assert message_score("def f(x): return x**2  # $f'(x)=2x$") < DETECTION_THRESHOLD


class TestAssess:
    def test_calm_conversation_has_no_signal_and_no_escalation(self):
        result = assess([user("¿Qué es una derivada?")], request_human_help=False)

        assert result.frustration.detected is False
        assert result.frustration.adapted_tone is False
        assert result.escalation_reason is None

    def test_a_single_frustrated_message_adapts_the_tone_but_does_not_escalate(self):
        result = assess([user("no entiendo")], request_human_help=False)

        assert result.frustration.detected is True
        assert result.frustration.adapted_tone is True
        assert result.frustration.score >= DETECTION_THRESHOLD
        assert result.escalation_reason is None

    def test_explicit_request_for_a_human_escalates(self):
        result = assess([user("¿Qué es un límite?")], request_human_help=True)

        assert result.escalation_reason == "student_requested"

    def test_explicit_request_wins_over_frustration(self):
        result = assess([user("me rindo")], request_human_help=True)

        assert result.escalation_reason == "student_requested"

    def test_persistent_frustration_escalates(self):
        messages = [
            user("no entiendo"),
            tutor(),
            user("sigo sin entender, esto es imposible"),
            tutor(),
            user("me rindo, no puedo más"),
        ]

        result = assess(messages, request_human_help=False)

        assert result.escalation_reason == "persistent_frustration"

    def test_two_frustrated_messages_among_the_last_three_are_enough(self):
        messages = [
            user("no entiendo"),
            tutor(),
            user("¿y si lo hago así?"),
            tutor(),
            user("no puedo"),
        ]

        assert (
            assess(messages, request_human_help=False).escalation_reason == "persistent_frustration"
        )

    def test_old_frustration_followed_by_calm_does_not_escalate(self):
        messages = [
            user("no entiendo"),
            tutor(),
            user("me rindo"),
            tutor(),
            user("ah, ya entendí, gracias"),
            tutor(),
            user("¿Y qué sigue?"),
            tutor(),
            user("perfecto"),
        ]

        result = assess(messages, request_human_help=False)

        assert result.escalation_reason is None
        assert result.frustration.detected is False

    def test_only_the_students_own_words_count(self):
        messages = [
            user("¿Qué es esto?"),
            tutor("Si no entiendes, me rindo con gusto, es imposible"),
            user("ok"),
        ]

        assert assess(messages, request_human_help=False).frustration.detected is False

    def test_no_messages_is_calm(self):
        result = assess([], request_human_help=False)

        assert result.frustration.score == 0.0 and result.escalation_reason is None
