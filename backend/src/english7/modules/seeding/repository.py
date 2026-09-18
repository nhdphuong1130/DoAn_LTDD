from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.db.models import (
    Activity,
    AudioTrack,
    AuditEvent,
    MediaAsset,
    Section,
    SourceDocument,
    SourceFragment,
    Textbook,
    Unit,
)
from english7.modules.seeding.manifest import SeedManifest


class SQLAlchemySeedRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def apply(self, manifest: SeedManifest) -> bool:
        with self._session_factory() as session, session.begin():
            imported = session.scalar(
                select(AuditEvent.id).where(
                    AuditEvent.action == "seed_import",
                    AuditEvent.entity_type == "seed_package",
                    AuditEvent.entity_id == manifest.package_id,
                )
            )
            if imported is not None:
                return False

            session.merge(
                Textbook(
                    id=manifest.textbook.id,
                    title=manifest.textbook.title,
                    is_active=True,
                )
            )
            session.merge(
                SourceDocument(
                    id=manifest.source.id,
                    textbook_id=manifest.textbook.id,
                    original_filename=manifest.source.filename,
                    object_key=manifest.source.object_key,
                    file_hash=manifest.source.sha256,
                    page_count=manifest.source.page_count,
                    ingestion_version=manifest.source.ingestion_version,
                )
            )
            units_by_number = {}
            for item in manifest.units:
                units_by_number[item.number] = item.id
                session.merge(
                    Unit(
                        id=item.id,
                        textbook_id=manifest.textbook.id,
                        number=item.number,
                        title=item.title,
                        is_published=True,
                    )
                )
            for item in manifest.sections:
                session.merge(
                    Section(
                        id=item.id,
                        unit_id=units_by_number[item.unit_number],
                        title=item.title,
                        section_type=item.section_type,
                        position=item.position,
                    )
                )
            for item in manifest.activities:
                session.merge(
                    Activity(
                        id=item.id,
                        section_id=item.section_id,
                        number=item.number,
                        activity_type=item.activity_type,
                        instruction=item.instruction,
                    )
                )
            for item in manifest.fragments:
                session.merge(
                    SourceFragment(
                        id=item.id,
                        source_document_id=item.source_document_id,
                        activity_id=item.activity_id,
                        pdf_page=item.pdf_page,
                        printed_page=item.printed_page,
                        region_type=item.region_type,
                        x=item.x,
                        y=item.y,
                        width=item.width,
                        height=item.height,
                        ocr_text=item.normalized_text,
                        normalized_text=item.normalized_text,
                        review_status=item.review_status.value,
                        is_published=item.is_published,
                    )
                )
            for item in manifest.audio:
                session.merge(
                    MediaAsset(
                        id=item.media_asset_id,
                        object_key=item.object_key,
                        bucket=item.bucket,
                        mime_type=item.mime_type,
                        size_bytes=item.size_bytes,
                        checksum=item.checksum,
                    )
                )
                session.merge(
                    AudioTrack(
                        id=item.id,
                        activity_id=item.activity_id,
                        media_asset_id=item.media_asset_id,
                        track_number=item.track_number,
                    )
                )
            session.add(
                AuditEvent(
                    action="seed_import",
                    entity_type="seed_package",
                    entity_id=manifest.package_id,
                    event_data={"manifest": manifest.to_dict()},
                )
            )
            return True

    def get_manifest(self, package_id: UUID) -> SeedManifest | None:
        with self._session_factory() as session:
            event_data = session.scalar(
                select(AuditEvent.event_data).where(
                    AuditEvent.action == "seed_import",
                    AuditEvent.entity_type == "seed_package",
                    AuditEvent.entity_id == package_id,
                )
            )
            if event_data is None:
                return None
            return SeedManifest.from_dict(event_data["manifest"])
