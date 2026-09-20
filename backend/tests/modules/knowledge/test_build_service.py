from dataclasses import replace
from uuid import UUID

import pytest

from english7.modules.knowledge.build_service import (
    GraphBuildValidationError,
    KnowledgeGraphBuildService,
)
from english7.modules.knowledge.contracts import (
    ConceptNode,
    FragmentNode,
    GraphBuildRecord,
    KnowledgeProjection,
)
from english7.modules.knowledge.domain import GraphBuildStatus
from english7.modules.knowledge.embedding import EmbeddingIdentity
from english7.modules.knowledge.graph_builder import ProjectionEmbeddingBuilder
from english7.modules.knowledge.neo4j_repository import Neo4jBuildReport

OLD_BUILD_ID = UUID("10000000-0000-4000-8000-000000000001")
NEW_BUILD_ID = UUID("20000000-0000-4000-8000-000000000001")
FRAGMENT_ID = UUID("30000000-0000-4000-8000-000000000001")
CONCEPT_ID = UUID("40000000-0000-4000-8000-000000000001")


def projection() -> KnowledgeProjection:
    return KnowledgeProjection.create(
        ontology_version="english7-v1",
        fragments=(
            FragmentNode(
                FRAGMENT_ID,
                UUID(int=1),
                UUID(int=2),
                UUID(int=3),
                UUID(int=4),
                "  My hobby   is reading. ",
                12,
                10,
                {"unit_title": "Hobbies"},
            ),
        ),
        concepts=(
            ConceptNode(
                CONCEPT_ID,
                "grammar",
                "Present simple",
                "present simple habits",
                {
                    "description_en": "Habits and routines",
                    "description_vi": "Thói quen",
                    "aliases": ["simple present"],
                },
            ),
        ),
    )


def report(*failures: str) -> Neo4jBuildReport:
    return Neo4jBuildReport(
        counts=projection().expected_counts,
        relationship_counts={},
        orphan_counts={"structural": 0, "semantic": 0},
        dimension_mismatches=0,
        non_verified=0,
        duplicate_ids=0,
        index_states={},
        failures=failures,
    )


class FakeSQL:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.active_build_id = OLD_BUILD_ID
        self.builds: list[GraphBuildRecord] = []

    def load_projection(self, ontology_version: str) -> KnowledgeProjection:
        assert ontology_version == "english7-v1"
        return projection()

    def start_build(self, value, identity) -> GraphBuildRecord:
        self.events.append("start")
        build = GraphBuildRecord(
            NEW_BUILD_ID,
            value.source_checksum,
            value.ontology_version,
            GraphBuildStatus.BUILDING,
            value.expected_counts,
            None,
            None,
            None,
        )
        self.builds.append(build)
        return build

    def mark_validated(self, build_id, validation_report) -> None:
        self.events.append("mark_validated")
        self.builds[-1] = replace(
            self.builds[-1],
            status=GraphBuildStatus.VALIDATED,
            validation_report=validation_report,
        )

    def activate_build(self, build_id) -> None:
        self.events.append("activate")
        self.active_build_id = build_id
        self.builds[-1] = replace(self.builds[-1], status=GraphBuildStatus.ACTIVE)

    def mark_failed(self, build_id, failure_code) -> None:
        self.events.append("mark_failed")
        self.builds[-1] = replace(
            self.builds[-1],
            status=GraphBuildStatus.FAILED,
            failure_code=failure_code,
        )


class FakeEmbedder:
    identity = EmbeddingIdentity("fake", "model", "v1", 2, "", "", "v1")

    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.failure: Exception | None = None

    def embed_documents(self, texts):
        self.events.append("embed")
        if self.failure:
            raise self.failure
        return tuple([float(position), 1.0] for position, _ in enumerate(texts))


class FakeNeo4j:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.validation_report = report()

    def prepare_build(self, build_id, identity) -> None:
        pass

    def write_projection(self, build_id, value, vectors) -> None:
        self.events.append("write")

    def ensure_indexes(self, build_id, identity) -> None:
        self.events.append("create_indexes")

    def wait_until_online(self, build_id, *, timeout_seconds) -> None:
        self.events.append("wait_online")

    def validate_build(self, build_id, expected_counts, *, dimensions):
        self.events.append("validate")
        return self.validation_report


def service(events: list[str]):
    sql = FakeSQL(events)
    embedder = FakeEmbedder(events)
    neo4j = FakeNeo4j(events)
    return (
        KnowledgeGraphBuildService(
            sql,
            neo4j,
            ProjectionEmbeddingBuilder(embedder, batch_size=2),
            index_timeout_seconds=5,
        ),
        sql,
        neo4j,
        embedder,
    )


def test_failed_candidate_never_replaces_active_build() -> None:
    build_service, sql, neo4j, _ = service([])
    neo4j.validation_report = report("count:fragments")

    with pytest.raises(GraphBuildValidationError):
        build_service.build("english7-v1")

    assert sql.active_build_id == OLD_BUILD_ID
    assert sql.builds[-1].status is GraphBuildStatus.FAILED
    assert sql.builds[-1].failure_code == "validation_failed"


def test_successful_build_activates_only_after_indexes_and_validation() -> None:
    events: list[str] = []
    build_service, sql, _, _ = service(events)

    result = build_service.build("english7-v1")

    assert events == [
        "start",
        "embed",
        "write",
        "create_indexes",
        "wait_online",
        "validate",
        "mark_validated",
        "activate",
    ]
    assert result.build.status is GraphBuildStatus.ACTIVE
    assert sql.active_build_id == NEW_BUILD_ID


def test_embedding_failure_marks_build_failed_without_partial_activation() -> None:
    build_service, sql, _, embedder = service([])
    embedder.failure = RuntimeError("offline")

    with pytest.raises(RuntimeError, match="offline"):
        build_service.build("english7-v1")

    assert sql.active_build_id == OLD_BUILD_ID
    assert sql.builds[-1].failure_code == "embedding_failed"


def test_embedding_inputs_are_normalized_stable_and_hashed() -> None:
    embedder = FakeEmbedder([])
    builder = ProjectionEmbeddingBuilder(embedder, batch_size=1)

    vectors = builder.embed(projection())

    assert set(vectors.fragments) == {FRAGMENT_ID}
    assert set(vectors.concepts) == {CONCEPT_ID}
    assert len(vectors.fragment_input_hashes[FRAGMENT_ID]) == 64
    assert len(vectors.concept_input_hashes[CONCEPT_ID]) == 64
