from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from english7.api.errors import ApplicationError
from english7.db.base import Base
from english7.db.models import (
    Activity,
    FragmentConceptAssertion,
    GraphBuild,
    KnowledgeConcept,
    ReviewStatus,
    Section,
    SourceDocument,
    SourceFragment,
    Textbook,
    Unit,
)
from english7.modules.knowledge.contracts import (
    ConceptNode,
    FragmentNode,
    KnowledgeProjection,
    StructuralNode,
)
from english7.modules.knowledge.domain import GraphBuildStatus
from english7.modules.knowledge.embedding import EmbeddingIdentity
from english7.modules.knowledge.sql_repository import SQLAlchemyKnowledgeRepository


def repository_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return SQLAlchemyKnowledgeRepository(factory), factory


def seed_projection_rows(factory):
    textbook_id = uuid4()
    unit_id = uuid4()
    section_id = uuid4()
    activity_id = uuid4()
    document_id = uuid4()
    verified_id = uuid4()
    draft_id = uuid4()
    verified_concept_id = uuid4()
    draft_concept_id = uuid4()
    verified_assertion_id = uuid4()
    draft_assertion_id = uuid4()
    with factory() as session, session.begin():
        session.add(Textbook(id=textbook_id, title="English 7", is_active=True))
        session.add(
            Unit(
                id=unit_id,
                textbook_id=textbook_id,
                number=1,
                title="Hobbies",
                is_published=True,
            )
        )
        session.add(
            Section(
                id=section_id,
                unit_id=unit_id,
                title="Getting Started",
                section_type="lesson",
                position=1,
            )
        )
        session.add(
            Activity(
                id=activity_id,
                section_id=section_id,
                number="1",
                activity_type="reading",
                instruction="Read",
            )
        )
        session.add(
            SourceDocument(
                id=document_id,
                textbook_id=textbook_id,
                original_filename="book.pdf",
                object_key="sources/book.pdf",
                file_hash="hash",
                page_count=100,
                ingestion_version="v1",
            )
        )
        for fragment_id, status, published, text in (
            (verified_id, ReviewStatus.VERIFIED.value, True, "verified text"),
            (draft_id, ReviewStatus.DRAFT.value, False, "draft text"),
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
        for concept_id, status, name in (
            (verified_concept_id, ReviewStatus.VERIFIED.value, "Present Simple"),
            (draft_concept_id, ReviewStatus.DRAFT.value, "Draft concept"),
        ):
            session.add(
                KnowledgeConcept(
                    id=concept_id,
                    concept_type="grammar",
                    canonical_name=name,
                    concept_text=name,
                    ontology_version="english7-v1",
                    review_status=status,
                    concept_properties={},
                    created_by="reviewer",
                )
            )
        session.add_all(
            [
                FragmentConceptAssertion(
                    id=verified_assertion_id,
                    fragment_id=verified_id,
                    concept_id=verified_concept_id,
                    assertion_type="teaches",
                    role_weight=1,
                    confidence=1,
                    review_status=ReviewStatus.VERIFIED.value,
                    created_by="reviewer",
                    ontology_version="english7-v1",
                ),
                FragmentConceptAssertion(
                    id=draft_assertion_id,
                    fragment_id=draft_id,
                    concept_id=draft_concept_id,
                    assertion_type="teaches",
                    role_weight=1,
                    confidence=1,
                    review_status=ReviewStatus.DRAFT.value,
                    created_by="model",
                    ontology_version="english7-v1",
                ),
            ]
        )
    return verified_id, verified_concept_id, verified_assertion_id


def test_projection_excludes_draft_fragments_concepts_and_assertions() -> None:
    repository, factory = repository_fixture()
    fragment_id, concept_id, assertion_id = seed_projection_rows(factory)

    projection = repository.load_projection("english7-v1")

    assert {item.id for item in projection.fragments} == {fragment_id}
    assert {item.id for item in projection.concepts} == {concept_id}
    assert {item.id for item in projection.fragment_assertions} == {assertion_id}


def test_projection_checksum_is_stable_across_input_order() -> None:
    structural = [
        StructuralNode(uuid4(), "Unit", {"title": "B"}),
        StructuralNode(uuid4(), "Unit", {"title": "A"}),
    ]
    fragments = [
        FragmentNode(
            uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), "text", 1, None, {}
        )
    ]
    concepts = [
        ConceptNode(uuid4(), "grammar", "Present Simple", "text", {})
    ]

    first = KnowledgeProjection.create(
        ontology_version="v1",
        units=structural,
        fragments=fragments,
        concepts=concepts,
    )
    second = KnowledgeProjection.create(
        ontology_version="v1",
        units=reversed(structural),
        fragments=fragments,
        concepts=concepts,
    )

    assert first.source_checksum == second.source_checksum
    assert first.units == second.units


def test_activation_retires_only_previous_active_build() -> None:
    repository, factory = repository_fixture()
    identity = EmbeddingIdentity("fake", "model", "v1", 2, "", "", "v1")
    projection = KnowledgeProjection.create(ontology_version="v1")
    old = repository.start_build(projection, identity)
    other = repository.start_build(projection, identity)
    new = repository.start_build(projection, identity)
    with factory() as session, session.begin():
        session.get(GraphBuild, old.id).status = GraphBuildStatus.ACTIVE.value
        session.get(GraphBuild, other.id).status = GraphBuildStatus.RETIRED.value
        session.get(GraphBuild, new.id).status = GraphBuildStatus.VALIDATED.value

    repository.activate_build(new.id)

    assert repository.get_build(new.id).status is GraphBuildStatus.ACTIVE
    assert repository.get_build(old.id).status is GraphBuildStatus.RETIRED
    assert repository.get_build(other.id).status is GraphBuildStatus.RETIRED


def test_activation_rejects_unvalidated_build() -> None:
    repository, _factory = repository_fixture()
    identity = EmbeddingIdentity("fake", "model", "v1", 2, "", "", "v1")
    projection = KnowledgeProjection.create(ontology_version="v1")
    build = repository.start_build(projection, identity)

    with pytest.raises(ApplicationError) as captured:
        repository.activate_build(build.id)

    assert captured.value.code == "graph_build_not_validated"
