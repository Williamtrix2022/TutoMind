from app.core.passwords import hash_password, verify_password


def test_correct_password_verifies():
    hashed = hash_password("demo12345")

    assert verify_password("demo12345", hashed)


def test_wrong_password_is_rejected():
    assert not verify_password("otra-clave", hash_password("demo12345"))


def test_hash_is_salted_and_never_contains_the_password():
    first, second = hash_password("demo12345"), hash_password("demo12345")

    assert first != second
    assert "demo12345" not in first


def test_malformed_hash_does_not_raise():
    assert not verify_password("demo12345", "not-a-hash")
    assert not verify_password("demo12345", "")
