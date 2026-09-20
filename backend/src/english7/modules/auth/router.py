from datetime import date, timedelta
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from english7.api.errors import ApplicationError
from english7.core.security import PasswordHasher, TokenService
from english7.core.settings import get_settings
from english7.db.session import get_session_factory
from english7.modules.auth.domain import AuthUser, ProfileGender
from english7.modules.auth.repository import SQLAlchemyAuthRepository
from english7.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class CredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: str | None
    date_of_birth: date | None
    gender: ProfileGender | None
    school_name: str | None
    class_name: str | None

    @classmethod
    def from_user(cls, user: AuthUser) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            school_name=user.school_name,
            class_name=user.class_name,
        )


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=255)
    date_of_birth: date | None = None
    gender: ProfileGender | None = None
    school_name: str | None = Field(default=None, max_length=255)
    class_name: str | None = Field(default=None, max_length=100)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    return UserResponse.from_user(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: CredentialsRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return TokenResponse(access_token=service.login(payload.email, payload.password))


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[AuthUser, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.from_user(user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: ProfileUpdateRequest,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    updated = service.update_profile(
        user.id,
        payload.model_dump(exclude_unset=True),
    )
    return UserResponse.from_user(updated)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    service.change_password(
        user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
