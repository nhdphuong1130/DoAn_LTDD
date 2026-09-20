from collections.abc import Iterable
from hashlib import sha256
import json

from english7.db.models import ReviewStatus
from english7.modules.knowledge.contracts import (
    Embedder,
    FragmentForIndexing,
    IndexedFragment,
    KnowledgeProjection,
    KnowledgeGraphRepository,
)
from english7.modules.knowledge.embedding import BatchEmbedder
from english7.modules.knowledge.neo4j_repository import ProjectionEmbeddings


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


class ProjectionEmbeddingBuilder:
    def __init__(self, embedder: BatchEmbedder, *, batch_size: int) -> None:
        if batch_size <= 0:
            raise ValueError("Embedding batch size must be positive")
        self._embedder = embedder
        self._batch_size = batch_size

    @property
    def identity(self):
        return self._embedder.identity

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.split())

    @classmethod
    def _fragment_input(cls, fragment) -> str:
        metadata = {
            key: fragment.properties[key]
            for key in sorted(fragment.properties)
            if key in {"unit_title", "section_title", "activity_type", "region_type"}
            and fragment.properties[key] is not None
        }
        context = json.dumps(
            metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return cls._normalize(f"evidence {context} text {fragment.text}")

    @classmethod
    def _concept_input(cls, concept) -> str:
        details = {
            key: concept.properties[key]
            for key in sorted(concept.properties)
            if key
            in {"description_en", "description_vi", "aliases", "reviewed_examples"}
            and concept.properties[key] is not None
        }
        context = json.dumps(
            details, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return cls._normalize(
            f"{concept.concept_type} {concept.canonical_name} "
            f"{concept.concept_text} {context}"
        )

    def embed(self, projection: KnowledgeProjection) -> ProjectionEmbeddings:
        items = [
            ("fragment", item.id, self._fragment_input(item))
            for item in projection.fragments
        ] + [
            ("concept", item.id, self._concept_input(item))
            for item in projection.concepts
        ]
        items.sort(key=lambda item: str(item[1]))
        fragment_vectors: dict = {}
        concept_vectors: dict = {}
        fragment_hashes: dict = {}
        concept_hashes: dict = {}
        for start in range(0, len(items), self._batch_size):
            batch = items[start : start + self._batch_size]
            vectors = self._embedder.embed_documents([item[2] for item in batch])
            if len(vectors) != len(batch):
                raise ValueError("Embedding model returned an unexpected vector count")
            for (kind, stable_id, text), vector in zip(batch, vectors, strict=True):
                target = fragment_vectors if kind == "fragment" else concept_vectors
                hashes = fragment_hashes if kind == "fragment" else concept_hashes
                target[stable_id] = vector
                hashes[stable_id] = sha256(text.encode("utf-8")).hexdigest()
        return ProjectionEmbeddings(
            fragments=fragment_vectors,
            concepts=concept_vectors,
            fragment_input_hashes=fragment_hashes,
            concept_input_hashes=concept_hashes,
        )
