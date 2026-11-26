"""Academic risk with explainability (XAI): a transparent, weighted, rule-based model.

Why rules and not a trained model: there is no labelled history to train on, and a teacher must be
able to *read* why a student is flagged. Every factor is a plain rule with a stated weight, and the
score is literally what the factors add up to:

    risk_score = clamp(0.5 + sum(impact_i), 0, 1)        impact_i = weight_i * severity_i

`severity` is in [-1, 1] (positive = more risk), `impact` is the factor's contribution to the
score, which is the `XaiFactor.impact` the dashboard draws. Thresholds: green < 0.40 <= yellow <
0.65 <= red. Recalibrate weights and thresholds with real data when there is some.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.schemas import RiskLevel, RiskSummary, StudentRisk, XaiFactor

GREEN_BELOW = 0.40
RED_FROM = 0.65
GRADE_SCALE = 5.0
NEUTRAL_GRADE = 3.0  # projected grade when there are no grades yet
PASSING_RATIO = 0.6  # 3.0 / 5

WEIGHTS = {
    "days_since_last_login": 0.30,
    "average_grade": 0.30,
    "missed_assignments": 0.15,
    "tutor_confusion": 0.10,
    "tutor_usage": 0.10,
    "open_tickets": 0.05,
}


@dataclass(frozen=True)
class Grade:
    value: float
    scale: float


@dataclass(frozen=True)
class StudentActivity:
    """What is known about one student in one course (see `activity.load_activity`)."""

    student_id: str
    name: str
    last_activity_at: datetime | None
    grades: list[Grade] = field(default_factory=list)  # recent graded work
    missed_deadlines: int = 0  # recent
    submissions: int = 0  # recent
    questions: int = 0  # tutor questions, recent
    scored_messages: int = 0  # tutor messages that carry a frustration score
    frustrated_messages: int = 0  # of those, how many are above the frustration threshold
    open_tickets: int = 0


def level_for(score: float) -> RiskLevel:
    if score < GREEN_BELOW:
        return RiskLevel.green
    return RiskLevel.yellow if score < RED_FROM else RiskLevel.red


def _clip(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _factor(
    key: str, label: str, severity: float, value: float | str, explanation: str
) -> XaiFactor:
    return XaiFactor(
        key=key,
        label=label,
        impact=round(WEIGHTS[key] * _clip(severity), 4),
        value=value,
        explanation=explanation,
    )


def _inactivity(last: datetime | None, now: datetime) -> XaiFactor:
    label = "Días sin ingresar"
    if last is None:
        return _factor(
            "days_since_last_login",
            label,
            1.0,
            "Sin actividad registrada",
            "No hay actividad registrada de este estudiante.",
        )
    days = max(0, int((now - last).total_seconds() // 86400))
    if days <= 1:
        severity = -0.6
    elif days <= 4:
        severity = -0.6 + 0.2 * (days - 1)
    else:
        severity = _clip((days - 4) / 10)
    explanation = (
        "Ingresó hoy." if days == 0 else f"No ingresa desde hace {_plural(days, 'día', 'días')}."
    )
    return _factor("days_since_last_login", label, severity, days, explanation)


def _grades(grades: list[Grade]) -> XaiFactor | None:
    if not grades:
        return None
    ratio = sum(g.value / g.scale for g in grades) / len(grades)
    shown = f"{ratio * GRADE_SCALE:.1f} / {GRADE_SCALE:g}"
    if ratio >= 0.8:
        explanation = f"Su promedio ({shown}) está por encima de lo esperado."
    elif ratio >= PASSING_RATIO:
        explanation = f"Su promedio ({shown}) está en el rango esperado."
    else:
        explanation = f"Su promedio ({shown}) está por debajo del mínimo recomendado (3.0 / 5)."
    severity = (PASSING_RATIO - ratio) / (1 - PASSING_RATIO)
    return _factor("average_grade", "Promedio de notas", severity, shown, explanation)


def _assignments(missed: int, submissions: int) -> XaiFactor | None:
    label = "Tareas sin entregar"
    if missed > 0:
        text = f"Dejó sin entregar {_plural(missed, 'tarea', 'tareas')} en el último mes."
        return _factor("missed_assignments", label, min(missed / 3, 1), missed, text)
    if submissions > 0:
        text = "Entregó sus tareas a tiempo en el último mes."
        return _factor("missed_assignments", label, -0.5, 0, text)
    return None


def _confusion(scored: int, frustrated: int) -> XaiFactor | None:
    if scored == 0:
        return None
    ratio = frustrated / scored
    value = f"{frustrated} de {scored} mensajes"
    label = "Dudas sin resolver con el tutor"
    if frustrated == 0:
        text = "No mostró señales de frustración al hablar con el tutor."
        return _factor("tutor_confusion", label, -0.3, value, text)
    text = f"Mostró frustración en {value} al consultar al tutor."
    return _factor("tutor_confusion", label, min(1.0, 2 * ratio), value, text)


def _tutor_usage(questions: int) -> XaiFactor:
    severity = _clip(0.4 - 0.2 * questions, -0.6, 1.0)
    if questions == 0:
        text = "No ha usado el tutor en las últimas dos semanas."
    else:
        count = _plural(questions, "consulta", "consultas")
        text = f"Hizo {count} al tutor en las últimas dos semanas."
    return _factor("tutor_usage", "Uso del tutor", severity, questions, text)


def _tickets(open_tickets: int) -> XaiFactor | None:
    if open_tickets == 0:
        return None
    count = _plural(open_tickets, "solicitud", "solicitudes")
    text = f"Tiene {count} de ayuda abiertas al docente."
    return _factor(
        "open_tickets", "Pidió ayuda al docente", min(open_tickets / 2, 1), open_tickets, text
    )


def compute_risk(activity: StudentActivity, now: datetime) -> StudentRisk:
    grade_factor = _grades(activity.grades)
    others = [
        _inactivity(activity.last_activity_at, now),
        _assignments(activity.missed_deadlines, activity.submissions),
        _confusion(activity.scored_messages, activity.frustrated_messages),
        _tutor_usage(activity.questions),
        _tickets(activity.open_tickets),
    ]
    other_factors = [f for f in others if f is not None]
    factors = sorted(
        [*other_factors, *([grade_factor] if grade_factor else [])],
        key=lambda f: abs(f.impact),
        reverse=True,
    )

    score = round(_clip(0.5 + sum(f.impact for f in factors), 0.0, 1.0), 4)

    if activity.grades:
        base = GRADE_SCALE * sum(g.value / g.scale for g in activity.grades) / len(activity.grades)
    else:
        base = NEUTRAL_GRADE
    # Everything except the grades themselves moves the projection (each +0.1 of impact: -0.25).
    projected = _clip(base - 2.5 * sum(f.impact for f in other_factors), 0.0, GRADE_SCALE)

    return StudentRisk(
        student_id=activity.student_id,
        name=activity.name,
        risk_level=level_for(score),
        risk_score=score,
        projected_grade=round(projected, 1),
        grade_scale_max=GRADE_SCALE,
        factors=factors,
        updated_at=now,
    )


def summarize(risks: list[StudentRisk]) -> RiskSummary:
    count = {level: sum(r.risk_level == level for r in risks) for level in RiskLevel}
    return RiskSummary(
        green=count[RiskLevel.green], yellow=count[RiskLevel.yellow], red=count[RiskLevel.red]
    )
