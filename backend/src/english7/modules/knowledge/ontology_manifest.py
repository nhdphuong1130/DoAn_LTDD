from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import UUID

from english7.db.models import ReviewStatus
from english7.modules.knowledge.domain import AssertionType, ConceptType


class OntologyValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ConceptEntry:
    id: UUID
    concept_type: ConceptType
    canonical_name: str
    description_en: str | None
    description_vi: str | None
    concept_text: str
    review_status: ReviewStatus
    properties: dict[str, Any]
    model_version: str | None = None
    reviewer_id: UUID | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class FragmentAssertionEntry:
    id: UUID
    fragment_id: UUID
    concept_id: UUID
    assertion_type: AssertionType
    role_weight: float
    confidence: float
    review_status: ReviewStatus
    evidence_reference: str | None = None
    model_version: str | None = None
    reviewer_id: UUID | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ConceptRelationEntry:
    id: UUID
    source_concept_id: UUID
    target_concept_id: UUID
    assertion_type: AssertionType
    role_weight: float
    confidence: float
    review_status: ReviewStatus
    evidence_fragment_id: UUID | None = None
    evidence_reference: str | None = None
    model_version: str | None = None
    reviewer_id: UUID | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class UnitAssertionEntry:
    id: UUID
    unit_id: UUID
    concept_id: UUID
    assertion_type: AssertionType
    role_weight: float
    confidence: float
    review_status: ReviewStatus
    evidence_fragment_id: UUID | None = None
    evidence_reference: str | None = None
    model_version: str | None = None
    reviewer_id: UUID | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class OntologyManifest:
    schema_version: int
    manifest_id: UUID
    ontology_version: str
    created_by: str
    concepts: tuple[ConceptEntry, ...]
    fragment_assertions: tuple[FragmentAssertionEntry, ...]
    concept_relations: tuple[ConceptRelationEntry, ...]
    unit_assertions: tuple[UnitAssertionEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), default=str))

    def checksum(self) -> str:
        canonical = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def verified_evidence_fragment_ids(self) -> frozenset[UUID]:
        fragment_ids = {
            item.fragment_id
            for item in self.fragment_assertions
            if item.review_status is ReviewStatus.VERIFIED
        }
        fragment_ids.update(
            item.evidence_fragment_id
            for item in (*self.concept_relations, *self.unit_assertions)
            if item.review_status is ReviewStatus.VERIFIED
            and item.evidence_fragment_id is not None
        )
        return frozenset(fragment_ids)

    def validate(self) -> None:
        if self.schema_version != 1:
            raise OntologyValidationError(
                "ontology_schema_unsupported", "Ontology schema version is unsupported"
            )
        if not self.ontology_version.strip() or not self.created_by.strip():
            raise OntologyValidationError(
                "ontology_metadata_invalid", "Ontology metadata is incomplete"
            )
        entries = (
            *self.concepts,
            *self.fragment_assertions,
            *self.concept_relations,
            *self.unit_assertions,
        )
        ids = [item.id for item in entries]
        if len(ids) != len(set(ids)):
            raise OntologyValidationError(
                "ontology_duplicate_id", "Ontology entity IDs must be unique"
            )

        concept_ids = {item.id for item in self.concepts}
        references = [
            item.concept_id
            for item in (*self.fragment_assertions, *self.unit_assertions)
        ]
        references.extend(
            concept_id
            for item in self.concept_relations
            for concept_id in (item.source_concept_id, item.target_concept_id)
        )
        if any(reference not in concept_ids for reference in references):
            raise OntologyValidationError(
                "ontology_reference_invalid", "Ontology references an unknown concept"
            )

        assertions = (
            *self.fragment_assertions,
            *self.concept_relations,
            *self.unit_assertions,
        )
        for item in assertions:
            for field in ("role_weight", "confidence"):
                value = getattr(item, field)
                if not math.isfinite(value) or not 0 <= value <= 1:
                    raise OntologyValidationError(
                        "ontology_score_invalid",
                        f"Ontology assertion {field} must be finite and between zero and one",
                    )
        for item in self.concept_relations:
            if (
                item.assertion_type is AssertionType.PREREQUISITE_OF
                and item.source_concept_id == item.target_concept_id
            ):
                raise OntologyValidationError(
                    "ontology_invalid_prerequisite",
                    "A concept cannot be its own prerequisite",
                )
        for item in (*self.concept_relations, *self.unit_assertions):
            if (
                item.review_status is ReviewStatus.VERIFIED
                and item.evidence_fragment_id is None
                and not (item.evidence_reference or "").strip()
            ):
                raise OntologyValidationError(
                    "ontology_evidence_required",
                    "Verified assertions require evidence",
                )

    @staticmethod
    def _datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OntologyManifest:
        def common(item: dict[str, Any]) -> dict[str, Any]:
            return {
                "model_version": item.get("model_version"),
                "reviewer_id": UUID(item["reviewer_id"])
                if item.get("reviewer_id")
                else None,
                "reviewed_at": cls._datetime(item.get("reviewed_at")),
            }

        manifest = cls(
            schema_version=int(data["schema_version"]),
            manifest_id=UUID(data["manifest_id"]),
            ontology_version=str(data["ontology_version"]),
            created_by=str(data["created_by"]),
            concepts=tuple(
                ConceptEntry(
                    id=UUID(item["id"]),
                    concept_type=ConceptType(item["concept_type"]),
                    canonical_name=str(item["canonical_name"]),
                    description_en=item.get("description_en"),
                    description_vi=item.get("description_vi"),
                    concept_text=str(item["concept_text"]),
                    review_status=ReviewStatus(item["review_status"]),
                    properties=dict(item.get("properties", {})),
                    **common(item),
                )
                for item in data.get("concepts", [])
            ),
            fragment_assertions=tuple(
                FragmentAssertionEntry(
                    id=UUID(item["id"]),
                    fragment_id=UUID(item["fragment_id"]),
                    concept_id=UUID(item["concept_id"]),
                    assertion_type=AssertionType(item["assertion_type"]),
                    role_weight=float(item["role_weight"]),
                    confidence=float(item["confidence"]),
                    review_status=ReviewStatus(item["review_status"]),
                    evidence_reference=item.get("evidence_reference"),
                    **common(item),
                )
                for item in data.get("fragment_assertions", [])
            ),
            concept_relations=tuple(
                ConceptRelationEntry(
                    id=UUID(item["id"]),
                    source_concept_id=UUID(item["source_concept_id"]),
                    target_concept_id=UUID(item["target_concept_id"]),
                    assertion_type=AssertionType(item["assertion_type"]),
                    role_weight=float(item["role_weight"]),
                    confidence=float(item["confidence"]),
                    review_status=ReviewStatus(item["review_status"]),
                    evidence_fragment_id=UUID(item["evidence_fragment_id"])
                    if item.get("evidence_fragment_id")
                    else None,
                    evidence_reference=item.get("evidence_reference"),
                    **common(item),
                )
                for item in data.get("concept_relations", [])
            ),
            unit_assertions=tuple(
                UnitAssertionEntry(
                    id=UUID(item["id"]),
                    unit_id=UUID(item["unit_id"]),
                    concept_id=UUID(item["concept_id"]),
                    assertion_type=AssertionType(item["assertion_type"]),
                    role_weight=float(item["role_weight"]),
                    confidence=float(item["confidence"]),
                    review_status=ReviewStatus(item["review_status"]),
                    evidence_fragment_id=UUID(item["evidence_fragment_id"])
                    if item.get("evidence_fragment_id")
                    else None,
                    evidence_reference=item.get("evidence_reference"),
                    **common(item),
                )
                for item in data.get("unit_assertions", [])
            ),
        )
        manifest.validate()
        return manifest

    @classmethod
    def load(cls, path: Path) -> OntologyManifest:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
