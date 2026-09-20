import os
from dataclasses import replace
from hashlib import sha256
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from neo4j import GraphDatabase
from sqlalchemy import select

from english7.db.models import (
    Activity,
    GraphBuild,
    ReviewStatus,
    Section,
    SourceDocument,
    SourceFragment,
    Textbook,
    Unit,
)
from english7.db.session import get_session_factory
from english7.modules.knowledge.build_service import (
    GraphBuildValidationError,
    KnowledgeGraphBuildService,
)
from english7.modules.knowledge.domain import (
    AssertionType,
    ConceptType,
    GraphBuildStatus,
)
from english7.modules.knowledge.embedding import EmbeddingIdentity
from english7.modules.knowledge.graph_builder import ProjectionEmbeddingBuilder
from english7.modules.knowledge.neo4j_repository import VersionedNeo4jRepository
from english7.modules.knowledge.ontology_importer import OntologyImporter
from english7.modules.knowledge.ontology_manifest import (
    ConceptEntry,
    ConceptRelationEntry,
    FragmentAssertionEntry,
    OntologyManifest,
    UnitAssertionEntry,
)
from english7.modules.knowledge.sql_repository import SQLAlchemyKnowledgeRepository


class DeterministicEmbedder:
    identity = EmbeddingIdentity("fake", "deterministic", "v1", 384, "", "", "v1")

    def embed_documents(self, texts):
        vectors = []
        for text in texts:
            digest = sha256(text.encode("utf-8")).digest()
            vector = [0.0] * self.identity.dimensions
            vector[int.from_bytes(digest[:2], "big") % len(vector)] = 1.0
            vectors.append(vector)
        return tuple(vectors)


class InvalidatingRepository:
    def __init__(self, repository: VersionedNeo4jRepository) -> None:
        self._repository = repository

    def __getattr__(self, name):
        return getattr(self._repository, name)

    def validate_build(self, *args, **kwargs):
        report = self._repository.validate_build(*args, **kwargs)
        return replace(report, failures=("forced_integration_failure",))


def _seed_curriculum(repository: SQLAlchemyKnowledgeRepository):
    sessions = get_session_factory()
    textbook_id, unit_id, section_id, activity_id, document_id = (
        uuid4() for _ in range(5)
    )
    verified_ids = (uuid4(), uuid4())
    draft_id = uuid4()
    with sessions() as session, session.begin():
        session.add(Textbook(id=textbook_id, title="English 7", is_active=True))
        session.flush()
        session.add(
            Unit(
                id=unit_id,
                textbook_id=textbook_id,
                number=1,
                title="Hobbies",
                is_published=True,
            )
        )
        session.flush()
        session.add(
            Section(
                id=section_id,
                unit_id=unit_id,
                title="Getting Started",
                section_type="lesson",
                position=1,
            )
        )
        session.flush()
        session.add(
            Activity(
                id=activity_id,
                section_id=section_id,
                number="1",
                activity_type="reading",
                instruction="Read",
            )
        )
        session.flush()
        session.add(
            SourceDocument(
                id=document_id,
                textbook_id=textbook_id,
                original_filename="integration.pdf",
                object_key=f"sources/{document_id}.pdf",
                file_hash=str(document_id),
                page_count=20,
                ingestion_version="integration-v1",
            )
        )
        session.flush()
        for fragment_id, status, published, text in (
            (verified_ids[0], ReviewStatus.VERIFIED.value, True, "I collect dolls."),
            (verified_ids[1], ReviewStatus.VERIFIED.value, True, "I read books."),
            (draft_id, ReviewStatus.DRAFT.value, False, "unreviewed content"),
        ):
            session.add(
                SourceFragment(
                    id=fragment_id,
                    source_document_id=document_id,
                    activity_id=activity_id,
                    pdf_page=12,
                    printed_page=10,
                    x=0,
                    y=0,
                    width=1,
                    height=1,
                    normalized_text=text,
                    review_status=status,
                    is_published=published,
                )
            )

    concept_a, concept_b = uuid4(), uuid4()
    manifest = OntologyManifest(
        schema_version=1,
        manifest_id=uuid4(),
        ontology_version="integration-v1",
        created_by="integration-reviewer",
        concepts=(
            ConceptEntry(
                concept_a,
                ConceptType.TOPIC,
                "Hobbies",
                "Leisure activities",
                "Sở thích",
                "hobbies and leisure activities",
                ReviewStatus.VERIFIED,
                {"aliases": ["free-time activities"]},
            ),
            ConceptEntry(
                concept_b,
                ConceptType.GRAMMAR,
                "Present simple",
                "Habits and routines",
                "Thói quen và hoạt động thường ngày",
                "present simple for habits",
                ReviewStatus.VERIFIED,
                {},
            ),
        ),
        fragment_assertions=(
            FragmentAssertionEntry(
                uuid4(),
                verified_ids[0],
                concept_a,
                AssertionType.TEACHES,
                1.0,
                1.0,
                ReviewStatus.VERIFIED,
                evidence_reference="English 7 p.10",
            ),
        ),
        concept_relations=(
            ConceptRelationEntry(
                uuid4(),
                concept_a,
                concept_b,
                AssertionType.PREREQUISITE_OF,
                0.8,
                1.0,
                ReviewStatus.VERIFIED,
                evidence_fragment_id=verified_ids[0],
            ),
        ),
        unit_assertions=(
            UnitAssertionEntry(
                uuid4(),
                unit_id,
                concept_b,
                AssertionType.INTRODUCES,
                1.0,
                1.0,
                ReviewStatus.VERIFIED,
                evidence_fragment_id=verified_ids[1],
            ),
        ),
    )
    OntologyImporter(repository).import_manifest(manifest)
    return draft_id, manifest.ontology_version


@pytest.mark.integration
def test_atomic_knowledge_build_keeps_last_valid_graph_active() -> None:
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER")
    password = os.getenv("NEO4J_TEST_PASSWORD")
    if not all((uri, user, password, os.getenv("ENGLISH7_DATABASE_URL"))):
        pytest.skip("Knowledge graph integration environment is not configured")

    command.upgrade(Config("alembic.ini"), "head")
    sessions = get_session_factory()
    sql = SQLAlchemyKnowledgeRepository(lambda: sessions())
    draft_id, ontology_version = _seed_curriculum(sql)
    driver = GraphDatabase.driver(uri, auth=(user, password))
    neo4j = VersionedNeo4jRepository(driver)
    builder = ProjectionEmbeddingBuilder(DeterministicEmbedder(), batch_size=2)
    build_ids = []
    try:
        service = KnowledgeGraphBuildService(
            sql, neo4j, builder, index_timeout_seconds=30
        )
        first = service.build(ontology_version)
        build_ids.append(first.build.id)

        assert first.build.status is GraphBuildStatus.ACTIVE
        assert first.validation_report is not None
        assert first.validation_report.counts["fragments"] == 2
        assert first.validation_report.valid
        with driver.session() as session:
            draft_count = session.run(
                "MATCH (fragment:SourceFragment "
                "{build_id: $build_id, sql_id: $draft_id}) "
                "RETURN count(fragment) AS count",
                build_id=str(first.build.id),
                draft_id=str(draft_id),
            ).single()["count"]
            bad_provenance = session.run(
                "MATCH ()-[rel {build_id: $build_id}]->() "
                "WHERE rel.assertion_id IS NOT NULL AND "
                "(rel.created_by IS NULL OR rel.ontology_version IS NULL OR "
                "rel.review_status <> 'verified') "
                "RETURN count(rel) AS count",
                build_id=str(first.build.id),
            ).single()["count"]
        assert draft_count == 0
        assert bad_provenance == 0

        with sessions() as session, session.begin():
            draft = session.get(SourceFragment, draft_id)
            draft.review_status = ReviewStatus.VERIFIED.value
            draft.is_published = True

        failing = KnowledgeGraphBuildService(
            sql,
            InvalidatingRepository(neo4j),
            builder,
            index_timeout_seconds=30,
        )
        with pytest.raises(GraphBuildValidationError):
            failing.build(ontology_version)

        with sessions() as session:
            failed = session.scalar(
                select(GraphBuild)
                .where(GraphBuild.status == GraphBuildStatus.FAILED.value)
                .order_by(GraphBuild.created_at.desc())
            )
            assert failed is not None
            build_ids.append(failed.id)
        assert sql.get_build(first.build.id).status is GraphBuildStatus.ACTIVE
    finally:
        for build_id in build_ids:
            neo4j.delete_build(build_id)
        driver.close()
