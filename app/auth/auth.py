from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(),
    ).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode(),
        hashed.encode(),
    )


def verify_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    if username != settings.auth_username:
        return False
    return verify_password(password, settings.auth_password_hash)


def create_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(
        hours=settings.jwt_expire_hours
    )
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256",
    )


def verify_token(token: str) -> Optional[str]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        return payload.get("sub")
    except JWTError:
        return None