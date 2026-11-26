"""Password hashing with scrypt from the standard library (no extra dependency)."""

import base64
import hashlib
import hmac
import os

_N, _R, _P = 2**14, 8, 1
_KEY_LENGTH = 32
_SCHEME = "scrypt"


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=_KEY_LENGTH)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = _derive(password, salt, _N, _R, _P)
    b64 = base64.b64encode
    return f"{_SCHEME}${_N}${_R}${_P}${b64(salt).decode()}${b64(digest).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time check. A malformed hash is simply a mismatch, never an exception."""
    try:
        scheme, n, r, p, salt, digest = hashed.split("$")
        if scheme != _SCHEME:
            return False
        expected = base64.b64decode(digest)
        actual = _derive(password, base64.b64decode(salt), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)
