from app.auth.jwt_handler import create_access_token, verify_token


def test_a_freshly_created_token_can_be_verified_back_to_the_same_data():
    token = create_access_token({"sub": "doctor@medgraph.ai", "role": "doctor"})
    payload = verify_token(token)

    assert payload is not None
    assert payload["sub"] == "doctor@medgraph.ai"
    assert payload["role"] == "doctor"


def test_a_garbage_string_is_rejected_instead_of_crashing():
    assert verify_token("this-is-not-a-real-token") is None


def test_a_token_signed_with_a_different_secret_is_rejected():
    from jose import jwt
    from app.core.config import settings

    forged = jwt.encode(
        {"sub": "attacker@evil.com", "role": "admin"},
        "a-completely-different-secret-key",
        algorithm=settings.ALGORITHM,
    )

    assert verify_token(forged) is None
