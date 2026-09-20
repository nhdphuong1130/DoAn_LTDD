from dataclasses import dataclass
from uuid import UUID

from english7.modules.knowledge.contracts import (
    ConceptNode,
    FragmentAssertion,
    FragmentNode,
    KnowledgeProjection,
    StructuralNode,
)
from english7.modules.knowledge.embedding import EmbeddingIdentity
from english7.modules.knowledge.neo4j_repository import (
    BuildIdentifiers,
    ProjectionEmbeddings,
    VersionedNeo4jRepository,
)

BUILD_ID = UUID("11111111-2222-4333-8444-555555555555")
TEXTBOOK_ID = UUID("10000000-0000-4000-8000-000000000001")
UNIT_ID = UUID("20000000-0000-4000-8000-000000000001")
SECTION_ID = UUID("30000000-0000-4000-8000-000000000001")
ACTIVITY_ID = UUID("40000000-0000-4000-8000-000000000001")
FRAGMENT_ID = UUID("50000000-0000-4000-8000-000000000001")
CONCEPT_ID = UUID("60000000-0000-4000-8000-000000000001")


@dataclass
class Call:
    query: str
    parameters: dict


class Result:
    def consume(self):
        return None


class Transaction:
    def __init__(self, calls: list[Call]) -> None:
        self.calls = calls

    def run(self, query, parameters=None, **kwargs):
        self.calls.append(Call(query, parameters or kwargs))
        return Result()


class Session:
    def __init__(self, calls: list[Call]) -> None:
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute_write(self, function, *args):
        return function(Transaction(self.calls), *args)

    def run(self, query, parameters=None, **kwargs):
        self.calls.append(Call(query, parameters or kwargs))
        return Result()


class Driver:
    def __init__(self) -> None:
        self.calls: list[Call] = []

    def session(self, **_kwargs):
        return Session(self.calls)


def projection() -> KnowledgeProjection:
    return KnowledgeProjection.create(
        ontology_version="v1",
        textbooks=(StructuralNode(TEXTBOOK_ID, "Textbook", {"title": "English 7"}),),
        units=(
            StructuralNode(
                UNIT_ID,
                "Unit",
                {"textbook_id": str(TEXTBOOK_ID), "number": 1, "title": "Hobbies"},
            ),
        ),
        sections=(
            StructuralNode(
                SECTION_ID,
                "Section",
                {"unit_id": str(UNIT_ID), "title": "Getting Started"},
            ),
        ),
        activities=(
            StructuralNode(
                ACTIVITY_ID,
                "Activity",
                {"section_id": str(SECTION_ID), "number": "1"},
            ),
        ),
        fragments=(
            FragmentNode(
                FRAGMENT_ID,
                TEXTBOOK_ID,
                UNIT_ID,
                SECTION_ID,
                ACTIVITY_ID,
                "My hobby is collecting dolls.",
                12,
                10,
                {},
            ),
        ),
        concepts=(
            ConceptNode(CONCEPT_ID, "grammar", "Present Simple", "present simple", {}),
        ),
        fragment_assertions=(
            FragmentAssertion(
                UUID("70000000-0000-4000-8000-000000000001"),
                FRAGMENT_ID,
                CONCEPT_ID,
                "teaches",
                1.0,
                1.0,
                None,
                "reviewer",
                None,
                "v1",
                None,
                None,
            ),
        ),
    )


def test_build_identifiers_are_derived_from_uuid_and_safe() -> None:
    names = BuildIdentifiers.from_build_id(BUILD_ID)

    assert names.fragment_label == (
        "SourceFragmentBuild_11111111222243338444555555555555"
    )
    assert names.fragment_index == (
        "fragment_embedding_11111111222243338444555555555555"
    )


def test_projection_write_always_parameters_build_id() -> None:
    driver = Driver()
    repository = VersionedNeo4jRepository(driver)
    embeddings = ProjectionEmbeddings(
        {FRAGMENT_ID: [1.0, 0.0]}, {CONCEPT_ID: [0.0, 1.0]}
    )

    repository.write_projection(BUILD_ID, projection(), embeddings)

    assert driver.calls
    assert all("$build_id" in call.query for call in driver.calls)
    assert all(call.parameters["build_id"] == str(BUILD_ID) for call in driver.calls)


def test_projection_write_never_uses_unrestricted_variable_traversal() -> None:
    driver = Driver()
    repository = VersionedNeo4jRepository(driver)

    repository.write_projection(
        BUILD_ID,
        projection(),
        ProjectionEmbeddings(
            {FRAGMENT_ID: [1.0, 0.0]}, {CONCEPT_ID: [0.0, 1.0]}
        ),
    )

    assert all("[*" not in call.query for call in driver.calls)


def test_prepare_build_uses_configured_embedding_dimensions() -> None:
    driver = Driver()
    repository = VersionedNeo4jRepository(driver)
    identity = EmbeddingIdentity("fake", "model", "v1", 384, "", "", "v1")

    repository.prepare_build(BUILD_ID, identity)

    index_queries = [call.query for call in driver.calls if "VECTOR INDEX" in call.query]
    assert len(index_queries) == 2
    assert all("`vector.dimensions`: 384" in query for query in index_queries)
