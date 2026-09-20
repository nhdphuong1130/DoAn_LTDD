from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from english7.api.errors import ApplicationError
from english7.db.models import (
    AuditEvent,
    Activity,
    ConceptRelationAssertion,
    FragmentConceptAssertion,
    GraphBuild,
    KnowledgeConcept,
    ReviewStatus,
    Section,
    SourceFragment,
    Textbook,
    Unit,
    UnitConceptAssertion,
)
from english7.modules.knowledge.contracts import (
    ConceptNode,
    ConceptRelation,
    FragmentAssertion,
    FragmentNode,
    GraphBuildRecord,
    KnowledgeProjection,
    StructuralNode,
    UnitAssertion,
)
from english7.modules.knowledge.domain import GraphBuildStatus
from english7.modules.knowledge.embedding import EmbeddingIdentity
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

    @staticmethod
    def _unit_metadata(number: int) -> tuple[str, float, int | None]:
        reviews = {31: (3.5, 1), 61: (6.5, 2), 91: (9.5, 3), 121: (12.5, 4)}
        if number in reviews:
            display_order, cycle = reviews[number]
            return "review", display_order, cycle
        return "regular", float(number), None

    def load_projection(self, ontology_version: str) -> KnowledgeProjection:
        with self._session_factory() as session:
            if session.get_bind().dialect.name == "mssql":
                session.connection(
                    execution_options={"isolation_level": "SERIALIZABLE"}
                )
            hierarchy_rows = session.execute(
                select(SourceFragment, Activity, Section, Unit, Textbook)
                .join(Activity, Activity.id == SourceFragment.activity_id)
                .join(Section, Section.id == Activity.section_id)
                .join(Unit, Unit.id == Section.unit_id)
                .join(Textbook, Textbook.id == Unit.textbook_id)
                .where(
                    SourceFragment.review_status == ReviewStatus.VERIFIED.value,
                    SourceFragment.is_published == True,
                )
                .order_by(SourceFragment.id)
            ).all()

            textbooks: dict[UUID, StructuralNode] = {}
            units: dict[UUID, StructuralNode] = {}
            sections: dict[UUID, StructuralNode] = {}
            activities: dict[UUID, StructuralNode] = {}
            fragments: list[FragmentNode] = []
            for fragment, activity, section, unit, textbook in hierarchy_rows:
                textbooks[textbook.id] = StructuralNode(
                    textbook.id,
                    "Textbook",
                    {"title": textbook.title},
                )
                kind, display_order, review_cycle = self._unit_metadata(unit.number)
                units[unit.id] = StructuralNode(
                    unit.id,
                    "Unit",
                    {
                        "textbook_id": str(textbook.id),
                        "number": unit.number,
                        "title": unit.title,
                        "unit_kind": kind,
                        "display_order": display_order,
                        "review_cycle": review_cycle,
                    },
                )
                sections[section.id] = StructuralNode(
                    section.id,
                    "Section",
                    {
                        "unit_id": str(unit.id),
                        "title": section.title,
                        "section_type": section.section_type,
                        "position": section.position,
                    },
                )
                activities[activity.id] = StructuralNode(
                    activity.id,
                    "Activity",
                    {
                        "section_id": str(section.id),
                        "number": activity.number,
                        "activity_type": activity.activity_type,
                        "instruction": activity.instruction,
                    },
                )
                fragments.append(
                    FragmentNode(
                        id=fragment.id,
                        textbook_id=textbook.id,
                        unit_id=unit.id,
                        section_id=section.id,
                        activity_id=activity.id,
                        text=fragment.normalized_text,
                        pdf_page=fragment.pdf_page,
                        printed_page=fragment.printed_page,
                        properties={
                            "source_document_id": str(fragment.source_document_id),
                            "region_type": fragment.region_type,
                        },
                    )
                )

            concept_rows = tuple(
                session.scalars(
                    select(KnowledgeConcept)
                    .where(
                        KnowledgeConcept.ontology_version == ontology_version,
                        KnowledgeConcept.review_status == ReviewStatus.VERIFIED.value,
                    )
                    .order_by(KnowledgeConcept.id)
                )
            )
            concepts = tuple(
                ConceptNode(
                    id=item.id,
                    concept_type=item.concept_type,
                    canonical_name=item.canonical_name,
                    concept_text=item.concept_text,
                    properties={
                        **item.concept_properties,
                        "description_en": item.description_en,
                        "description_vi": item.description_vi,
                        "model_version": item.model_version,
                    },
                )
                for item in concept_rows
            )
            fragment_rows = tuple(
                session.scalars(
                    select(FragmentConceptAssertion)
                    .where(
                        FragmentConceptAssertion.ontology_version == ontology_version,
                        FragmentConceptAssertion.review_status
                        == ReviewStatus.VERIFIED.value,
                    )
                    .order_by(FragmentConceptAssertion.id)
                )
            )
            relation_rows = tuple(
                session.scalars(
                    select(ConceptRelationAssertion)
                    .where(
                        ConceptRelationAssertion.ontology_version == ontology_version,
                        ConceptRelationAssertion.review_status
                        == ReviewStatus.VERIFIED.value,
                    )
                    .order_by(ConceptRelationAssertion.id)
                )
            )
            unit_rows = tuple(
                session.scalars(
                    select(UnitConceptAssertion)
                    .where(
                        UnitConceptAssertion.ontology_version == ontology_version,
                        UnitConceptAssertion.review_status
                        == ReviewStatus.VERIFIED.value,
                    )
                    .order_by(UnitConceptAssertion.id)
                )
            )

        fragment_ids = {item.id for item in fragments}
        concept_ids = {item.id for item in concepts}
        unit_ids = set(units)
        invalid = any(
            item.fragment_id not in fragment_ids or item.concept_id not in concept_ids
            for item in fragment_rows
        ) or any(
            item.source_concept_id not in concept_ids
            or item.target_concept_id not in concept_ids
            or (
                item.evidence_fragment_id is not None
                and item.evidence_fragment_id not in fragment_ids
            )
            for item in relation_rows
        ) or any(
            item.unit_id not in unit_ids
            or item.concept_id not in concept_ids
            or (
                item.evidence_fragment_id is not None
                and item.evidence_fragment_id not in fragment_ids
            )
            for item in unit_rows
        )
        if invalid:
            raise ApplicationError(
                "knowledge_projection_reference_invalid",
                "Verified ontology assertion references excluded graph data",
                409,
            )

        fragment_assertions = tuple(
            FragmentAssertion(
                item.id,
                item.fragment_id,
                item.concept_id,
                item.assertion_type,
                item.role_weight,
                item.confidence,
                item.evidence_reference,
                item.created_by,
                item.model_version,
                item.ontology_version,
                item.reviewer_id,
                item.reviewed_at,
            )
            for item in fragment_rows
        )
        concept_relations = tuple(
            ConceptRelation(
                item.id,
                item.source_concept_id,
                item.target_concept_id,
                item.assertion_type,
                item.role_weight,
                item.confidence,
                item.evidence_fragment_id,
                item.evidence_reference,
                item.created_by,
                item.model_version,
                item.ontology_version,
                item.reviewer_id,
                item.reviewed_at,
            )
            for item in relation_rows
        )
        unit_assertions = tuple(
            UnitAssertion(
                item.id,
                item.unit_id,
                item.concept_id,
                item.assertion_type,
                item.role_weight,
                item.confidence,
                item.evidence_fragment_id,
                item.evidence_reference,
                item.created_by,
                item.model_version,
                item.ontology_version,
                item.reviewer_id,
                item.reviewed_at,
            )
            for item in unit_rows
        )
        return KnowledgeProjection.create(
            ontology_version=ontology_version,
            textbooks=textbooks.values(),
            units=units.values(),
            sections=sections.values(),
            activities=activities.values(),
            fragments=fragments,
            concepts=concepts,
            fragment_assertions=fragment_assertions,
            concept_relations=concept_relations,
            unit_assertions=unit_assertions,
        )

    @staticmethod
    def _build_record(row: GraphBuild) -> GraphBuildRecord:
        return GraphBuildRecord(
            row.id,
            row.source_checksum,
            row.ontology_version,
            GraphBuildStatus(row.status),
            row.expected_counts,
            row.actual_counts,
            row.validation_report,
            row.failure_code,
        )

    def start_build(
        self, projection: KnowledgeProjection, identity: EmbeddingIdentity
    ) -> GraphBuildRecord:
        with self._session_factory() as session, session.begin():
            if session.get_bind().dialect.name == "mssql":
                lock_result = session.execute(
                    text(
                        "SET NOCOUNT ON; DECLARE @result int; "
                        "EXEC @result = sp_getapplock "
                        "@Resource = 'english7:knowledge-graph-build', "
                        "@LockMode = 'Exclusive', @LockOwner = 'Transaction', "
                        "@LockTimeout = 0; SET NOCOUNT OFF; SELECT @result"
                    )
                ).scalar_one()
                if int(lock_result) < 0:
                    raise ApplicationError(
                        "graph_build_in_progress",
                        "Another knowledge graph build is in progress",
                        409,
                    )

            building = session.scalar(
                select(GraphBuild)
                .where(GraphBuild.status == GraphBuildStatus.BUILDING.value)
                .with_for_update()
            )
            if building is not None:
                raise ApplicationError(
                    "graph_build_in_progress",
                    "Another knowledge graph build is in progress",
                    409,
                )
            active = session.scalar(
                select(GraphBuild).where(
                    GraphBuild.status == GraphBuildStatus.ACTIVE.value,
                    GraphBuild.source_checksum == projection.source_checksum,
                    GraphBuild.ontology_version == projection.ontology_version,
                    GraphBuild.embedding_provider == identity.provider,
                    GraphBuild.embedding_model == identity.model,
                    GraphBuild.embedding_model_version == identity.model_version,
                    GraphBuild.embedding_dimensions == identity.dimensions,
                    GraphBuild.embedding_query_prefix == identity.query_prefix,
                    GraphBuild.embedding_passage_prefix == identity.passage_prefix,
                    GraphBuild.embedding_preprocessing_version
                    == identity.preprocessing_version,
                )
            )
            if active is not None:
                return self._build_record(active)
            row = GraphBuild(
                source_checksum=projection.source_checksum,
                ontology_version=projection.ontology_version,
                embedding_provider=identity.provider,
                embedding_model=identity.model,
                embedding_model_version=identity.model_version,
                embedding_dimensions=identity.dimensions,
                embedding_query_prefix=identity.query_prefix,
                embedding_passage_prefix=identity.passage_prefix,
                embedding_preprocessing_version=identity.preprocessing_version,
                status=GraphBuildStatus.BUILDING.value,
                expected_counts=projection.expected_counts,
            )
            session.add(row)
            session.flush()
            row.fragment_index_name = f"fragment_embedding_{row.id.hex}"
            row.concept_index_name = f"concept_embedding_{row.id.hex}"
            result = self._build_record(row)
        return result

    def get_build(self, build_id: UUID) -> GraphBuildRecord | None:
        with self._session_factory() as session:
            row = session.get(GraphBuild, build_id)
            return self._build_record(row) if row is not None else None

    def mark_validated(self, build_id: UUID, report: dict) -> None:
        with self._session_factory() as session, session.begin():
            row = session.get(GraphBuild, build_id)
            if row is None:
                raise KeyError(build_id)
            row.actual_counts = dict(report.get("counts", {}))
            row.validation_report = report
            row.status = GraphBuildStatus.VALIDATED.value
            row.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, build_id: UUID, failure_code: str) -> None:
        with self._session_factory() as session, session.begin():
            row = session.get(GraphBuild, build_id)
            if row is None:
                raise KeyError(build_id)
            row.status = GraphBuildStatus.FAILED.value
            row.failure_code = failure_code
            row.completed_at = datetime.now(timezone.utc)

    def activate_build(self, build_id: UUID) -> None:
        with self._session_factory() as session, session.begin():
            candidate = session.get(GraphBuild, build_id)
            if candidate is None or candidate.status != GraphBuildStatus.VALIDATED.value:
                raise ApplicationError(
                    "graph_build_not_validated",
                    "Only a validated graph build can be activated",
                    409,
                )
            active = tuple(
                session.scalars(
                    select(GraphBuild).where(
                        GraphBuild.status == GraphBuildStatus.ACTIVE.value,
                        GraphBuild.id != build_id,
                    )
                )
            )
            now = datetime.now(timezone.utc)
            for row in active:
                row.status = GraphBuildStatus.RETIRED.value
            candidate.status = GraphBuildStatus.ACTIVE.value
            candidate.activated_at = now
