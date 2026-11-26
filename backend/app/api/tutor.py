import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.models import Course, Enrollment, User
from app.db.session import SessionFactory, get_session, get_session_factory
from app.schemas import TutorChatRequest, TutorStreamEvent
from app.services.llm import LLMClient, get_llm_client
from app.services.moodle import moodle_course_url
from app.services.tutor import prepare_turn, stream_events, validate_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])


# Errors are plain JSON even though the success response is an event stream.
_JSON_ERROR = {
    "description": "Error",
    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
}


class EventStreamResponse(StreamingResponse):
    media_type = "text/event-stream"


def _check_course_access(session: Session, user: User, course_id: str) -> None:
    if session.get(Course, course_id) is None:
        raise ApiError(404, "not_found", "El curso no existe.")
    if session.get(Enrollment, (course_id, user.id)) is None:
        raise ApiError(403, "forbidden", "No perteneces a este curso.")


@router.post(
    "/chat/stream",
    operation_id="streamTutorChat",
    summary="Chat con el tutor (streaming SSE)",
    response_class=EventStreamResponse,
    responses={
        200: {"description": "Flujo de eventos del tutor", "model": TutorStreamEvent},
        401: _JSON_ERROR,
        422: _JSON_ERROR,
    },
)
async def stream_tutor_chat(
    body: TutorChatRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
    session_factory: SessionFactory = Depends(get_session_factory),
    settings: Settings = Depends(get_settings),
) -> EventStreamResponse:
    question = validate_request(body)
    await run_in_threadpool(_check_course_access, session, user, body.course_id)

    query_vector = None
    if not body.request_human_help:  # a canned reply needs no retrieval
        try:
            query_vector = (await llm.embed([question], is_query=True))[0]
        except Exception:
            # No material is better than no tutor: answer without it.
            logger.exception("Embedding the question failed; answering without course material")

    course_url = moodle_course_url(settings, body.course_id)
    turn = await run_in_threadpool(prepare_turn, session, user, body, query_vector, course_url)
    return EventStreamResponse(
        stream_events(turn, llm, session_factory),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
