from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.api.errors import ApplicationError
from english7.db.models import (
    AuditEvent,
    ConceptRelationAssertion,
    FragmentConceptAssertion,
    KnowledgeConcept,
    ReviewStatus,
    SourceFragment,
    UnitConceptAssertion,
)
from english7.modules.knowledge.ontology_manifest import OntologyManifest


class SQLAlchemyKnowledgeRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def verified_fragment_ids(
        self, requested: frozenset[UUID]
    ) -> frozenset[UUID]:
        if not requested:
            return frozenset()
        with self._session_factory() as session:
            return frozenset(
                session.scalars(
                    select(SourceFragment.id).where(
                        SourceFragment.id.in_(requested),
                        SourceFragment.review_status == ReviewStatus.VERIFIED.value,
                        SourceFragment.is_published == True,
                    )
                )
            )

    def apply_ontology(self, manifest: OntologyManifest) -> bool:
        checksum = manifest.checksum()
        with self._session_factory() as session, session.begin():
            existing = session.scalar(
                select(AuditEvent).where(
                    AuditEvent.action == "ontology_import",
                    AuditEvent.entity_type == "ontology_manifest",
                    AuditEvent.entity_id == manifest.manifest_id,
                )
            )
            if existing is not None:
                if existing.event_data.get("checksum") != checksum:
                    raise ApplicationError(
                        "ontology_manifest_conflict",
                        "Ontology manifest ID already has different content",
                        409,
                    )
                return False

            for item in manifest.concepts:
                session.merge(
                    KnowledgeConcept(
                        id=item.id,
                        concept_type=item.concept_type.value,
                        canonical_name=item.canonical_name,
                        description_en=item.description_en,
                        description_vi=item.description_vi,
                        concept_text=item.concept_text,
                        ontology_version=manifest.ontology_version,
                        review_status=item.review_status.value,
                        concept_properties=item.properties,
                        created_by=manifest.created_by,
                        model_version=item.model_version,
                        reviewer_id=item.reviewer_id,
                        reviewed_at=item.reviewed_at,
                    )
                )
            for item in manifest.fragment_assertions:
                row = FragmentConceptAssertion(
                    id=item.id,
                    fragment_id=item.fragment_id,
                    concept_id=item.concept_id,
                    assertion_type=item.assertion_type.value,
                    role_weight=item.role_weight,
                    confidence=item.confidence,
                    review_status=item.review_status.value,
                    evidence_reference=item.evidence_reference,
                    created_by=manifest.created_by,
                    model_version=item.model_version,
                    ontology_version=manifest.ontology_version,
                    reviewer_id=item.reviewer_id,
                    reviewed_at=item.reviewed_at,
                )
                row.validate_scores()
                session.merge(row)
            for item in manifest.concept_relations:
                row = ConceptRelationAssertion(
                    id=item.id,
                    source_concept_id=item.source_concept_id,
                    target_concept_id=item.target_concept_id,
                    assertion_type=item.assertion_type.value,
                    role_weight=item.role_weight,
                    confidence=item.confidence,
                    review_status=item.review_status.value,
                    evidence_fragment_id=item.evidence_fragment_id,
                    evidence_reference=item.evidence_reference,
                    created_by=manifest.created_by,
                    model_version=item.model_version,
                    ontology_version=manifest.ontology_version,
                    reviewer_id=item.reviewer_id,
                    reviewed_at=item.reviewed_at,
                )
                row.validate_scores()
                session.merge(row)
            for item in manifest.unit_assertions:
                row = UnitConceptAssertion(
                    id=item.id,
                    unit_id=item.unit_id,
                    concept_id=item.concept_id,
                    assertion_type=item.assertion_type.value,
                    role_weight=item.role_weight,
                    confidence=item.confidence,
                    review_status=item.review_status.value,
                    evidence_fragment_id=item.evidence_fragment_id,
                    evidence_reference=item.evidence_reference,
                    created_by=manifest.created_by,
                    model_version=item.model_version,
                    ontology_version=manifest.ontology_version,
                    reviewer_id=item.reviewer_id,
                    reviewed_at=item.reviewed_at,
                )
                row.validate_scores()
                session.merge(row)
            session.add(
                AuditEvent(
                    action="ontology_import",
                    entity_type="ontology_manifest",
                    entity_id=manifest.manifest_id,
                    event_data={
                        "checksum": checksum,
                        "ontology_version": manifest.ontology_version,
                        "concept_count": len(manifest.concepts),
                        "fragment_assertion_count": len(
                            manifest.fragment_assertions
                        ),
                        "concept_relation_count": len(manifest.concept_relations),
                        "unit_assertion_count": len(manifest.unit_assertions),
                    },
                )
            )
            return True
