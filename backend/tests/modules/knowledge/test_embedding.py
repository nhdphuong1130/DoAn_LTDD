from pathlib import Path

import pytest

from english7.modules.knowledge.embedding import (
    EmbeddingIdentity,
    FastEmbedService,
)


class RecordingModel:
    def __init__(self, batches: list[list[list[float]]]) -> None:
        self._batches = iter(batches)
        self.calls: list[list[str]] = []

    def embed(self, documents, *, batch_size):
        self.calls.append(list(documents))
        return iter(next(self._batches))


def identity(**overrides) -> EmbeddingIdentity:
    values = {
        "provider": "fastembed",
        "model": "fake-model",
        "model_version": "v1",
        "dimensions": 4,
        "query_prefix": "",
        "passage_prefix": "",
        "preprocessing_version": "v1",
    }
    values.update(overrides)
    return EmbeddingIdentity(**values)


def service(model: RecordingModel, **identity_overrides) -> FastEmbedService:
    return FastEmbedService(
        identity=identity(**identity_overrides),
        cache_dir=Path("cache"),
        batch_size=2,
        model_factory=lambda **_: model,
    )


def test_rejects_wrong_vector_dimensions() -> None:
    embedder = service(RecordingModel([[[0.1, 0.2]]]))

    with pytest.raises(ValueError, match="4 dimensions"):
        embedder.embed_query("hobby")


def test_query_and_document_prefixes_are_normalized_and_applied_once() -> None:
    model = RecordingModel(
        [
            [[[1.0, 0.0, 0.0, 0.0]][0]],
            [[[0.0, 1.0, 0.0, 0.0]][0]],
            [[[0.0, 0.0, 1.0, 0.0]][0]],
        ]
    )
    embedder = service(
        model,
        query_prefix="query: ",
        passage_prefix="passage: ",
    )

    embedder.embed_query("  sở   thích  ")
    embedder.embed_documents([" collecting   stamps "])
    embedder.embed_query("query: already prefixed")

    assert model.calls == [
        ["query: sở thích"],
        ["passage: collecting stamps"],
        ["query: already prefixed"],
    ]


def test_document_embeddings_preserve_input_order() -> None:
    model = RecordingModel(
        [[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]]
    )

    vectors = service(model).embed_documents(["first", "second"])

    assert vectors == ([1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0])


def test_rejects_non_finite_vector_values() -> None:
    embedder = service(RecordingModel([[[0.0, float("nan"), 0.0, 0.0]]]))

    with pytest.raises(ValueError, match="finite"):
        embedder.embed_query("hobby")
