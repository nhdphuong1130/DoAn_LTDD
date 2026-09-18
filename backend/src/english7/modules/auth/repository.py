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


class SQLAlchemyAuthRepository:
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
                )
            )
            session.commit()
        return user

