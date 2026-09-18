from sqlalchemy import select

from english7.db.models import Role
from english7.db.session import get_session_factory


def test_migrations_seed_required_application_roles() -> None:
    with get_session_factory()() as session:
        roles = set(session.scalars(select(Role.name)).all())

    assert {"student", "admin"} <= roles
