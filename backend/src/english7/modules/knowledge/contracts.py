import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from typing import Protocol
from uuid import UUID

from english7.db.models import ReviewStatus
from english7.modules.knowledge.domain import GraphBuildStatus


@dataclass(frozen=True, slots=True)
class FragmentForIndexing:
    fragment_id: UUID
    textbook_id: UUID
    textbook_title: str
    unit_id: UUID
    unit_number: int
    unit_title: str
    section_id: UUID
    section_title: str
    activity_id: UUID
    normalized_text: str
    pdf_page: int
    printed_page: int | None
    review_status: ReviewStatus


@dataclass(frozen=True, slots=True)
class IndexedFragment:
    fragment_id: UUID
    textbook_id: UUID
    unit_id: UUID
    section_id: UUID
    activity_id: UUID
    unit_number: int
    text: str
    pdf_page: int
    printed_page: int | None
    embedding: list[float]
    hierarchy: tuple[str, str, str, str]


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class KnowledgeGraphRepository(Protocol):
    def upsert_fragment(self, fragment: IndexedFragment) -> None: ...


@dataclass(frozen=True, slots=True)
class StructuralNode:
    id: UUID
    label: str
    properties: dict


@dataclass(frozen=True, slots=True)
class FragmentNode:
    id: UUID
    textbook_id: UUID
    unit_id: UUID
    section_id: UUID
    activity_id: UUID
    text: str
    pdf_page: int
    printed_page: int | None
    properties: dict


@dataclass(frozen=True, slots=True)
class ConceptNode:
    id: UUID
    concept_type: str
    canonical_name: str
    concept_text: str
    properties: dict


@dataclass(frozen=True, slots=True)
class FragmentAssertion:
    id: UUID
    fragment_id: UUID
    concept_id: UUID
    assertion_type: str
    role_weight: float
    confidence: float
    evidence_reference: str | None
    created_by: str
    model_version: str | None
    ontology_version: str
    reviewer_id: UUID | None
    reviewed_at: datetime | None


@dataclass(frozen=True, slots=True)
class ConceptRelation:
    id: UUID
    source_concept_id: UUID
    target_concept_id: UUID
    assertion_type: str
    role_weight: float
    confidence: float
    evidence_fragment_id: UUID | None
    evidence_reference: str | None
    created_by: str
    model_version: str | None
    ontology_version: str
    reviewer_id: UUID | None
    reviewed_at: datetime | None


@dataclass(frozen=True, slots=True)
class UnitAssertion:
    id: UUID
    unit_id: UUID
    concept_id: UUID
    assertion_type: str
    role_weight: float
    confidence: float
    evidence_fragment_id: UUID | None
    evidence_reference: str | None
    created_by: str
    model_version: str | None
    ontology_version: str
    reviewer_id: UUID | None
    reviewed_at: datetime | None


def _ordered(items: Iterable):
    return tuple(sorted(items, key=lambda item: str(item.id)))


@dataclass(frozen=True, slots=True)
class KnowledgeProjection:
    source_checksum: str
    ontology_version: str
    textbooks: tuple[StructuralNode, ...]
    units: tuple[StructuralNode, ...]
    sections: tuple[StructuralNode, ...]
    activities: tuple[StructuralNode, ...]
    fragments: tuple[FragmentNode, ...]
    concepts: tuple[ConceptNode, ...]
    fragment_assertions: tuple[FragmentAssertion, ...]
    concept_relations: tuple[ConceptRelation, ...]
    unit_assertions: tuple[UnitAssertion, ...]

    @classmethod
    def create(
        cls,
        *,
        ontology_version: str,
        textbooks: Iterable[StructuralNode] = (),
        units: Iterable[StructuralNode] = (),
        sections: Iterable[StructuralNode] = (),
        activities: Iterable[StructuralNode] = (),
        fragments: Iterable[FragmentNode] = (),
        concepts: Iterable[ConceptNode] = (),
        fragment_assertions: Iterable[FragmentAssertion] = (),
        concept_relations: Iterable[ConceptRelation] = (),
        unit_assertions: Iterable[UnitAssertion] = (),
    ) -> "KnowledgeProjection":
        values = {
            "ontology_version": ontology_version,
            "textbooks": _ordered(textbooks),
            "units": _ordered(units),
            "sections": _ordered(sections),
            "activities": _ordered(activities),
            "fragments": _ordered(fragments),
            "concepts": _ordered(concepts),
            "fragment_assertions": _ordered(fragment_assertions),
            "concept_relations": _ordered(concept_relations),
            "unit_assertions": _ordered(unit_assertions),
        }
        canonical = json.dumps(
            values,
            default=lambda value: asdict(value)
            if hasattr(value, "__dataclass_fields__")
            else str(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return cls(
            source_checksum=sha256(canonical.encode("utf-8")).hexdigest(),
            **values,
        )

    @property
    def expected_counts(self) -> dict[str, int]:
        return {
            "textbooks": len(self.textbooks),
            "units": len(self.units),
            "sections": len(self.sections),
            "activities": len(self.activities),
            "fragments": len(self.fragments),
            "concepts": len(self.concepts),
            "fragment_assertions": len(self.fragment_assertions),
            "concept_relations": len(self.concept_relations),
            "unit_assertions": len(self.unit_assertions),
        }


@dataclass(frozen=True, slots=True)
class GraphBuildRecord:
    id: UUID
    source_checksum: str
    ontology_version: str
    status: GraphBuildStatus
    expected_counts: dict[str, int]
    actual_counts: dict | None
    validation_report: dict | None
    failure_code: str | None
