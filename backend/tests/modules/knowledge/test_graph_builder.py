from uuid import uuid4

from english7.db.models import ReviewStatus
from english7.modules.knowledge.contracts import FragmentForIndexing
from english7.modules.knowledge.graph_builder import GraphBuilder


class FakeEmbedder:
    def embed(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]


class FakeGraphRepository:
    def __init__(self) -> None:
        self.indexed = []

    def upsert_fragment(self, fragment) -> None:
        self.indexed.append(fragment)


def fragment(status: ReviewStatus) -> FragmentForIndexing:
    return FragmentForIndexing(
        fragment_id=uuid4(),
        textbook_id=uuid4(),
        textbook_title="English 7 Global Success",
        unit_id=uuid4(),
        unit_number=1,
        unit_title="Hobbies",
        section_id=uuid4(),
        section_title="Getting Started",
        activity_id=uuid4(),
        normalized_text="My hobby is collecting dolls.",
        pdf_page=12,
        printed_page=10,
        review_status=status,
    )


def test_graph_builder_indexes_only_verified_fragments_with_stable_sql_ids() -> None:
    repository = FakeGraphRepository()
    builder = GraphBuilder(repository, FakeEmbedder())
    verified = fragment(ReviewStatus.VERIFIED)

    count = builder.build([verified, fragment(ReviewStatus.DRAFT)])

    assert count == 1
    assert len(repository.indexed) == 1
    indexed = repository.indexed[0]
    assert indexed.fragment_id == verified.fragment_id
    assert indexed.unit_id == verified.unit_id
    assert indexed.embedding == [float(len(verified.normalized_text)), 1.0]
    assert indexed.hierarchy == (
        "English 7 Global Success",
        "Unit 1: Hobbies",
        "Getting Started",
        str(verified.activity_id),
    )
