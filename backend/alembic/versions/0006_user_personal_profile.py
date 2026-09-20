"""Add personal profile fields to users.

Revision ID: 0006_user_personal_profile
Revises: 0005_knowledge_graph_foundation
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_user_personal_profile"
down_revision = "0005_knowledge_graph_foundation"
branch_labels = None
depends_on = None


PROFILE_COLUMNS = (
    sa.Column("full_name", sa.Unicode(255), nullable=True),
    sa.Column("date_of_birth", sa.Date(), nullable=True),
    sa.Column("gender", sa.String(30), nullable=True),
    sa.Column("school_name", sa.Unicode(255), nullable=True),
    sa.Column("class_name", sa.Unicode(100), nullable=True),
)


def upgrade() -> None:
    existing = {
        item["name"] for item in sa.inspect(op.get_bind()).get_columns("users")
    }
    for column in PROFILE_COLUMNS:
        if column.name not in existing:
            op.add_column("users", column)


def downgrade() -> None:
    existing = {
        item["name"] for item in sa.inspect(op.get_bind()).get_columns("users")
    }
    for name in (
        "class_name",
        "school_name",
        "gender",
        "date_of_birth",
        "full_name",
    ):
        if name in existing:
            op.drop_column("users", name)
