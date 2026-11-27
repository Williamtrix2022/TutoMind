"""Shared vocabulary helpers: which words of a text can say what it is about."""

from app.services.embeddings import tokenize

MIN_WORD_LENGTH = 4  # ignore tiny words when deciding that two texts talk about the same thing


def stem(word: str) -> str:
    """Spanish plural to singular ("funciones" -> "funcion", "derivadas" -> "derivada")."""
    if word.endswith("es") and len(word) > 5:
        return word[:-2]
    if word.endswith("s") and len(word) > 4:
        return word[:-1]
    return word


def vocabulary(text: str) -> set[str]:
    """The stemmed content words of a text, without accents, case, plurals or tiny words."""
    return {stem(t) for t in tokenize(text) if len(t) >= MIN_WORD_LENGTH}
