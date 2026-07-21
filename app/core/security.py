import difflib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"
TOKEN_TTL_DAYS = 7

# A small curated list of the most common weak passwords, mirroring the intent
# of Django's CommonPasswordValidator without bundling a full wordlist asset.
_COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "password1",
    "111111", "123123", "letmein", "welcome", "monkey", "iloveyou",
    "admin", "login", "passw0rd", "starwars", "dragon", "sunshine",
    "princess", "football", "baseball", "trustno1", "superman",
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def validate_password_strength(password: str, username: str = "", email: str = "") -> None:
    if len(password) < 8:
        raise ValueError("This password is too short. It must contain at least 8 characters.")

    if password.isdigit():
        raise ValueError("This password is entirely numeric.")

    if password.lower() in _COMMON_PASSWORDS:
        raise ValueError("This password is too common.")

    email_local = email.split("@")[0] if email else ""
    for attribute in (username, email_local):
        if not attribute:
            continue
        similarity = difflib.SequenceMatcher(a=password.lower(), b=attribute.lower()).quick_ratio()
        if similarity > 0.7:
            raise ValueError("The password is too similar to the username or email.")


def create_access_token(user_id: str, username: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "iat": now,
        "exp": now + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
