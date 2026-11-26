"""Business rules the contract states that a model must enforce when validating real data."""

import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas import (
    ChatMessage,
    CourseDocument,
    DocumentUploadResponse,
    EscalationSignal,
    FrustrationSignal,
    LoginRequest,
    LoginResponse,
    SourceCitation,
    StudentRisk,
    TopicStat,
    TutorChatRequest,
    TutorStreamEvent,
    XaiFactor,
)

PDF = "application/pdf"
NOW = "2026-11-25T10:00:00Z"
EVENT = TypeAdapter(TutorStreamEvent)


def factor(**overrides):
    base = {
        "key": "days_since_last_login",
        "label": "Días sin ingresar",
        "impact": 0.4,
        "value": 12,
        "explanation": "No ingresa hace 12 días.",
    }
    return {**base, **overrides}


def student_risk(**overrides):
    base = {
        "student_id": "s1",
        "name": "Ana",
        "risk_level": "red",
        "risk_score": 0.8,
        "projected_grade": 2.1,
        "factors": [factor()],
        "updated_at": NOW,
    }
    return {**base, **overrides}


def document(**overrides):
    base = {
        "document_id": "d1",
        "course_id": "c1",
        "filename": "a.pdf",
        "mime_type": PDF,
        "size_bytes": 10,
        "status": "queued",
        "created_at": NOW,
    }
    return {**base, **overrides}


class TestLogin:
    def test_valid_request(self):
        request = LoginRequest(email="ana@uni.edu", password="12345678")

        assert request.role is None

    @pytest.mark.parametrize("password", ["", "1234567"])
    def test_password_shorter_than_8_is_rejected(self, password):
        with pytest.raises(ValidationError):
            LoginRequest(email="ana@uni.edu", password=password)

    def test_invalid_email_is_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="12345678")

    def test_unknown_role_is_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="ana@uni.edu", password="12345678", role="admin")

    def test_token_type_must_be_bearer(self):
        user = {"id": "u1", "name": "Ana", "email": "ana@uni.edu", "role": "student"}
        with pytest.raises(ValidationError):
            LoginResponse(access_token="t", token_type="basic", expires_in=3600, user=user)


class TestDocuments:
    def test_mime_outside_the_allowed_three_is_rejected(self):
        with pytest.raises(ValidationError):
            DocumentUploadResponse(
                document_id="d1",
                course_id="c1",
                filename="a.txt",
                mime_type="text/plain",
                status="queued",
            )

    def test_negative_size_is_rejected(self):
        with pytest.raises(ValidationError):
            CourseDocument(**document(size_bytes=-1))

    def test_optional_fields_default_to_none(self):
        parsed = CourseDocument(**document(status="failed"))

        assert parsed.title is None and parsed.error_message is None


class TestTutor:
    def test_request_needs_at_least_one_message(self):
        with pytest.raises(ValidationError):
            TutorChatRequest(course_id="c1", messages=[], student_level="basic")

    def test_human_help_defaults_to_false(self):
        request = TutorChatRequest(
            course_id="c1",
            student_level="basic",
            messages=[ChatMessage(role="user", content="hola")],
        )

        assert request.request_human_help is False and request.conversation_id is None

    @pytest.mark.parametrize("score", [-0.1, 1.1])
    def test_frustration_score_is_bounded(self, score):
        with pytest.raises(ValidationError):
            FrustrationSignal(detected=True, score=score)

    def test_escalation_reason_must_be_known(self):
        with pytest.raises(ValidationError):
            EscalationSignal(suggested=True, reason="because")

    def test_citation_url_must_be_a_uri(self):
        with pytest.raises(ValidationError):
            SourceCitation(document_id="d1", title="T", moodle_url="not a url")


class TestStreamEvents:
    def test_discriminator_picks_the_right_variant(self):
        event = EVENT.validate_python({"type": "token", "content": "Hola"})

        assert event.type == "token" and event.content == "Hola"

    def test_done_event_requires_conversation_id(self):
        with pytest.raises(ValidationError):
            EVENT.validate_python({"type": "done"})

    def test_unknown_event_type_is_rejected(self):
        with pytest.raises(ValidationError):
            EVENT.validate_python({"type": "banana"})

    def test_nested_signals_are_validated(self):
        with pytest.raises(ValidationError):
            EVENT.validate_python(
                {"type": "frustration", "frustration": {"detected": True, "score": 9}}
            )

    def test_event_serializes_without_unset_optionals(self):
        event = EVENT.validate_python(
            {
                "type": "escalation",
                "escalation": {"suggested": True, "reason": "student_requested"},
            }
        )

        dumped = event.model_dump(mode="json", exclude_none=True)

        assert dumped == {
            "type": "escalation",
            "escalation": {"suggested": True, "reason": "student_requested"},
        }


class TestAnalytics:
    def test_risk_always_carries_xai_factors(self):
        """Project rule: every risk level is returned with structured XAI factors."""
        with pytest.raises(ValidationError):
            StudentRisk(**student_risk(factors=[]))

    def test_factor_value_accepts_number_or_text(self):
        assert XaiFactor(**factor(value=3.5)).value == 3.5
        assert XaiFactor(**factor(value="alta")).value == "alta"

    @pytest.mark.parametrize("impact", [-1.01, 1.01])
    def test_factor_impact_is_bounded(self, impact):
        with pytest.raises(ValidationError):
            XaiFactor(**factor(impact=impact))

    def test_unknown_risk_level_is_rejected(self):
        with pytest.raises(ValidationError):
            StudentRisk(**student_risk(risk_level="orange"))

    def test_grade_scale_defaults_to_5(self):
        assert StudentRisk(**student_risk()).grade_scale_max == 5

    def test_topic_counts_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            TopicStat(topic="t", question_count=-1, confusion_score=0.1, confusion_alert=False)
