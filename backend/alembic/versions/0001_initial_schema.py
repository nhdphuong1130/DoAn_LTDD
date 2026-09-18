"""Create the initial English 7 schema.

Revision ID: 0001_initial_schema
Revises:
"""

from alembic import op

from english7.db.base import Base
from english7.db import models  # noqa: F401

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)

