"""Offline text embeddings (feature hashing). No network, no API key."""

import hashlib
import math
import re
import unicodedata

_STOPWORDS = frozenset(
    "a al como con de del el ella en es esta este la las lo los me mi no o para por que se "
    "si su sus un una uno y".split()
)


def tokenize(text: str) -> list[str]:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z0-9]+", plain)
    return [w for w in words if w not in _STOPWORDS] or words


class HashingEmbedder:
    """Deterministic bag-of-words vectors. Texts that share vocabulary end up close.

    Enough to exercise retrieval end to end in development and tests. It is lexical, not
    semantic: Gemini (`GeminiClient`) replaces it when `GEMINI_API_KEY` is set.
    """

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big")
            vector[digest % self.dimensions] += 1.0 if (digest >> 63) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:  # no usable tokens: a fixed unit vector keeps cosine distance defined
            vector[0] = 1.0
            return vector
        return [x / norm for x in vector]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]
