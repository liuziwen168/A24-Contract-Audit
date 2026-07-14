from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.errors import fail


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, digest = stored.split("$", 3)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.urlsafe_b64decode(salt + "=="), int(rounds)
        )
        return hmac.compare_digest(_b64(actual), digest)
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(
        json.dumps(
            {
                "sub": str(user_id),
                "role": role,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(seconds=settings.jwt_expire_seconds)).timestamp()),
            },
            separators=(",", ":"),
        ).encode()
    )
    signed = f"{header}.{payload}".encode()
    return f"{signed.decode()}.{_b64(hmac.new(settings.jwt_secret.encode(), signed, hashlib.sha256).digest())}"


def decode_token(token: str) -> dict[str, object]:
    try:
        header, payload, signature = token.split(".")
        signed = f"{header}.{payload}".encode()
        expected = _b64(hmac.new(settings.jwt_secret.encode(), signed, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if int(data["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return data
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise fail("AUTH_TOKEN_INVALID")
