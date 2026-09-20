from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.db.models import Role, User
from english7.modules.auth.domain import AuthUser


class AuthRepository(Protocol):
    def get_by_email(self, email: str) -> AuthUser | None: ...

    def get_by_id(self, user_id: UUID) -> AuthUser | None: ...

    def create(self, user: AuthUser) -> AuthUser: ...

    def update_profile(
        self,
        user_id: UUID,
        changes: dict[str, object],
    ) -> AuthUser | None: ...

    def update_password_hash(self, user_id: UUID, password_hash: str) -> bool: ...


class SQLAlchemyAuthRepository:
    _PROFILE_FIELDS = {
        "full_name",
        "date_of_birth",
        "gender",
        "school_name",
        "class_name",
    }

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(user: User, role_name: str) -> AuthUser:
        return AuthUser(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            role=role_name,
            is_active=user.is_active,
            full_name=user.full_name,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            school_name=user.school_name,
            class_name=user.class_name,
        )

    def get_by_email(self, email: str) -> AuthUser | None:
        with self._session_factory() as session:
            row = session.execute(
                select(User, Role.name)
                .join(Role, User.role_id == Role.id)
                .where(User.email == email)
            ).first()
            return self._to_domain(row[0], row[1]) if row else None

    def get_by_id(self, user_id: UUID) -> AuthUser | None:
        with self._session_factory() as session:
            row = session.execute(
                select(User, Role.name)
                .join(Role, User.role_id == Role.id)
                .where(User.id == user_id)
            ).first()
            return self._to_domain(row[0], row[1]) if row else None

    def create(self, user: AuthUser) -> AuthUser:
        with self._session_factory() as session:
            role_id = session.scalar(select(Role.id).where(Role.name == user.role))
            if role_id is None:
                raise RuntimeError(f"Role is not seeded: {user.role}")
            session.add(
                User(
                    id=user.id,
                    email=user.email,
                    password_hash=user.password_hash,
                    role_id=role_id,
                    is_active=user.is_active,
                    full_name=user.full_name,
                    date_of_birth=user.date_of_birth,
                    gender=user.gender,
                    school_name=user.school_name,
                    class_name=user.class_name,
                )
            )
            session.commit()
        return user

    def update_profile(
        self,
        user_id: UUID,
        changes: dict[str, object],
    ) -> AuthUser | None:
        invalid_fields = set(changes) - self._PROFILE_FIELDS
        if invalid_fields:
            names = ", ".join(sorted(invalid_fields))
            raise ValueError(f"Unsupported profile fields: {names}")

        with self._session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                return None
            for field, value in changes.items():
                setattr(user, field, value)
            session.commit()

        return self.get_by_id(user_id)

    def update_password_hash(self, user_id: UUID, password_hash: str) -> bool:
        with self._session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                return False
            user.password_hash = password_hash
            session.commit()
        return True
