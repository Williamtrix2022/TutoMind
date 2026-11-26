"""Split page text into overlapping chunks that fit the embedding model."""

from dataclasses import dataclass

from app.services.extraction import Page

DEFAULT_SIZE = 1000
DEFAULT_OVERLAP = 150


@dataclass(frozen=True)
class Chunk:
    index: int
    page: int | None
    content: str


def _words(text: str, size: int) -> list[str]:
    words: list[str] = []
    for word in text.split():
        # A "word" longer than a chunk (a URL, a base64 blob) would never fit: cut it.
        words += (
            [word[i : i + size] for i in range(0, len(word), size)] if len(word) > size else [word]
        )
    return words


def _overlap_tail(words: list[str], overlap: int) -> list[str]:
    tail: list[str] = []
    length = 0
    for word in reversed(words):
        added = len(word) + (1 if tail else 0)
        if length + added > overlap:
            break
        tail.insert(0, word)
        length += added
    return tail


def chunk_pages(
    pages: list[Page], size: int = DEFAULT_SIZE, overlap: int = DEFAULT_OVERLAP
) -> list[Chunk]:
    """Chunks never exceed `size` characters, never mix pages, and share `overlap` characters."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    chunks: list[Chunk] = []

    for page in pages:
        current: list[str] = []
        length = 0

        def emit(words: list[str], page: Page = page) -> None:
            chunks.append(Chunk(index=len(chunks), page=page.number, content=" ".join(words)))

        for word in _words(page.text, size):
            added = len(word) + (1 if current else 0)
            if current and length + added > size:
                emit(current)
                current = _overlap_tail(current, overlap)
                length = len(" ".join(current))
                added = len(word) + (1 if current else 0)
                if length + added > size:  # the tail leaves no room for the word: drop it
                    current, length, added = [], 0, len(word)
            current.append(word)
            length += added
        if current:
            emit(current)

    return chunks
