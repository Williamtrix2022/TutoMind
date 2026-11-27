"""`LLMClient` that works with no API key: lexical embeddings and a stand-in tutor.

Used when `GEMINI_API_KEY` is empty, so the whole product can be developed, tested and demoed
offline. The stand-in does not reason: it **presents the course material it was given**, cleanly
(a friendly heading, the sentences that best answer the question as bullets, the material's
worked example and its source). With no relevant material it says so honestly instead of
inventing an answer.
"""

import html
import re
import zlib
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from app.core.config import Settings
from app.services.embeddings import HashingEmbedder
from app.services.lexical import vocabulary
from app.services.retrieval import GENERIC_TERMS, Relevance
from app.services.tutor_prompt import EMPATHY_MARKER, QUESTION_MARKER, SOLUTION_GUARD_MARKER

_SOURCE = re.compile(
    r'<fuente id="[^"]*" titulo="(?P<title>[^"]*)"(?: pagina="(?P<page>\d+)")?>\n'
    r"(?P<content>.*?)\n</fuente>",
    re.DOTALL,
)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡0-9`$(])")
_FILE_EXTENSION = re.compile(r"\.(pdf|docx|pptx)$", re.IGNORECASE)
# Study notes often open with a flattened title line ("Derivadas Cálculo Diferencial · Apuntes…").
_TITLE_LINE = re.compile(r"^.{0,140}?Apuntes de apoyo\s*", re.IGNORECASE)
# PDF text loses line breaks, so a section title sticks to the next sentence: «Regla de la cadena
# Se usa cuando…». A short run of words followed by a capitalized word is such a title: drop it.
_STUCK_HEADING = re.compile(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [a-záéíóúñ]+){0,3} (?=[A-ZÁÉÍÓÚÑ¿¡])")

MAX_SOURCES_SHOWN = 2
MAX_BULLETS = 6
EXAMPLE_SENTENCES = 3
MIN_SENTENCE_CHARS = 25
MAX_SENTENCE_CHARS = 260

_OPENERS = (
    "¡Muy buena pregunta!",
    "¡Excelente pregunta!",
    "¡Claro que sí, vamos a verlo!",
    "Vas por muy buen camino.",
)
EMPATHETIC_OPENERS = (
    "Te entiendo, a veces cuesta: vamos con calma y por partes.",
    "Es normal que esto cueste; lo vemos con calma, paso a paso.",
    "Tranquilo, a todos nos pasa: lo repasamos desde otro ángulo.",
)
_SOLUTION_NOTE = (
    "Te explico el concepto y un ejemplo para que puedas resolver tu ejercicio con confianza."
)
_NOT_FOUND = (
    "Revisé el material de tu curso y no encontré nada sobre esto, así que prefiero no "
    "inventarte una explicación. Prueba a reformular la pregunta con el nombre del tema "
    "(por ejemplo, «regla de la cadena»)."
)
ASK_WHAT_PART = (
    "Cuéntame qué parte exacta se te complica (un paso, un concepto o un ejercicio) y la "
    "revisamos con calma, explicada de otra forma.",
    "¿Qué parte exacta se te complica? Dime si es un paso, un concepto o un ejercicio y lo "
    "vemos de otra manera.",
    "Dime en qué punto te pierdes (un paso, un concepto o un ejercicio) y lo repasamos juntos, "
    "con otra explicación.",
)
_CLOSING = "¿Te queda claro{example} o quieres que revisemos otra parte?"


@dataclass(frozen=True)
class _Source:
    title: str
    page: int | None
    content: str


def _next_variant(variants: tuple[str, ...], history: str) -> str:
    """The first wording not used yet in this conversation, so the tutor never repeats itself."""
    used = sum(variant in history for variant in variants)
    return variants[used % len(variants)]


def _sources(system: str) -> list[_Source]:
    found = []
    for match in _SOURCE.finditer(system):
        title = _FILE_EXTENSION.sub("", html.unescape(match["title"])).strip() or "tu material"
        page = int(match["page"]) if match["page"] else None
        found.append(_Source(title, page, html.unescape(match["content"])))
    return found


@dataclass(frozen=True)
class _Sentence:
    shown: str  # what the student reads
    raw: str  # with its section title still attached: that title is evidence of relevance


def _shorten(sentence: str) -> str:
    if len(sentence) <= MAX_SENTENCE_CHARS:
        return sentence
    return sentence[:MAX_SENTENCE_CHARS].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _sentences(text: str) -> list[_Sentence]:
    """Readable sentences of a chunk, which may start and end in the middle of one."""
    text = _TITLE_LINE.sub("", re.sub(r"\s+", " ", text).strip())
    parts = [p.strip() for p in _SENTENCE_BREAK.split(text)]
    if len(parts) > 1 and parts[0][:1].islower():
        parts = parts[1:]  # the chunk began mid-sentence: that fragment has no beginning
    if len(parts) > 1 and not parts[-1].endswith((".", "!", "?", ":", ";", ")", "`", "$")):
        parts = parts[:-1]  # the chunk ended mid-sentence; the next chunk repeats it whole

    merged: list[str] = []
    index = 0
    while index < len(parts):
        # A bare «Ejemplo.» label belongs to the sentence that follows it.
        if parts[index].rstrip(".:").lower() == "ejemplo" and index + 1 < len(parts):
            parts[index + 1] = f"Ejemplo. {parts[index + 1]}"
        else:
            merged.append(parts[index])
        index += 1

    sentences = []
    for part in merged:
        shown = _STUCK_HEADING.sub("", part, count=1) if len(part) > 40 else part
        if len(shown) >= MIN_SENTENCE_CHARS:
            sentences.append(_Sentence(_shorten(shown), part))
    return sentences


def _split_examples(
    sentences: list[_Sentence],
) -> tuple[list[_Sentence], list[list[_Sentence]]]:
    """Separate the worked examples (each starts with «Ejemplo») from the explanation."""
    explanation: list[_Sentence] = []
    examples: list[list[_Sentence]] = []
    remaining = 0  # sentences still to add to the example being collected
    for sentence in sentences:
        if sentence.shown.lower().startswith("ejemplo"):
            examples.append([sentence])
            remaining = EXAMPLE_SENTENCES - 1
        elif remaining and sentence.shown == sentence.raw:  # a new section ends the example
            examples[-1].append(sentence)
            remaining -= 1
        else:
            remaining = 0
            explanation.append(sentence)
    return explanation, examples


def _overlap(sentence: _Sentence, asked: set[str]) -> int:
    return len(asked & vocabulary(sentence.raw))


def _best(sentences: list[_Sentence], question: str) -> list[_Sentence]:
    """What the material says about the question, in reading order.

    The sentences that share the most vocabulary with it, each followed by the sentence after it
    (explanations continue). With no match at all, the opening sentences.
    """
    asked = vocabulary(question) - GENERIC_TERMS
    overlap = [_overlap(sentence, asked) for sentence in sentences]
    best = max(overlap, default=0)
    if best == 0:
        return sentences[:3]
    top = [i for i, score in enumerate(overlap) if score == best][:3]
    chosen = {j for i in top for j in (i, i + 1) if j < len(sentences)}
    return [sentences[i] for i in sorted(chosen)[:MAX_BULLETS]]


def _best_example(examples: list[list[_Sentence]], question: str) -> list[_Sentence]:
    """The worked example that shares the most vocabulary with the question, if any does."""
    asked = vocabulary(question) - GENERIC_TERMS
    scored = [(sum(_overlap(s, asked) for s in block), block) for block in examples]
    scored = [item for item in scored if item[0] > 0]
    return max(scored, key=lambda item: item[0])[1] if scored else []


def _by_document(sources: list[_Source]) -> list[list[_Source]]:
    """Chunks of the same document together, documents in order of relevance, chunks by page."""
    groups: dict[str, list[_Source]] = {}
    for source in sources:
        groups.setdefault(source.title, []).append(source)
    return [sorted(g, key=lambda src: (src.page is None, src.page or 0)) for g in groups.values()]


def _pages(group: list[_Source]) -> str:
    pages = sorted({src.page for src in group if src.page is not None})
    if not pages:
        return ""
    if len(pages) == 1:
        return f", página {pages[0]}"
    return ", páginas " + ", ".join(map(str, pages[:-1])) + f" y {pages[-1]}"


def _section(group: list[_Source], question: str) -> tuple[str, bool]:
    title = group[0].title
    sentences = [s for source in group for s in _sentences(source.content)]
    explanation, examples = _split_examples(sentences)
    bullets = _best(explanation, question)
    example = _best_example(examples, question)
    if not bullets and example:  # the material is only a worked example: show it as the lesson
        bullets, example = example, []
    lines = [f"### 📘 Lo esencial de «{title}»", ""]
    lines += [f"- {sentence.shown}" for sentence in bullets]
    if example:
        lines += ["", "**Ejemplo del material**", ""] + [f"> {s.shown}" for s in example]
    lines += ["", f"*Fuente: {title}{_pages(group)}.*"]
    return "\n".join(lines), bool(example)


class OfflineLLMClient:
    # The hashing embedder barely separates topics by distance, so relevance is decided by the
    # rare vocabulary the question shares with a chunk (see `app.services.retrieval`).
    relevance = Relevance(max_distance=0.985, lexical_min_score=0.8)

    def __init__(self, settings: Settings) -> None:
        self._embedder = HashingEmbedder(settings.embedding_dimensions)

    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
        return self._embedder.embed(list(texts))

    def _reply(self, prompt: str, system: str) -> str:
        history, _, question = prompt.partition(QUESTION_MARKER)
        question = question.strip()
        empathetic = EMPATHY_MARKER in system
        opener = (
            _next_variant(EMPATHETIC_OPENERS, history)
            if empathetic
            else _OPENERS[zlib.crc32(question.encode()) % len(_OPENERS)]
        )
        groups = _by_document(_sources(system))[:MAX_SOURCES_SHOWN]
        if not groups:
            # A frustrated message is about how the student feels, not a subject to look up.
            return f"{opener} {_next_variant(ASK_WHAT_PART, history) if empathetic else _NOT_FOUND}"

        parts = [opener]
        if SOLUTION_GUARD_MARKER in system:
            parts.append(_SOLUTION_NOTE)
        parts.append("Esto es lo que explica tu material del curso:")
        has_example = False
        for group in groups:
            text, example = _section(group, question)
            parts.append(text)
            has_example = has_example or example
        parts.append(_CLOSING.format(example=" este ejemplo" if has_example else ""))
        return "\n\n".join(parts)

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        for piece in re.split(r"(\s+)", self._reply(prompt, system or "")):
            if piece:
                yield piece
