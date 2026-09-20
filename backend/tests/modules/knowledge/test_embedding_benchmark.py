from english7.modules.knowledge.embedding import EmbeddingIdentity
from english7.modules.knowledge.embedding_benchmark import (
    BenchmarkCandidate,
    BenchmarkCase,
    benchmark,
)


class FakeEmbedder:
    identity = EmbeddingIdentity(
        provider="fake",
        model="bilingual-test",
        model_version="v1",
        dimensions=2,
        query_prefix="",
        passage_prefix="",
        preprocessing_version="v1",
    )

    def embed_query(self, text: str) -> list[float]:
        return {
            "sở thích": [1.0, 0.0],
            "healthy habits": [0.0, 1.0],
        }[text]

    def embed_documents(self, texts) -> tuple[list[float], ...]:
        vectors = {
            "hobby evidence": [1.0, 0.0],
            "health evidence": [0.0, 1.0],
            "unrelated": [-1.0, 0.0],
        }
        return tuple(vectors[text] for text in texts)


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        self.value += 0.01
        return self.value


def test_benchmark_computes_recall_and_unit_accuracy_from_labels() -> None:
    cases = (
        BenchmarkCase("vi-hobby", "sở thích", frozenset({"f1"}), frozenset({1})),
        BenchmarkCase(
            "en-health", "healthy habits", frozenset({"f2"}), frozenset({2})
        ),
    )
    candidates = (
        BenchmarkCandidate("f1", "hobby evidence", 1),
        BenchmarkCandidate("f2", "health evidence", 2),
        BenchmarkCandidate("f3", "unrelated", 3),
    )

    report = benchmark(
        FakeEmbedder(), cases, candidates, top_k=2, clock=Clock(), peak_rss_mb=12.5
    )

    assert report.query_count == 2
    assert report.recall_at_k == 1.0
    assert report.unit_accuracy == 1.0
    assert report.p50_latency_ms == 10.0
    assert report.p95_latency_ms == 10.0
    assert report.peak_rss_mb == 12.5
