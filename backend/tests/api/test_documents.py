import pytest
from pydantic import TypeAdapter
from sqlalchemy import select

from app.db.models import Course, Document, DocumentChunk, Enrollment
from app.schemas import DocumentListResponse, DocumentUploadResponse
from app.services.llm import get_llm_client
from tests.files import DOCX, PDF, PPTX, make_docx, make_pdf, make_pptx

MAX_BYTES = 20 * 1024 * 1024


@pytest.fixture
def teacher(make_user):
    return make_user("t1", role="teacher")


@pytest.fixture
def student(make_user):
    return make_user("s1", role="student")


def upload(api, headers, course="c1", filename="a.pdf", content=None, mime=PDF, **form):
    content = make_pdf(["derivadas basicas"]) if content is None else content
    return api.post(
        f"/api/v1/courses/{course}/documents",
        headers=headers,
        files={"file": (filename, content, mime)},
        data=form,
    )


def listing(api, headers, course="c1"):
    return api.get(f"/api/v1/courses/{course}/documents", headers=headers)


class TestUpload:
    def test_teacher_upload_is_accepted_and_ends_up_indexed(self, api, teacher, auth):
        response = upload(api, auth(teacher), title="Sílabo")

        assert response.status_code == 202
        body = response.json()
        TypeAdapter(DocumentUploadResponse).validate_python(body)
        assert body["status"] == "queued"
        assert body["filename"] == "a.pdf" and body["mime_type"] == PDF
        listed = listing(api, auth(teacher)).json()["documents"]
        assert [(d["document_id"], d["status"], d["title"]) for d in listed] == [
            (body["document_id"], "indexed", "Sílabo")
        ]

    def test_indexing_stores_chunks_with_embeddings_and_pages(self, api, session, teacher, auth):
        pdf = make_pdf(["derivadas basicas", "integrales definidas"])
        document_id = upload(api, auth(teacher), content=pdf).json()["document_id"]

        chunks = session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        ).all()

        assert [c.page for c in chunks] == [1, 2]
        assert [c.course_id for c in chunks] == ["c1", "c1"]
        assert "integrales" in chunks[1].content
        assert len(chunks[0].embedding) == 1024

    @pytest.mark.parametrize(
        ("filename", "build", "mime"),
        [
            pytest.param("g.docx", lambda: make_docx(["Guía de ejercicios."]), DOCX, id="docx"),
            pytest.param("s.pptx", lambda: make_pptx(["Límites"]), PPTX, id="pptx"),
        ],
    )
    def test_docx_and_pptx_are_indexed_too(self, api, teacher, auth, filename, build, mime):
        upload(api, auth(teacher), filename=filename, content=build(), mime=mime)

        assert listing(api, auth(teacher)).json()["documents"][0]["status"] == "indexed"

    def test_type_is_resolved_from_the_extension_when_the_mime_is_generic(self, api, teacher, auth):
        response = upload(api, auth(teacher), mime="application/octet-stream")

        assert response.status_code == 202
        assert response.json()["mime_type"] == PDF

    def test_unsupported_type_is_415(self, api, teacher, auth):
        response = upload(api, auth(teacher), filename="a.txt", content=b"hola", mime="text/plain")

        assert response.status_code == 415
        assert response.json()["code"] == "unsupported_media_type"

    def test_content_that_does_not_match_the_type_is_415(self, api, teacher, auth):
        response = upload(api, auth(teacher), content=b"I am not a pdf")

        assert response.status_code == 415

    def test_over_20_mb_is_413_and_nothing_is_stored(self, api, session, teacher, auth):
        response = upload(api, auth(teacher), content=b"%PDF-" + b"0" * MAX_BYTES)

        assert response.status_code == 413
        assert response.json()["code"] == "file_too_large"
        assert session.scalars(select(Document)).all() == []

    def test_exactly_20_mb_is_accepted(self, api, teacher, auth):
        response = upload(api, auth(teacher), content=b"%PDF-" + b"0" * (MAX_BYTES - 5))

        assert response.status_code == 202

    def test_empty_file_is_422(self, api, teacher, auth):
        response = upload(api, auth(teacher), content=b"")

        assert response.status_code == 422
        assert response.json()["code"] == "invalid_request"

    def test_missing_file_is_422(self, api, teacher, auth):
        response = api.post("/api/v1/courses/c1/documents", headers=auth(teacher))

        assert response.status_code == 422

    def test_title_over_200_chars_is_422(self, api, teacher, auth):
        assert upload(api, auth(teacher), title="t" * 201).status_code == 422

    def test_title_is_optional(self, api, teacher, auth):
        upload(api, auth(teacher))

        assert listing(api, auth(teacher)).json()["documents"][0]["title"] is None

    def test_path_in_the_filename_is_stripped(self, api, teacher, auth):
        response = upload(api, auth(teacher), filename="../../etc/evil.pdf")

        assert response.json()["filename"] == "evil.pdf"

    def test_unreadable_file_ends_up_failed_with_a_reason_and_no_chunks(
        self, api, session, teacher, auth
    ):
        upload(api, auth(teacher), content=b"%PDF-1.4 but then garbage")

        document = listing(api, auth(teacher)).json()["documents"][0]
        assert document["status"] == "failed"
        assert document["error_message"]
        assert session.scalars(select(DocumentChunk)).all() == []

    def test_internal_errors_are_reported_without_leaking_details(
        self, api, teacher, auth, settings
    ):
        class Broken:
            async def embed(self, texts, *, is_query=False):
                raise RuntimeError("secret internal detail")

        api.app.dependency_overrides[get_llm_client] = lambda: Broken()
        upload(api, auth(teacher))

        document = listing(api, auth(teacher)).json()["documents"][0]
        assert document["status"] == "failed"
        assert "secret internal detail" not in document["error_message"]


class TestAuthorization:
    def test_no_token_is_401(self, api):
        assert upload(api, {}).status_code == 401
        assert listing(api, {}).status_code == 401

    def test_student_is_403(self, api, student, auth):
        assert upload(api, auth(student)).status_code == 403
        assert listing(api, auth(student)).status_code == 403

    def test_unknown_course_is_404(self, api, teacher, auth):
        assert upload(api, auth(teacher), course="nope").status_code == 404
        assert listing(api, auth(teacher), course="nope").status_code == 404

    def test_teacher_of_another_course_is_403(self, api, session, teacher, auth):
        session.add(Course(id="c2", name="Otro"))
        session.flush()

        assert upload(api, auth(teacher), course="c2").status_code == 403
        assert listing(api, auth(teacher), course="c2").status_code == 403


class TestListing:
    def test_empty_course_lists_nothing(self, api, teacher, auth):
        response = listing(api, auth(teacher))

        assert response.status_code == 200
        assert response.json() == {"course_id": "c1", "documents": []}

    def test_newest_first_and_contract_valid(self, api, teacher, auth):
        upload(api, auth(teacher), filename="first.pdf")
        upload(api, auth(teacher), filename="second.pdf")

        body = listing(api, auth(teacher)).json()

        TypeAdapter(DocumentListResponse).validate_python(body)
        assert [d["filename"] for d in body["documents"]] == ["second.pdf", "first.pdf"]
        assert body["documents"][0]["size_bytes"] > 0

    def test_documents_of_other_courses_are_not_listed(self, api, session, teacher, auth):
        session.add(Course(id="c2", name="Otro"))
        session.flush()
        session.add(Enrollment(course_id="c2", user_id="t1"))
        session.flush()
        upload(api, auth(teacher), course="c2", filename="other.pdf")

        assert listing(api, auth(teacher)).json()["documents"] == []
