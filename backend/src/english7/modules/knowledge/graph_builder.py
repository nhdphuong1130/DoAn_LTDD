from collections.abc import Iterable

from english7.db.models import ReviewStatus
from english7.modules.knowledge.contracts import (
    Embedder,
    FragmentForIndexing,
    IndexedFragment,
    KnowledgeGraphRepository,
)


class GraphBuilder:
    def __init__(
        self, repository: KnowledgeGraphRepository, embedder: Embedder
    ) -> None:
        self._repository = repository
        self._embedder = embedder

    def build(self, fragments: Iterable[FragmentForIndexing]) -> int:
        indexed_count = 0
        for fragment in fragments:
            if fragment.review_status is not ReviewStatus.VERIFIED:
                continue
            indexed = IndexedFragment(
                fragment_id=fragment.fragment_id,
                textbook_id=fragment.textbook_id,
                unit_id=fragment.unit_id,
                section_id=fragment.section_id,
                activity_id=fragment.activity_id,
                unit_number=fragment.unit_number,
                text=fragment.normalized_text,
                pdf_page=fragment.pdf_page,
                printed_page=fragment.printed_page,
                embedding=self._embedder.embed(fragment.normalized_text),
                hierarchy=(
                    fragment.textbook_title,
                    f"Unit {fragment.unit_number}: {fragment.unit_title}",
                    fragment.section_title,
                    str(fragment.activity_id),
                ),
            )
            self._repository.upsert_fragment(indexed)
            indexed_count += 1
        return indexed_count
