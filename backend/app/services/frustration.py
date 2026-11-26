"""Frustration detection and the decision to escalate to the teacher.

Rule-based on purpose: transparent, free, deterministic and testable. Only the student's own
messages count. Code, inline code and math are ignored so they never trigger it by accident.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.schemas import ChatMessage, FrustrationSignal

DETECTION_THRESHOLD = 0.5
# Escalate when the student is frustrated now and was in at least 2 of their last 3 messages.
PERSISTENCE_WINDOW = 3
PERSISTENCE_MIN_HITS = 2

EscalationReason = Literal["student_requested", "persistent_frustration"]

# (pattern on lower-case text without accents, weight). Weights combine as a noisy-or.
_SIGNALS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(p), w)
    for p, w in [
        (r"\bme rindo\b|\bme doy por vencid[oa]\b", 0.85),
        (r"\bfrustrad[oa]s?\b|\bfrustracion\b", 0.8),
        (r"\b(?:estoy|ando|toy) (?:harto|harta|cansad[oa]|agotad[oa])\b|\bhart[oa] de\b", 0.65),
        (r"\bno (?:lo |la |nada )?(?:entiendo|entendi|comprendo)\b", 0.55),
        (r"\bsigo sin (?:entender|comprender)\b", 0.55),
        (r"\bno (?:puedo|logro|consigo)\b", 0.5),
        (r"\bimposible\b", 0.5),
        (r"\bodio\b", 0.5),
        (r"\bno sirve\b|\bno tiene sentido\b|\bnada funciona\b|\bno funciona\b", 0.4),
        (r"\botra vez\b|\bde nuevo\b|\bya (?:lo )?intente\b", 0.2),
    ]
]
_EXCLAMATIONS = re.compile(r"!{2,}")
_NON_PROSE = re.compile(r"```.*?```|`[^`]*`|\$\$.*?\$\$|\$[^$]*\$", re.DOTALL)


def _normalize(text: str) -> str:
    text = _NON_PROSE.sub(" ", text)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def _is_shouting(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.6


def message_score(text: str) -> float:
    """Frustration of one message, from 0 (calm) to 1 (very frustrated)."""
    prose = _NON_PROSE.sub(" ", text)
    normalized = _normalize(text)
    remaining = 1.0
    matched = False
    for pattern, weight in _SIGNALS:
        if pattern.search(normalized):
            matched = True
            remaining *= 1 - weight
    if not matched:
        return 0.0
    # Shouting or "!!" only amplify an expression that is already there ("¡¡Gracias!!" is fine).
    if _is_shouting(prose):
        remaining *= 0.85
    if _EXCLAMATIONS.search(prose):
        remaining *= 0.85
    return round(min(1.0, 1 - remaining), 4)


@dataclass(frozen=True)
class Assessment:
    frustration: FrustrationSignal
    escalation_reason: EscalationReason | None


def assess(messages: list[ChatMessage], request_human_help: bool) -> Assessment:
    scores = [message_score(m.content) for m in messages if m.role == "user"]
    current = scores[-1] if scores else 0.0
    detected = current >= DETECTION_THRESHOLD

    recent = scores[-PERSISTENCE_WINDOW:]
    persistent = detected and sum(s >= DETECTION_THRESHOLD for s in recent) >= PERSISTENCE_MIN_HITS

    reason: EscalationReason | None = None
    if request_human_help:
        reason = "student_requested"
    elif persistent:
        reason = "persistent_frustration"

    signal = FrustrationSignal(detected=detected, score=current, adapted_tone=detected)
    return Assessment(frustration=signal, escalation_reason=reason)
