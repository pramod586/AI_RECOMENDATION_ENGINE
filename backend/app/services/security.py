
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from app.config import settings


# JWT configuration
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing. Please add it to your .env file."
    )


# Password hashing
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Convert a plain password into a secure hash."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether a password matches its stored hash."""
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""

    to_encode = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Validate and decode a JWT access token."""

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )