"""Store the source object's configurable storage key.

Revision ID: 0002_source_document_object_key
Revises: 0001_initial_schema
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_source_document_object_key"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("source_documents")}
    if "object_key" not in columns:
        op.add_column(
            "source_documents",
            sa.Column("object_key", sa.String(length=1024), nullable=True),
        )
        op.create_unique_constraint(
            "uq_source_documents_object_key", "source_documents", ["object_key"]
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("source_documents")}
    if "object_key" in columns:
        unique_names = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("source_documents")
        }
        if "uq_source_documents_object_key" in unique_names:
            op.drop_constraint(
                "uq_source_documents_object_key", "source_documents", type_="unique"
            )
        op.drop_column("source_documents", "object_key")
