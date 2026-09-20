from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from english7.modules.knowledge.contracts import Embedder
from english7.modules.retrieval.reranker import (
    reciprocal_rank_fusion,
    weighted_reciprocal_rank_fusion,
)


@dataclass(frozen=True, slots=True)
class RetrievalCandidate:
    fragment_id: UUID
    unit_number: int
    text: str
    pdf_page: int
    printed_page: int | None
    vector_score: float
    has_verified_source: bool
    hierarchy: tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class Citation:
    fragment_id: UUID
    pdf_page: int
    printed_page: int | None


@dataclass(frozen=True, slots=True)
class GroundedContext:
    fragments: tuple[RetrievalCandidate, ...]
    citations: tuple[Citation, ...]


class RetrievalRepository(Protocol):
    def vector_search(
        self, query_vector: list[float], top_k: int
    ) -> list[RetrievalCandidate]: ...

    def expand(
        self, fragment_ids: tuple[UUID, ...], max_depth: int
    ) -> list[RetrievalCandidate]: ...


class RetrievalService:
    def __init__(
        self,
        *,
        repository: RetrievalRepository,
        embedder: Embedder,
        allowed_units: frozenset[int],
        top_k: int,
        min_vector_score: float,
        graph_depth: int,
        rrf_constant: int,
        max_context_fragments: int,
    ) -> None:
        if not allowed_units:
            raise ValueError("At least one allowed unit is required")
        if top_k <= 0 or graph_depth <= 0 or max_context_fragments <= 0:
            raise ValueError("Retrieval limits must be positive")
        self._repository = repository
        self._embedder = embedder
        self._allowed_units = allowed_units
        self._top_k = top_k
        self._threshold = min_vector_score
        self._graph_depth = graph_depth
        self._rrf_constant = rrf_constant
        self._max_context = max_context_fragments

    def _allowed(self, item: RetrievalCandidate) -> bool:
        return item.unit_number in self._allowed_units and item.has_verified_source

    def retrieve(self, query: str) -> GroundedContext:
        vector = [
            item
            for item in self._repository.vector_search(
                self._embedder.embed(query), self._top_k
            )
            if self._allowed(item) and item.vector_score >= self._threshold
        ]
        if not vector:
            return GroundedContext((), ())

        if hasattr(self._repository, "weighted_graph_search"):
            graph_results = [
                (item, weight)
                for item, weight in self._repository.weighted_graph_search(
                    tuple(item.fragment_id for item in vector), self._graph_depth
                )
                if self._allowed(item)
            ]
            by_id = {str(item.fragment_id): item for item in vector}
            for item, _ in graph_results:
                by_id[str(item.fragment_id)] = item
            fused = weighted_reciprocal_rank_fusion(
                vector_ids=tuple(str(item.fragment_id) for item in vector),
                graph_scored_ids=tuple(
                    (str(item.fragment_id), weight) for item, weight in graph_results
                ),
                rank_constant=self._rrf_constant,
            )
        else:
            graph = [
                item
                for item in self._repository.expand(
                    tuple(item.fragment_id for item in vector), self._graph_depth
                )
                if self._allowed(item)
            ]
            by_id = {str(item.fragment_id): item for item in (*vector, *graph)}
            fused = reciprocal_rank_fusion(
                vector_ids=tuple(str(item.fragment_id) for item in vector),
                graph_ids=tuple(str(item.fragment_id) for item in graph),
                rank_constant=self._rrf_constant,
            )

        fragments = tuple(
            by_id[item.item_id] for item in fused[: self._max_context]
        )
        seen_pages: set[tuple[int, int | None]] = set()
        citations: list[Citation] = []
        for fragment in fragments:
            page_key = (fragment.pdf_page, fragment.printed_page)
            if page_key in seen_pages:
                continue
            seen_pages.add(page_key)
            citations.append(
                Citation(
                    fragment.fragment_id,
                    fragment.pdf_page,
                    fragment.printed_page,
                )
            )
        return GroundedContext(fragments, tuple(citations))
