from collections.abc import Callable
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import Float, case, cast, select
from sqlalchemy.orm import Session

from english7.db.models import (
    Activity,
    AuditEvent,
    AudioTrack,
    ReviewStatus,
    Section,
    SourceFragment,
    Unit,
)
from english7.modules.textbooks.domain import (
    TextbookActivityDetail,
    TextbookAudioTrack,
    TextbookFragment,
    TextbookSectionDetail,
    TextbookUnit,
    TextbookUnitStructure,
)


class TextbookRepository(Protocol):
    def list_published_units(self, offset: int, limit: int) -> list[TextbookUnit]: ...

    def list_published_fragments(
        self,
        unit_id: UUID,
        offset: int,
        limit: int,
    ) -> list[TextbookFragment]: ...

    def get_unit_structure(self, unit_id: UUID) -> TextbookUnitStructure | None: ...

    def get_fragment(self, fragment_id: UUID) -> TextbookFragment | None: ...

    def save_fragment(self, fragment: TextbookFragment) -> TextbookFragment: ...

    def add_audit_event(self, event: dict[str, Any]) -> None: ...


class SQLAlchemyTextbookRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fragment(row: tuple[Any, ...]) -> TextbookFragment:
        if len(row) == 2:
            fragment, unit_id = row
            return TextbookFragment(
                id=fragment.id,
                unit_id=unit_id,
                pdf_page=fragment.pdf_page,
                printed_page=fragment.printed_page,
                normalized_text=fragment.normalized_text,
                review_status=ReviewStatus(fragment.review_status),
                is_published=fragment.is_published,
                reviewer_id=fragment.reviewer_id,
            )
        fragment, unit_id, section_id, section_title, act_id, act_num, act_type, act_inst = row
        return TextbookFragment(
            id=fragment.id,
            unit_id=unit_id,
            pdf_page=fragment.pdf_page,
            printed_page=fragment.printed_page,
            normalized_text=fragment.normalized_text,
            review_status=ReviewStatus(fragment.review_status),
            is_published=fragment.is_published,
            reviewer_id=fragment.reviewer_id,
            section_id=section_id,
            section_title=section_title,
            activity_id=act_id,
            activity_number=act_num,
            activity_type=act_type,
            activity_instruction=act_inst,
        )

    def list_published_units(self, offset: int, limit: int) -> list[TextbookUnit]:
        with self._session_factory() as session:
            order_expr = case(
                (Unit.title.ilike("%Review 1%"), 3.5),
                (Unit.title.ilike("%Review 2%"), 6.5),
                (Unit.title.ilike("%Review 3%"), 9.5),
                (Unit.title.ilike("%Review 4%"), 12.5),
                else_=cast(Unit.number, Float),
            )
            rows = session.scalars(
                select(Unit)
                .where(Unit.is_published == True)
                .order_by(order_expr)
                .offset(offset)
                .limit(limit)
            ).all()
            return [
                TextbookUnit(row.id, row.number, row.title, row.is_published)
                for row in rows
            ]

    def _fragment_query(self):
        return (
            select(
                SourceFragment,
                Unit.id,
                Section.id,
                Section.title,
                Activity.id,
                Activity.number,
                Activity.activity_type,
                Activity.instruction,
            )
            .join(Activity, SourceFragment.activity_id == Activity.id)
            .join(Section, Activity.section_id == Section.id)
            .join(Unit, Section.unit_id == Unit.id)
        )

    def list_published_fragments(
        self,
        unit_id: UUID,
        offset: int,
        limit: int,
    ) -> list[TextbookFragment]:
        with self._session_factory() as session:
            rows = session.execute(
                self._fragment_query()
                .where(
                    Unit.id == unit_id,
                    SourceFragment.is_published == True,
                    SourceFragment.review_status == ReviewStatus.VERIFIED,
                )
                .order_by(SourceFragment.pdf_page, SourceFragment.y, SourceFragment.x)
                .offset(offset)
                .limit(limit)
            ).all()
            return [self._fragment(row) for row in rows]

    def get_unit_structure(self, unit_id: UUID) -> TextbookUnitStructure | None:
        with self._session_factory() as session:
            unit = session.scalar(
                select(Unit).where(Unit.id == unit_id, Unit.is_published == True)
            )
            if not unit:
                return None

            sections = session.scalars(
                select(Section)
                .where(Section.unit_id == unit_id)
                .order_by(Section.position)
            ).all()

            section_details: list[TextbookSectionDetail] = []
            for sec in sections:
                activities = session.scalars(
                    select(Activity)
                    .where(Activity.section_id == sec.id)
                    .order_by(Activity.number)
                ).all()

                act_details: list[TextbookActivityDetail] = []
                for act in activities:
                    frags = session.scalars(
                        select(SourceFragment)
                        .where(
                            SourceFragment.activity_id == act.id,
                            SourceFragment.is_published == True,
                            SourceFragment.review_status == ReviewStatus.VERIFIED.value,
                        )
                        .order_by(
                            SourceFragment.pdf_page,
                            SourceFragment.y,
                            SourceFragment.x,
                        )
                    ).all()

                    frag_models = [
                        TextbookFragment(
                            id=f.id,
                            unit_id=unit.id,
                            pdf_page=f.pdf_page,
                            printed_page=f.printed_page,
                            normalized_text=f.normalized_text,
                            review_status=ReviewStatus(f.review_status),
                            is_published=f.is_published,
                            reviewer_id=f.reviewer_id,
                            section_id=sec.id,
                            section_title=sec.title,
                            activity_id=act.id,
                            activity_number=act.number,
                            activity_type=act.activity_type,
                            activity_instruction=act.instruction,
                        )
                        for f in frags
                    ]
                    audio_tracks = session.scalars(
                        select(AudioTrack)
                        .where(AudioTrack.activity_id == act.id)
                        .order_by(AudioTrack.track_number)
                    ).all()
                    track_models = [
                        TextbookAudioTrack(
                            id=t.id,
                            track_number=t.track_number,
                            audio_url=f"/api/v1/media/audio/{t.track_number}",
                        )
                        for t in audio_tracks
                    ]
                    act_details.append(
                        TextbookActivityDetail(
                            id=act.id,
                            section_id=sec.id,
                            number=act.number,
                            activity_type=act.activity_type,
                            instruction=act.instruction,
                            fragments=frag_models,
                            audio_tracks=track_models,
                        )
                    )
                section_details.append(
                    TextbookSectionDetail(
                        id=sec.id,
                        unit_id=unit.id,
                        title=sec.title,
                        section_type=sec.section_type,
                        position=sec.position,
                        activities=act_details,
                    )
                )

            return TextbookUnitStructure(
                id=unit.id,
                number=unit.number,
                title=unit.title,
                is_published=unit.is_published,
                sections=section_details,
            )

    def get_fragment(self, fragment_id: UUID) -> TextbookFragment | None:
        with self._session_factory() as session:
            row = session.execute(
                self._fragment_query().where(SourceFragment.id == fragment_id)
            ).first()
            return self._fragment(row) if row else None

    def save_fragment(self, fragment: TextbookFragment) -> TextbookFragment:
        with self._session_factory() as session:
            model = session.get(SourceFragment, fragment.id)
            if model is None:
                raise RuntimeError("Source fragment disappeared during update")
            model.normalized_text = fragment.normalized_text
            model.review_status = fragment.review_status
            model.is_published = fragment.is_published
            model.reviewer_id = fragment.reviewer_id
            session.commit()
        return fragment

    def add_audit_event(self, event: dict[str, Any]) -> None:
        with self._session_factory() as session:
            session.add(
                AuditEvent(
                    actor_id=event["actor_id"],
                    action=event["action"],
                    entity_type=event["entity_type"],
                    entity_id=event["entity_id"],
                    event_data=event["event_data"],
                )
            )
            session.commit()

