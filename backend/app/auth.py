import hashlib
import hmac
import os
import secrets
import time

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me")


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000)
    return f"{salt}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    salt, digest = stored.split("$")
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000)
    return hmac.compare_digest(dk.hex(), digest)


def make_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": int(time.time()) + 7 * 86400}, SECRET, algorithm="HS256")


def optional_user(authorization: str | None = Header(None), db: Session = Depends(get_db)) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        payload = jwt.decode(authorization.split(" ", 1)[1], SECRET, algorithms=["HS256"])
        return db.get(User, int(payload["sub"]))
    except Exception:
        return None


def required_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in")
    return user
