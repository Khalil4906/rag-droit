from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.auth import verify_credentials, create_token


router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    if not verify_credentials(body.username, body.password):
        raise HTTPException(
            status_code=401,
            detail="Identifiant ou mot de passe incorrect.",
        )
    token = create_token(body.username)
    return LoginResponse(
        access_token=token,
        username=body.username,
    )


@router.post("/auth/logout")
async def logout() -> dict:
    return {"status": "ok", "message": "Déconnecté."}