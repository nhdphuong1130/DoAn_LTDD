from dataclasses import replace
from uuid import UUID

import pytest

from english7.api.errors import ApplicationError
from english7.db.models import ReviewStatus
from english7.modules.knowledge.domain import AssertionType, ConceptType
from english7.modules.knowledge.ontology_importer import OntologyImporter
from english7.modules.knowledge.ontology_manifest import (
    ConceptEntry,
    ConceptRelationEntry,
    FragmentAssertionEntry,
    OntologyManifest,
    UnitAssertionEntry,
)

MANIFEST_ID = UUID("10000000-0000-4000-8000-000000000001")
FRAGMENT_ID = UUID("20000000-0000-4000-8000-000000000001")
UNIT_ID = UUID("30000000-0000-4000-8000-000000000001")
FOUNDATION_ID = UUID("40000000-0000-4000-8000-000000000001")
TARGET_ID = UUID("40000000-0000-4000-8000-000000000002")
ASSERTION_ID = UUID("50000000-0000-4000-8000-000000000001")
RELATION_ID = UUID("60000000-0000-4000-8000-000000000001")
UNIT_ASSERTION_ID = UUID("70000000-0000-4000-8000-000000000001")


class FakeOntologyRepository:
    def __init__(self, verified_fragment_ids: set[UUID]) -> None:
        self._verified = verified_fragment_ids
        self._manifests: dict[UUID, str] = {}

    def verified_fragment_ids(self, requested: frozenset[UUID]) -> frozenset[UUID]:
        return frozenset(requested & self._verified)

    def apply_ontology(self, manifest: OntologyManifest) -> bool:
        checksum = manifest.checksum()
        previous = self._manifests.get(manifest.manifest_id)
        if previous is not None and previous != checksum:
            raise ApplicationError(
                "ontology_manifest_conflict", "Manifest ID has different content", 409
            )
        if previous is not None:
            return False
        self._manifests[manifest.manifest_id] = checksum
        return True


def concept(concept_id: UUID, name: str) -> ConceptEntry:
    return ConceptEntry(
        id=concept_id,
        concept_type=ConceptType.GRAMMAR,
        canonical_name=name,
        description_en=name,
        description_vi=name,
        concept_text=name,
        review_status=ReviewStatus.VERIFIED,
        properties={},
    )


def valid_manifest() -> OntologyManifest:
    return OntologyManifest(
        schema_version=1,
        manifest_id=MANIFEST_ID,
        ontology_version="english7-v1",
        created_by="human-review",
        concepts=(
            concept(FOUNDATION_ID, "Verb be"),
            concept(TARGET_ID, "Present Simple"),
        ),
        fragment_assertions=(
            FragmentAssertionEntry(
                id=ASSERTION_ID,
                fragment_id=FRAGMENT_ID,
                concept_id=TARGET_ID,
                assertion_type=AssertionType.TEACHES,
                role_weight=1.0,
                confidence=1.0,
                review_status=ReviewStatus.VERIFIED,
            ),
        ),
        concept_relations=(
            ConceptRelationEntry(
                id=RELATION_ID,
                source_concept_id=FOUNDATION_ID,
                target_concept_id=TARGET_ID,
                assertion_type=AssertionType.PREREQUISITE_OF,
                role_weight=0.8,
                confidence=1.0,
                review_status=ReviewStatus.VERIFIED,
                evidence_reference="curriculum-review:english7-v1",
            ),
        ),
        unit_assertions=(
            UnitAssertionEntry(
                id=UNIT_ASSERTION_ID,
                unit_id=UNIT_ID,
                concept_id=TARGET_ID,
                assertion_type=AssertionType.INTRODUCES,
                role_weight=1.0,
                confidence=1.0,
                review_status=ReviewStatus.VERIFIED,
                evidence_fragment_id=FRAGMENT_ID,
            ),
        ),
    )


def test_import_rejects_verified_assertion_with_unverified_fragment() -> None:
    repository = FakeOntologyRepository(verified_fragment_ids=set())

    with pytest.raises(ApplicationError) as captured:
        OntologyImporter(repository).import_manifest(valid_manifest())

    assert captured.value.code == "ontology_evidence_not_verified"


def test_import_is_idempotent_by_manifest_id_and_checksum() -> None:
    repository = FakeOntologyRepository(verified_fragment_ids={FRAGMENT_ID})
    importer = OntologyImporter(repository)

    assert importer.import_manifest(valid_manifest()).created is True
    assert importer.import_manifest(valid_manifest()).created is False


def test_reusing_manifest_id_with_changed_content_is_rejected() -> None:
    repository = FakeOntologyRepository(verified_fragment_ids={FRAGMENT_ID})
    importer = OntologyImporter(repository)
    importer.import_manifest(valid_manifest())
    changed = replace(valid_manifest(), created_by="different-review")

    with pytest.raises(ApplicationError) as captured:
        importer.import_manifest(changed)

    assert captured.value.code == "ontology_manifest_conflict"


def test_prerequisite_self_cycle_is_rejected() -> None:
    relation = replace(
        valid_manifest().concept_relations[0],
        target_concept_id=FOUNDATION_ID,
    )
    item = replace(valid_manifest(), concept_relations=(relation,))

    with pytest.raises(ApplicationError) as captured:
        OntologyImporter(FakeOntologyRepository({FRAGMENT_ID})).import_manifest(item)

    assert captured.value.code == "ontology_invalid_prerequisite"


def test_missing_concept_reference_is_rejected() -> None:
    missing = UUID("40000000-0000-4000-8000-999999999999")
    assertion = replace(
        valid_manifest().fragment_assertions[0], concept_id=missing
    )
    item = replace(valid_manifest(), fragment_assertions=(assertion,))

    with pytest.raises(ApplicationError) as captured:
        OntologyImporter(FakeOntologyRepository({FRAGMENT_ID})).import_manifest(item)

    assert captured.value.code == "ontology_reference_invalid"


def test_non_finite_assertion_score_is_rejected() -> None:
    assertion = replace(valid_manifest().fragment_assertions[0], confidence=float("nan"))
    item = replace(valid_manifest(), fragment_assertions=(assertion,))

    with pytest.raises(ApplicationError) as captured:
        OntologyImporter(FakeOntologyRepository({FRAGMENT_ID})).import_manifest(item)

    assert captured.value.code == "ontology_score_invalid"
