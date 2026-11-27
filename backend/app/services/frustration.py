"""Frustration detection and the decision to *offer* the teacher's help.

Rule-based on purpose: transparent, free, deterministic and testable. Only the student's own
messages count. Code, inline code and math are ignored so they never trigger it by accident.

The teacher is the last resort, so the tutor offers to escalate only when:
- the student asks for it (`student_requested`);
- the frustration persists (`persistent_frustration`: frustrated now and in at least 2 of the last
  3 messages); or
- the student says they still do not understand after at least 2 explanations
  (`repeated_failure`).
Offering is not escalating: a ticket is created only when the student confirms.
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
# "Still lost" only counts once the tutor has explained at least this many times.
MIN_EXPLANATIONS_BEFORE_ESCALATING = 2

EscalationReason = Literal["student_requested", "persistent_frustration", "repeated_failure"]

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
# The student says out loud that the explanation did not land (lower-case text without accents).
_STILL_LOST = [
    re.compile(p)
    for p in (
        r"\bsigo sin (?:entender|comprender)\b",
        r"\b(?:aun|todavia) no (?:lo |la |te )?(?:entiendo|entendi|comprendo|me queda claro)\b",
        r"\bsigue sin (?:quedar|quedarme)\b",
        r"\bno me queda claro\b",
        r"\bsigo (?:perdid[oa]|confundid[oa]|igual)\b",
        r"\bno (?:lo |la )?(?:entiendo|entendi|comprendo) (?:todavia|aun)\b",
    )
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


def says_still_lost(text: str) -> bool:
    """Does the student say the explanation did not help?"""
    normalized = _normalize(text)
    return any(pattern.search(normalized) for pattern in _STILL_LOST)


def assess(messages: list[ChatMessage], request_human_help: bool) -> Assessment:
    scores = [message_score(m.content) for m in messages if m.role == "user"]
    current = scores[-1] if scores else 0.0
    detected = current >= DETECTION_THRESHOLD

    recent = scores[-PERSISTENCE_WINDOW:]
    persistent = detected and sum(s >= DETECTION_THRESHOLD for s in recent) >= PERSISTENCE_MIN_HITS

    explanations = sum(1 for m in messages if m.role == "assistant")
    last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
    still_lost = explanations >= MIN_EXPLANATIONS_BEFORE_ESCALATING and says_still_lost(last_user)

    reason: EscalationReason | None = None
    if request_human_help:
        reason = "student_requested"
    elif persistent:
        reason = "persistent_frustration"
    elif still_lost:
        reason = "repeated_failure"

    signal = FrustrationSignal(detected=detected, score=current, adapted_tone=detected)
    return Assessment(frustration=signal, escalation_reason=reason)
