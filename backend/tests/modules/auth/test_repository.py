from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from english7.db.base import Base
from english7.db.models import Role
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.repository import SQLAlchemyAuthRepository


@pytest.fixture
def repository() -> Iterator[SQLAlchemyAuthRepository]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        session.add(Role(name="student"))
        session.commit()

    yield SQLAlchemyAuthRepository(session_factory)
    engine.dispose()


def test_repository_updates_only_requested_profile_fields(
    repository: SQLAlchemyAuthRepository,
) -> None:
    user = repository.create(
        AuthUser.new(
            email="student@example.com",
            password_hash="hash",
        )
    )

    updated = repository.update_profile(
        user.id,
        {"full_name": "Nguyễn An", "class_name": "7A1"},
    )

    assert updated is not None
    assert updated.full_name == "Nguyễn An"
    assert updated.class_name == "7A1"
    assert updated.email == "student@example.com"


def test_repository_updates_password_hash(
    repository: SQLAlchemyAuthRepository,
) -> None:
    user = repository.create(
        AuthUser.new(email="student@example.com", password_hash="old-hash")
    )

    assert repository.update_password_hash(user.id, "new-hash") is True
    assert repository.get_by_id(user.id).password_hash == "new-hash"  # type: ignore[union-attr]
