from app.auth.hashing import hash_password, verify_password


def test_hash_password_produces_a_different_string_than_the_input():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"


def test_verify_password_accepts_the_correct_password():
    hashed = hash_password("my-secret-password")
    assert verify_password("my-secret-password", hashed) is True


def test_verify_password_rejects_the_wrong_password():
    hashed = hash_password("my-secret-password")
    assert verify_password("not-the-right-password", hashed) is False


def test_hashing_the_same_password_twice_gives_different_hashes():
    # A good password hash includes a random salt, so two hashes of the
    # same password should never be identical - otherwise two users with
    # the same password would have identical hashes in the database.
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second
