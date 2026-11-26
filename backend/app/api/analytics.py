from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.access import course_for_teacher
from app.api.deps import require_role
from app.db.models import User
from app.db.session import get_session
from app.schemas import CourseRiskResponse, ErrorResponse, RiskLevel
from app.services.activity import load_activity
from app.services.risk import compute_risk, summarize

router = APIRouter(prefix="/api/v1/analytics/courses", tags=["analytics"])

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.get(
    "/{course_id}/risk",
    operation_id="getCourseRisk",
    summary="Riesgo académico por estudiante con explicabilidad (XAI)",
    response_model=CourseRiskResponse,
    responses=_ERRORS,
)
def get_course_risk(
    course_id: str,
    level: RiskLevel | None = None,
    user: User = Depends(require_role("teacher")),
    session: Session = Depends(get_session),
) -> CourseRiskResponse:
    """Most at-risk first. `level` narrows the list; the summary always counts the whole course."""
    course_for_teacher(session, user, course_id)
    now = datetime.now(UTC)
    risks = [compute_risk(a, now) for a in load_activity(session, course_id, now)]
    risks.sort(key=lambda r: (-r.risk_score, r.name))
    shown = [r for r in risks if level is None or r.risk_level == level]
    return CourseRiskResponse(course_id=course_id, summary=summarize(risks), students=shown)
