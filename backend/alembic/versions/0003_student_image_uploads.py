"""Add owner-scoped student image uploads.

Revision ID: 0003_student_image_uploads
Revises: 0002_source_document_object_key
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_student_image_uploads"
down_revision = "0002_source_document_object_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "student_image_uploads" in inspector.get_table_names():
        return
    op.create_table(
        "student_image_uploads",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("size_bytes > 0"),
        sa.CheckConstraint(
            "ocr_confidence IS NULL OR (ocr_confidence >= 0 AND ocr_confidence <= 1)"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "student_image_uploads" in inspector.get_table_names():
        op.drop_table("student_image_uploads")
