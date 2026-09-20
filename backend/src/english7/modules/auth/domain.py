from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4


class ProfileGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: UUID
    email: str
    password_hash: str
    role: str
    is_active: bool = True
    full_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    school_name: str | None = None
    class_name: str | None = None

    @classmethod
    def new(
        cls,
        *,
        email: str,
        password_hash: str,
        role: str = "student",
    ) -> "AuthUser":
        return cls(
            id=uuid4(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
        )


@dataclass(frozen=True, slots=True)
class TokenClaims:
    subject: UUID
    email: str
    role: str
