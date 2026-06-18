"""JWT creation and verification.

Two token types share the signing secret but carry a `type` claim so an access
token can't be used to reset a password (or vice-versa).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

# Password-reset tokens are deliberately short-lived.
RESET_TOKEN_MINUTES = 30


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or the wrong type."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(user_id: int, token_type: str, expires_in: timedelta) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": _now(),
        "exp": _now() + expires_in,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _encode(
        user_id, "access", timedelta(minutes=get_settings().jwt_expires_minutes)
    )


def create_reset_token(user_id: int) -> str:
    return _encode(user_id, "reset", timedelta(minutes=RESET_TOKEN_MINUTES))


def decode_token(token: str, *, expected_type: str) -> int:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired token") from exc
    if payload.get("type") != expected_type:
        raise TokenError("Wrong token type")
    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise TokenError("Malformed token subject") from exc
