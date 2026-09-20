from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from english7.api.errors import ApplicationError
from english7.modules.knowledge.ontology_manifest import (
    OntologyManifest,
    OntologyValidationError,
)


class OntologyRepository(Protocol):
    def verified_fragment_ids(
        self, requested: frozenset[UUID]
    ) -> frozenset[UUID]: ...

    def apply_ontology(self, manifest: OntologyManifest) -> bool: ...


@dataclass(frozen=True, slots=True)
class OntologyImportResult:
    manifest_id: UUID
    created: bool
    concept_count: int
    assertion_count: int


class OntologyImporter:
    def __init__(self, repository: OntologyRepository) -> None:
        self._repository = repository

    def import_manifest(self, manifest: OntologyManifest) -> OntologyImportResult:
        try:
            manifest.validate()
        except OntologyValidationError as error:
            raise ApplicationError(error.code, str(error), 422) from error
        evidence_ids = manifest.verified_evidence_fragment_ids()
        if evidence_ids != self._repository.verified_fragment_ids(evidence_ids):
            raise ApplicationError(
                "ontology_evidence_not_verified",
                "Verified ontology assertions require verified textbook evidence",
                422,
            )
        created = self._repository.apply_ontology(manifest)
        assertion_count = (
            len(manifest.fragment_assertions)
            + len(manifest.concept_relations)
            + len(manifest.unit_assertions)
        )
        return OntologyImportResult(
            manifest.manifest_id,
            created,
            len(manifest.concepts),
            assertion_count,
        )
