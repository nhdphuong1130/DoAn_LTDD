from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class EmbeddingIdentity:
    provider: str
    model: str
    model_version: str
    dimensions: int
    query_prefix: str
    passage_prefix: str
    preprocessing_version: str

    def __post_init__(self) -> None:
        if self.dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive")
        for field in (
            "provider",
            "model",
            "model_version",
            "preprocessing_version",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"Embedding {field} is required")


class BatchEmbedder(Protocol):
    identity: EmbeddingIdentity

    def embed_query(self, text: str) -> list[float]: ...

    def embed_documents(self, texts: Sequence[str]) -> tuple[list[float], ...]: ...


class EmbeddingModel(Protocol):
    def embed(self, documents: Iterable[str], *, batch_size: int): ...


def _fastembed_model_factory(**kwargs: Any):
    from fastembed import TextEmbedding

    return TextEmbedding(**kwargs)


class FastEmbedService:
    def __init__(
        self,
        *,
        identity: EmbeddingIdentity,
        cache_dir: Path,
        batch_size: int = 32,
        model_factory: Callable[..., EmbeddingModel] = _fastembed_model_factory,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("Embedding batch size must be positive")
        self.identity = identity
        self._cache_dir = cache_dir
        self._batch_size = batch_size
        self._model_factory = model_factory
        self._model_instance: EmbeddingModel | None = None
        self._initialization_lock = Lock()

    def _model(self) -> EmbeddingModel:
        if self._model_instance is None:
            with self._initialization_lock:
                if self._model_instance is None:
                    self._model_instance = self._model_factory(
                        model_name=self.identity.model,
                        cache_dir=str(self._cache_dir),
                    )
        return self._model_instance

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = " ".join(text.split())
        if not normalized:
            raise ValueError("Embedding input must not be empty")
        return normalized

    def _prepare(self, text: str, prefix: str) -> str:
        normalized = self._normalize(text)
        normalized_prefix = " ".join(prefix.split())
        if not normalized_prefix:
            return normalized
        if normalized == normalized_prefix or normalized.startswith(
            normalized_prefix + " "
        ):
            return normalized
        return f"{normalized_prefix} {normalized}"

    def _validate_vector(self, vector: Iterable[float]) -> list[float]:
        values = [float(value) for value in vector]
        if len(values) != self.identity.dimensions:
            raise ValueError(
                "Embedding vector must contain "
                f"{self.identity.dimensions} dimensions, got {len(values)}"
            )
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Embedding vector values must be finite")
        return values

    def _embed(self, texts: Sequence[str], prefix: str) -> tuple[list[float], ...]:
        if not texts:
            return ()
        prepared = [self._prepare(text, prefix) for text in texts]
        vectors = tuple(
            self._validate_vector(vector)
            for vector in self._model().embed(
                prepared,
                batch_size=self._batch_size,
            )
        )
        if len(vectors) != len(prepared):
            raise ValueError("Embedding model returned an unexpected vector count")
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed((text,), self.identity.query_prefix)[0]

    def embed_documents(self, texts: Sequence[str]) -> tuple[list[float], ...]:
        return self._embed(texts, self.identity.passage_prefix)
