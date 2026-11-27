import pytest

from app.schemas import ChatMessage
from app.services.frustration import (
    DETECTION_THRESHOLD,
    assess,
    message_score,
    says_still_lost,
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


class TestRepeatedFailure:
    """The teacher is offered when the student still does not understand after 2 explanations."""

    def test_still_lost_after_two_explanations_offers_the_teacher(self):
        messages = [
            user("¿cómo derivo una función compuesta?"),
            tutor(),
            user("sigue sin quedarme claro"),
            tutor(),
            user("todavía no lo entiendo"),
        ]

        result = assess(messages, request_human_help=False)

        assert result.escalation_reason == "repeated_failure"

    def test_not_after_a_single_explanation(self):
        messages = [user("¿cómo derivo?"), tutor(), user("sigo sin entender")]

        assert assess(messages, request_human_help=False).escalation_reason is None

    def test_a_calm_follow_up_after_two_explanations_does_not_offer_it(self):
        messages = [
            user("¿qué es un límite?"),
            tutor(),
            user("ok, ¿y un ejemplo?"),
            tutor(),
            user("gracias"),
        ]

        assert assess(messages, request_human_help=False).escalation_reason is None

    @pytest.mark.parametrize(
        "text",
        [
            "sigo sin entender",
            "Sigo sin comprender esto",
            "aún no lo entiendo",
            "todavia no me queda claro",
            "no me queda claro",
            "sigo confundida",
            "sigo perdido",
        ],
    )
    def test_the_ways_of_saying_it_still_did_not_land(self, text):
        assert says_still_lost(text)

    @pytest.mark.parametrize(
        "text", ["¿qué es una derivada?", "ya entendí, gracias", "no entendí el paso 2"]
    )
    def test_ordinary_messages_are_not_flagged(self, text):
        assert not says_still_lost(text)

    def test_persistent_frustration_keeps_its_own_reason(self):
        messages = [
            user("no entiendo"),
            tutor(),
            user("sigo sin entender, esto es imposible"),
            tutor(),
            user("me rindo, no puedo más"),
        ]

        assert (
            assess(messages, request_human_help=False).escalation_reason == "persistent_frustration"
        )

    def test_asking_outright_still_wins(self):
        messages = [user("a"), tutor(), user("b"), tutor(), user("sigo sin entender")]

        assert assess(messages, request_human_help=True).escalation_reason == "student_requested"
