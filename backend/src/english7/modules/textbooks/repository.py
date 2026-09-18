from collections.abc import Callable
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.db.models import (
    Activity,
    AuditEvent,
    ReviewStatus,
    Section,
    SourceFragment,
    Unit,
)
from english7.modules.textbooks.domain import TextbookFragment, TextbookUnit


class TextbookRepository(Protocol):
    def list_published_units(self, offset: int, limit: int) -> list[TextbookUnit]: ...

    def list_published_fragments(
        self,
        unit_id: UUID,
        offset: int,
        limit: int,
    ) -> list[TextbookFragment]: ...

    def get_fragment(self, fragment_id: UUID) -> TextbookFragment | None: ...

    def save_fragment(self, fragment: TextbookFragment) -> TextbookFragment: ...

    def add_audit_event(self, event: dict[str, Any]) -> None: ...


class SQLAlchemyTextbookRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fragment(row: tuple[SourceFragment, UUID]) -> TextbookFragment:
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

    def list_published_units(self, offset: int, limit: int) -> list[TextbookUnit]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(Unit)
                .where(Unit.is_published.is_(True))
                .order_by(Unit.number)
                .offset(offset)
                .limit(limit)
            ).all()
            return [
                TextbookUnit(row.id, row.number, row.title, row.is_published)
                for row in rows
            ]

    def _fragment_query(self):
        return (
            select(SourceFragment, Unit.id)
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
                    SourceFragment.is_published.is_(True),
                    SourceFragment.review_status == ReviewStatus.VERIFIED,
                )
                .order_by(SourceFragment.pdf_page, SourceFragment.y, SourceFragment.x)
                .offset(offset)
                .limit(limit)
            ).all()
            return [self._fragment(row) for row in rows]

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

