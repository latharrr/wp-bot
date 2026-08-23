from datetime import datetime, timedelta, timezone

import jwt

from app.core.auth import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import get_settings


def test_hash_password_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_create_and_decode_access_token():
    token = create_access_token("alice")
    assert decode_access_token(token) == "alice"


def test_decode_rejects_garbage_token():
    assert decode_access_token("not-a-jwt") is None


def test_decode_rejects_expired_token():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {"sub": "alice", "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    assert decode_access_token(expired) is None


def test_decode_rejects_token_signed_with_wrong_secret():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "alice", "iat": now, "exp": now + timedelta(hours=1)},
        "some-other-secret",
        algorithm=JWT_ALGORITHM,
    )
    assert decode_access_token(token) is None
