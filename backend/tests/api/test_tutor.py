import pytest
from pydantic import TypeAdapter
from sqlalchemy import select

from app.db.models import Conversation, Course, Document, DocumentChunk, Message, SupportTicket
from app.schemas import TutorStreamEvent
from app.services.embeddings import HashingEmbedder
from app.services.llm import get_llm_client
from app.services.tutor_prompt import (
    EMPATHY_MARKER,
    LEVEL_GUIDANCE,
    SOLUTION_GUARD_MARKER,
)
from tests.sse import SpyLLM, parse_sse

URL = "/api/v1/tutor/chat/stream"
EVENT = TypeAdapter(TutorStreamEvent)
EMBEDDER = HashingEmbedder(1024)


@pytest.fixture
def student(make_user):
    return make_user("s1", role="student")


@pytest.fixture
def spy(api):
    llm = SpyLLM()
    api.app.dependency_overrides[get_llm_client] = lambda: llm
    return llm


def add_material(session, course_id, doc_id, title, text, page=1):
    if session.get(Course, course_id) is None:
        session.add(Course(id=course_id, name=course_id))
        session.flush()
    session.add(
        Document(
            id=doc_id, course_id=course_id, filename=f"{doc_id}.pdf", title=title,
            mime_type="application/pdf", size_bytes=10, status="indexed",
        )
    )  # fmt: skip
    session.flush()
    session.add(
        DocumentChunk(
            document_id=doc_id, course_id=course_id, chunk_index=0, page=page,
            content=text, embedding=EMBEDDER.embed([text])[0],
        )
    )  # fmt: skip
    session.flush()


def chat(api, user, auth, text="¿Qué es una derivada?", history=None, **extra):
    messages = [*(history or []), {"role": "user", "content": text}]
    body = {"course_id": "c1", "student_level": "basic", "messages": messages, **extra}
    return api.post(URL, json=body, headers=auth(user))


def user_msg(text):
    return {"role": "user", "content": text}


def tutor_msg(text="Veamos."):
    return {"role": "assistant", "content": text}


def types(events):
    return [e["type"] for e in events]


class TestStreaming:
    def test_streams_tokens_then_done_in_sse_format(self, api, student, auth, spy):
        response = chat(api, student, auth)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-cache"
        events = parse_sse(response.text)
        assert types(events) == ["token", "token", "done"]
        assert "".join(e["content"] for e in events if e["type"] == "token") == "Hola mundo"

    def test_every_event_matches_the_contract(self, api, student, auth, spy):
        for event in parse_sse(chat(api, student, auth).text):
            EVENT.validate_python(event)

    def test_markdown_latex_and_code_pass_through_untouched(self, api, student, auth, spy):
        spy.tokens = ["$$x^2$$ ", "```py\n", "print(1)\n", "```"]

        events = parse_sse(chat(api, student, auth).text)

        text = "".join(e["content"] for e in events if e["type"] == "token")
        assert text == "$$x^2$$ ```py\nprint(1)\n```"

    def test_a_new_conversation_is_created_and_both_messages_are_stored(
        self, api, session, student, auth, spy
    ):
        events = parse_sse(chat(api, student, auth, text="¿Qué es un límite?").text)

        conversation_id = events[-1]["conversation_id"]
        conversation = session.get(Conversation, conversation_id)
        assert (conversation.course_id, conversation.student_id) == ("c1", "s1")
        stored = session.scalars(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
        ).all()
        assert [(m.role, m.content) for m in stored] == [
            ("user", "¿Qué es un límite?"),
            ("assistant", "Hola mundo"),
        ]

    def test_an_existing_conversation_is_continued(self, api, session, student, auth, spy):
        first = parse_sse(chat(api, student, auth).text)[-1]["conversation_id"]

        second = parse_sse(chat(api, student, auth, conversation_id=first).text)[-1]

        assert second["conversation_id"] == first
        count = session.scalars(select(Message).where(Message.conversation_id == first)).all()
        assert len(count) == 4


class TestRetrieval:
    def test_sources_come_from_the_course_material_and_are_cited(
        self, api, session, student, auth, spy
    ):
        add_material(session, "c1", "d1", "Guía de cálculo", "la derivada mide el cambio", page=7)
        add_material(session, "c2", "d9", "Biología", "la derivada de la mitocondria")

        events = parse_sse(chat(api, student, auth, text="derivada y cambio").text)

        sources = next(e for e in events if e["type"] == "sources")["sources"]
        assert [(s["document_id"], s["title"], s["page"]) for s in sources] == [
            ("d1", "Guía de cálculo", 7)
        ]
        assert types(events)[-1] == "done"
        assert events.index(sources and next(e for e in events if e["type"] == "sources")) > 0

    def test_the_retrieved_material_reaches_the_model_but_other_courses_do_not(
        self, api, session, student, auth, spy
    ):
        add_material(session, "c1", "d1", "Guía", "la derivada mide el cambio")
        add_material(session, "c2", "d9", "Biología", "la derivada de la mitocondria")

        chat(api, student, auth, text="derivada y cambio")

        _, system = spy.calls[0]
        assert "la derivada mide el cambio" in system
        assert "mitocondria" not in system

    def test_without_material_there_is_no_sources_event(self, api, student, auth, spy):
        events = parse_sse(chat(api, student, auth).text)

        assert "sources" not in types(events)
        assert "No hay material del curso relevante" in spy.calls[0][1]


class TestPedagogy:
    @pytest.mark.parametrize("level", ["basic", "intermediate", "advanced"])
    def test_depth_follows_the_student_level(self, api, student, auth, spy, level):
        chat(api, student, auth, student_level=level)

        assert LEVEL_GUIDANCE[level] in spy.calls[0][1]

    def test_the_question_and_recent_history_reach_the_model(self, api, student, auth, spy):
        chat(
            api, student, auth, text="¿y si x es negativo?",
            history=[user_msg("¿Qué es el valor absoluto?"), tutor_msg("¿Qué crees?")],
        )  # fmt: skip

        prompt, _ = spy.calls[0]
        assert "¿Qué es el valor absoluto?" in prompt
        assert prompt.rstrip().endswith("¿y si x es negativo?")

    def test_asking_for_the_full_solution_activates_the_guard(self, api, student, auth, spy):
        chat(api, student, auth, text="dame la solución completa de mi tarea")

        assert SOLUTION_GUARD_MARKER in spy.calls[0][1]

    def test_a_normal_question_does_not(self, api, student, auth, spy):
        chat(api, student, auth, text="¿Cómo se resuelve una ecuación cuadrática?")

        assert SOLUTION_GUARD_MARKER not in spy.calls[0][1]


class TestFrustration:
    def test_a_frustrated_message_emits_the_signal_first_and_softens_the_tone(
        self, api, student, auth, spy
    ):
        events = parse_sse(chat(api, student, auth, text="no entiendo").text)

        assert events[0]["type"] == "frustration"
        assert events[0]["frustration"]["detected"] is True
        assert events[0]["frustration"]["adapted_tone"] is True
        assert EMPATHY_MARKER in spy.calls[0][1]
        assert "escalation" not in types(events)

    def test_a_calm_message_emits_no_signal(self, api, student, auth, spy):
        events = parse_sse(chat(api, student, auth).text)

        assert "frustration" not in types(events)
        assert EMPATHY_MARKER not in spy.calls[0][1]

    def test_persistent_frustration_escalates_and_opens_a_ticket(
        self, api, session, student, auth, spy
    ):
        history = [user_msg("no entiendo"), tutor_msg(), user_msg("sigo sin entender")]

        events = parse_sse(chat(api, student, auth, text="me rindo", history=history).text)

        escalation = next(e for e in events if e["type"] == "escalation")["escalation"]
        assert escalation["suggested"] is True
        assert escalation["reason"] == "persistent_frustration"
        ticket = session.get(SupportTicket, escalation["ticket_id"])
        assert (ticket.status, ticket.reason, ticket.student_id) == (
            "open", "persistent_frustration", "s1",
        )  # fmt: skip
        assert types(events)[-1] == "done"

    def test_asking_for_the_teacher_escalates_without_calling_the_model(
        self, api, session, student, auth, spy
    ):
        events = parse_sse(chat(api, student, auth, request_human_help=True).text)

        escalation = next(e for e in events if e["type"] == "escalation")["escalation"]
        assert escalation["reason"] == "student_requested"
        assert escalation["ticket_id"]
        assert spy.calls == []  # a canned acknowledgement: no model cost
        reply = "".join(e["content"] for e in events if e["type"] == "token")
        assert "docente" in reply
        assert types(events)[-1] == "done"

    def test_asking_twice_in_the_same_conversation_reuses_the_ticket(
        self, api, session, student, auth, spy
    ):
        first = parse_sse(chat(api, student, auth, request_human_help=True).text)
        conversation_id = first[-1]["conversation_id"]

        second = parse_sse(
            chat(api, student, auth, request_human_help=True, conversation_id=conversation_id).text
        )

        ids = {
            next(e for e in run if e["type"] == "escalation")["escalation"]["ticket_id"]
            for run in (first, second)
        }
        assert len(ids) == 1
        assert len(session.scalars(select(SupportTicket)).all()) == 1


class TestFailures:
    def test_a_provider_failure_becomes_an_error_event_without_leaking_details(
        self, api, session, student, auth, spy
    ):
        spy.tokens = ["Ho", "la"]
        spy.fail_at = 1

        response = chat(api, student, auth)

        events = parse_sse(response.text)
        assert types(events) == ["token", "error"]
        assert events[-1]["code"] == "llm_error"
        assert "secret provider failure" not in response.text
        EVENT.validate_python(events[-1])
        assert [m.role for m in session.scalars(select(Message)).all()] == ["user"]


class TestAccess:
    def test_no_token_is_401(self, api):
        response = api.post(URL, json={})

        assert response.status_code == 401

    def test_a_student_outside_the_course_is_403(self, api, make_user, auth, spy, session):
        student = make_user("s1")
        session.add(Course(id="c9", name="Otro"))
        session.flush()

        response = chat(api, student, auth, **{"course_id": "c9"})

        assert response.status_code == 403
        assert spy.calls == []

    def test_unknown_course_is_404(self, api, student, auth, spy):
        assert chat(api, student, auth, course_id="nope").status_code == 404

    def test_someone_elses_conversation_is_404(self, api, make_user, auth, spy):
        owner, intruder = make_user("s1"), make_user("s2")
        conversation_id = parse_sse(chat(api, owner, auth).text)[-1]["conversation_id"]

        response = chat(api, intruder, auth, conversation_id=conversation_id)

        assert response.status_code == 404

    def test_unknown_conversation_is_404(self, api, student, auth, spy):
        assert chat(api, student, auth, conversation_id="nope").status_code == 404


class TestValidation:
    def test_no_messages_is_422(self, api, student, auth, spy):
        body = {"course_id": "c1", "student_level": "basic", "messages": []}

        assert api.post(URL, json=body, headers=auth(student)).status_code == 422

    def test_the_last_message_must_come_from_the_student(self, api, student, auth, spy):
        body = {
            "course_id": "c1",
            "student_level": "basic",
            "messages": [user_msg("hola"), tutor_msg("¿en qué te ayudo?")],
        }

        response = api.post(URL, json=body, headers=auth(student))

        assert response.status_code == 422
        assert response.json()["code"] == "invalid_request"

    def test_unknown_level_is_422(self, api, student, auth, spy):
        assert chat(api, student, auth, student_level="expert").status_code == 422

    def test_oversized_messages_are_422_before_reaching_the_model(self, api, student, auth, spy):
        response = chat(api, student, auth, text="x" * 8001)

        assert response.status_code == 422
        assert spy.calls == []

    def test_too_long_a_history_is_422(self, api, student, auth, spy):
        history = [user_msg("a"), tutor_msg("b")] * 25

        assert chat(api, student, auth, history=history).status_code == 422
