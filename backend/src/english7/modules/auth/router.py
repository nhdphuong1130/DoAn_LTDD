from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from english7.api.errors import ApplicationError
from english7.core.security import PasswordHasher, TokenService
from english7.core.settings import get_settings
from english7.db.session import get_session_factory
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.repository import SQLAlchemyAuthRepository
from english7.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class CredentialsRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@lru_cache
def get_auth_service() -> AuthService:
    settings = get_settings()
    secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else None
    lifetime = (
        timedelta(minutes=settings.access_token_minutes)
        if settings.access_token_minutes is not None
        else None
    )
    return AuthService(
        SQLAlchemyAuthRepository(lambda: get_session_factory()()),
        PasswordHasher(),
        TokenService(
            secret=secret,
            algorithm=settings.jwt_algorithm,
            lifetime=lifetime,
        ),
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthUser:
    if credentials is None:
        raise ApplicationError(
            code="unauthorized",
            message="Authentication is required",
            status_code=401,
        )
    return service.authenticate_token(credentials.credentials)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: CredentialsRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = service.register(payload.email, payload.password)
    return UserResponse(id=str(user.id), email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: CredentialsRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return TokenResponse(access_token=service.login(payload.email, payload.password))


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[AuthUser, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, role=user.role)
