from uuid import uuid4

import pytest
from sqlalchemy import Unicode, UnicodeText

from english7.db.models import FragmentConceptAssertion, GraphBuild, KnowledgeConcept
from english7.modules.knowledge.domain import (
    ConceptType,
    GraphBuildStatus,
)


def test_concept_types_cover_the_approved_ontology() -> None:
    assert {item.value for item in ConceptType} == {
        "grammar",
        "vocabulary_sense",
        "pronunciation_feature",
        "topic",
        "skill",
    }


def test_assertion_rejects_confidence_outside_unit_interval() -> None:
    assertion = FragmentConceptAssertion(
        fragment_id=uuid4(),
        concept_id=uuid4(),
        assertion_type="teaches",
        role_weight=1.0,
        confidence=1.1,
        review_status="verified",
        created_by="human",
        ontology_version="v1",
    )

    with pytest.raises(ValueError, match="confidence"):
        assertion.validate_scores()


def test_graph_build_status_is_required_by_contract() -> None:
    assert GraphBuildStatus.ACTIVE.value == "active"
    assert GraphBuild.__table__.c.status.nullable is False


def test_knowledge_concept_uses_unicode_for_bilingual_content() -> None:
    columns = KnowledgeConcept.__table__.c

    assert isinstance(columns.canonical_name.type, Unicode)
    assert isinstance(columns.description_en.type, UnicodeText)
    assert isinstance(columns.description_vi.type, UnicodeText)
    assert isinstance(columns.concept_text.type, UnicodeText)
