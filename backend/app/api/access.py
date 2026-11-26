"""Course-level access checks shared by the teacher-only endpoints."""

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.models import Course, Enrollment, User


def course_for_teacher(session: Session, user: User, course_id: str) -> Course:
    """The course, if it exists and the user belongs to it. 404 and 403 otherwise."""
    course = session.get(Course, course_id)
    if course is None:
        raise ApiError(404, "not_found", "El curso no existe.")
    if session.get(Enrollment, (course_id, user.id)) is None:
        raise ApiError(403, "forbidden", "No tienes permiso sobre este curso.")
    return course
