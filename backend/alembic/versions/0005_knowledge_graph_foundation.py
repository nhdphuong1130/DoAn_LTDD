"""Add authoritative knowledge graph tables.

Revision ID: 0005_knowledge_graph_foundation
Revises: 0004_seed_application_roles
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_knowledge_graph_foundation"
down_revision = "0004_seed_application_roles"
branch_labels = None
depends_on = None


def _assertion_columns(*, source_columns: tuple[sa.Column, ...]) -> list:
    return [
        *source_columns,
        sa.Column("assertion_type", sa.String(length=50), nullable=False),
        sa.Column("role_weight", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("review_status", sa.String(length=30), nullable=False),
        sa.Column("evidence_reference", sa.String(length=1024), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=255), nullable=True),
        sa.Column("ontology_version", sa.String(length=100), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "knowledge_concepts",
        sa.Column("concept_type", sa.String(length=50), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("description_vi", sa.Text(), nullable=True),
        sa.Column("concept_text", sa.Text(), nullable=False),
        sa.Column("ontology_version", sa.String(length=100), nullable=False),
        sa.Column("review_status", sa.String(length=30), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=255), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ontology_version",
            "concept_type",
            "canonical_name",
            name="uq_knowledge_concept_identity",
        ),
    )
    op.create_index(
        "ix_knowledge_concepts_review_version",
        "knowledge_concepts",
        ["review_status", "ontology_version"],
    )

    op.create_table(
        "fragment_concept_assertions",
        *_assertion_columns(
            source_columns=(
                sa.Column("fragment_id", sa.Uuid(), nullable=False),
                sa.Column("concept_id", sa.Uuid(), nullable=False),
            )
        ),
        sa.CheckConstraint(
            "role_weight >= 0 AND role_weight <= 1",
            name="ck_fragment_concept_role_weight",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_fragment_concept_confidence",
        ),
        sa.ForeignKeyConstraint(["concept_id"], ["knowledge_concepts.id"]),
        sa.ForeignKeyConstraint(["fragment_id"], ["source_fragments.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fragment_id",
            "concept_id",
            "assertion_type",
            name="uq_fragment_concept_assertion",
        ),
    )

    relation_columns = _assertion_columns(
        source_columns=(
            sa.Column("source_concept_id", sa.Uuid(), nullable=False),
            sa.Column("target_concept_id", sa.Uuid(), nullable=False),
        )
    )
    relation_columns.insert(
        4, sa.Column("evidence_fragment_id", sa.Uuid(), nullable=True)
    )
    op.create_table(
        "concept_relation_assertions",
        *relation_columns,
        sa.CheckConstraint(
            "role_weight >= 0 AND role_weight <= 1",
            name="ck_concept_relation_role_weight",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_concept_relation_confidence",
        ),
        sa.ForeignKeyConstraint(["source_concept_id"], ["knowledge_concepts.id"]),
        sa.ForeignKeyConstraint(["target_concept_id"], ["knowledge_concepts.id"]),
        sa.ForeignKeyConstraint(["evidence_fragment_id"], ["source_fragments.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_concept_id",
            "target_concept_id",
            "assertion_type",
            name="uq_concept_relation_assertion",
        ),
    )

    unit_columns = _assertion_columns(
        source_columns=(
            sa.Column("unit_id", sa.Uuid(), nullable=False),
            sa.Column("concept_id", sa.Uuid(), nullable=False),
        )
    )
    unit_columns.insert(4, sa.Column("evidence_fragment_id", sa.Uuid(), nullable=True))
    op.create_table(
        "unit_concept_assertions",
        *unit_columns,
        sa.CheckConstraint(
            "role_weight >= 0 AND role_weight <= 1",
            name="ck_unit_concept_role_weight",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_unit_concept_confidence",
        ),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["concept_id"], ["knowledge_concepts.id"]),
        sa.ForeignKeyConstraint(["evidence_fragment_id"], ["source_fragments.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "unit_id", "concept_id", "assertion_type", name="uq_unit_concept_assertion"
        ),
    )

    for table in (
        "fragment_concept_assertions",
        "concept_relation_assertions",
        "unit_concept_assertions",
    ):
        op.create_index(
            f"ix_{table}_review_version",
            table,
            ["review_status", "ontology_version"],
        )

    op.create_table(
        "graph_builds",
        sa.Column("source_checksum", sa.String(length=128), nullable=False),
        sa.Column("ontology_version", sa.String(length=100), nullable=False),
        sa.Column("embedding_provider", sa.String(length=50), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding_model_version", sa.String(length=100), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column(
            "embedding_preprocessing_version", sa.String(length=100), nullable=False
        ),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("fragment_index_name", sa.String(length=255), nullable=True),
        sa.Column("concept_index_name", sa.String(length=255), nullable=True),
        sa.Column("expected_counts", sa.JSON(), nullable=False),
        sa.Column("actual_counts", sa.JSON(), nullable=True),
        sa.Column("validation_report", sa.JSON(), nullable=True),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "embedding_dimensions > 0", name="ck_graph_build_embedding_dimensions"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_graph_builds_status", "graph_builds", ["status"])
    op.create_index(
        "ix_graph_builds_source_identity",
        "graph_builds",
        ["source_checksum", "ontology_version", "embedding_model"],
    )


def downgrade() -> None:
    op.drop_table("graph_builds")
    op.drop_table("unit_concept_assertions")
    op.drop_table("concept_relation_assertions")
    op.drop_table("fragment_concept_assertions")
    op.drop_table("knowledge_concepts")
