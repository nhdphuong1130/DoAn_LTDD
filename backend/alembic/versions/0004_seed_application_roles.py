"""Seed roles required by authentication.

Revision ID: 0004_seed_application_roles
Revises: 0003_student_image_uploads
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0004_seed_application_roles"
down_revision = "0003_student_image_uploads"
branch_labels = None
depends_on = None

_ROLES = {
    "student": UUID("4b660d73-b062-46d2-a52e-590cc4d15ee1"),
    "admin": UUID("5a4559de-52f2-4b45-ad11-660e7c53277d"),
}


def upgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
    )
    connection = op.get_bind()
    existing = set(connection.execute(sa.select(roles.c.name)).scalars())
    for name, role_id in _ROLES.items():
        if name not in existing:
            connection.execute(roles.insert().values(id=role_id, name=name))


def downgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
    )
    users = sa.table("users", sa.column("role_id", sa.Uuid()))
    connection = op.get_bind()
    used = set(connection.execute(sa.select(users.c.role_id)).scalars())
    removable = [role_id for role_id in _ROLES.values() if role_id not in used]
    if removable:
        connection.execute(roles.delete().where(roles.c.id.in_(removable)))
