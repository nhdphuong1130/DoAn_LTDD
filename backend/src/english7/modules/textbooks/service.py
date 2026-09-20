from uuid import UUID

from english7.api.errors import ApplicationError
from english7.modules.textbooks.domain import (
    TextbookFragment,
    TextbookUnit,
    TextbookUnitStructure,
)
from english7.modules.textbooks.repository import TextbookRepository


class TextbookService:
    def __init__(self, repository: TextbookRepository) -> None:
        self.repository = repository

    def list_units(self, *, offset: int, limit: int) -> list[TextbookUnit]:
        return self.repository.list_published_units(offset, limit)

    def get_unit_structure(self, unit_id: UUID) -> TextbookUnitStructure:
        structure = self.repository.get_unit_structure(unit_id)
        if structure is None:
            raise ApplicationError(
                code="unit_not_found",
                message="Textbook unit was not found or is not published",
                status_code=404,
            )
        return structure

    def list_fragments(
        self,
        unit_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[TextbookFragment]:
        return self.repository.list_published_fragments(unit_id, offset, limit)

    def verify_fragment(
        self,
        fragment_id: UUID,
        *,
        corrected_text: str,
        reviewer_id: UUID,
    ) -> TextbookFragment:
        fragment = self.repository.get_fragment(fragment_id)
        if fragment is None:
            raise ApplicationError(
                code="fragment_not_found",
                message="Source fragment was not found",
                status_code=404,
            )
        if not corrected_text.strip():
            raise ApplicationError(
                code="empty_fragment_text",
                message="Verified text must not be empty",
                status_code=422,
            )
        updated = fragment.verified(
            corrected_text=corrected_text,
            reviewer_id=reviewer_id,
        )
        self.repository.save_fragment(updated)
        self.repository.add_audit_event(
            {
                "actor_id": reviewer_id,
                "action": "source_fragment.verified",
                "entity_type": "source_fragment",
                "entity_id": fragment_id,
                "event_data": {"pdf_page": updated.pdf_page},
            }
        )
        return updated

