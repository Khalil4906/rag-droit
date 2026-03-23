from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth import verify_token


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(
        bearer_scheme
    ),
) -> str:
    token = credentials.credentials
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré. Reconnecte-toi.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username