import os
from uuid import UUID, uuid4

import pytest
from neo4j import GraphDatabase

from english7.modules.knowledge.contracts import (
    ConceptNode,
    ConceptRelation,
    FragmentAssertion,
    FragmentNode,
    KnowledgeProjection,
    StructuralNode,
    UnitAssertion,
)
from english7.modules.knowledge.embedding import EmbeddingIdentity
from english7.modules.knowledge.neo4j_repository import (
    ProjectionEmbeddings,
    VersionedNeo4jRepository,
)


def _projection() -> KnowledgeProjection:
    textbook, unit, section, activity = (uuid4() for _ in range(4))
    fragment_a, fragment_b, concept_a, concept_b = (uuid4() for _ in range(4))
    provenance = (1.0, 1.0, None, "integration", None, "test-v1", None, None)
    return KnowledgeProjection.create(
        ontology_version="test-v1",
        textbooks=(StructuralNode(textbook, "Textbook", {"title": "English 7"}),),
        units=(
            StructuralNode(
                unit,
                "Unit",
                {"textbook_id": str(textbook), "number": 1, "title": "Hobbies"},
            ),
        ),
        sections=(
            StructuralNode(
                section,
                "Section",
                {"unit_id": str(unit), "title": "Getting Started"},
            ),
        ),
        activities=(
            StructuralNode(
                activity,
                "Activity",
                {"section_id": str(section), "number": "1"},
            ),
        ),
        fragments=(
            FragmentNode(
                fragment_a, textbook, unit, section, activity,
                "My hobby is collecting dolls.", 12, 10, {},
            ),
            FragmentNode(
                fragment_b, textbook, unit, section, activity,
                "I collect dolls every weekend.", 13, 11, {},
            ),
        ),
        concepts=(
            ConceptNode(concept_a, "topic", "Hobbies", "hobbies", {}),
            ConceptNode(
                concept_b, "grammar", "Present simple", "present simple", {}
            ),
        ),
        fragment_assertions=(
            FragmentAssertion(
                uuid4(), fragment_a, concept_a, "teaches", *provenance
            ),
        ),
        concept_relations=(
            ConceptRelation(
                uuid4(), concept_a, concept_b, "prerequisite_of", 1.0, 1.0,
                fragment_a, None, "integration", None, "test-v1", None, None,
            ),
        ),
        unit_assertions=(
            UnitAssertion(
                uuid4(), unit, concept_b, "introduces", 1.0, 1.0,
                fragment_b, None, "integration", None, "test-v1", None, None,
            ),
        ),
    )


def _embeddings(projection: KnowledgeProjection, first: float) -> ProjectionEmbeddings:
    return ProjectionEmbeddings(
        {
            item.id: [first, float(position)]
            for position, item in enumerate(projection.fragments, start=1)
        },
        {
            item.id: [first, float(position)]
            for position, item in enumerate(projection.concepts, start=1)
        },
    )


@pytest.mark.integration
def test_build_scoped_projection_validation_and_vector_isolation() -> None:
    uri = os.getenv("NEO4J_TEST_URI")
    user = os.getenv("NEO4J_TEST_USER")
    password = os.getenv("NEO4J_TEST_PASSWORD")
    if not all((uri, user, password)):
        pytest.skip("Neo4j integration environment is not configured")

    identity = EmbeddingIdentity("fake", "fake", "v1", 2, "", "", "v1")
    first_build, second_build = uuid4(), uuid4()
    first, second = _projection(), _projection()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    repository = VersionedNeo4jRepository(driver)
    try:
        for build_id, projection, marker in (
            (first_build, first, 1.0),
            (second_build, second, -1.0),
        ):
            repository.prepare_build(build_id, identity)
            repository.write_projection(
                build_id, projection, _embeddings(projection, marker)
            )
            repository.wait_until_online(build_id, timeout_seconds=30)

        report = repository.validate_build(
            first_build, first.expected_counts, dimensions=identity.dimensions
        )
        report.require_valid()
        fragment_results = repository.query_vector_index(
            first_build, kind="fragment", vector=[1.0, 1.0], top_k=10
        )
        concept_results = repository.query_vector_index(
            first_build, kind="concept", vector=[1.0, 1.0], top_k=10
        )

        assert {UUID(item["sql_id"]) for item in fragment_results} == {
            item.id for item in first.fragments
        }
        assert {UUID(item["sql_id"]) for item in concept_results} == {
            item.id for item in first.concepts
        }
        assert not (
            {item.id for item in second.fragments}
            & {UUID(item["sql_id"]) for item in fragment_results}
        )
        assert report.relationship_counts["TEACHES"] == 1
        assert report.relationship_counts["PREREQUISITE_OF"] == 1
        assert report.relationship_counts["INTRODUCES"] == 1
    finally:
        repository.delete_build(first_build)
        repository.delete_build(second_build)
        driver.close()
