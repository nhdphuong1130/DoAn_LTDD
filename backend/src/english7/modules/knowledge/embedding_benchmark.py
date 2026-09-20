from __future__ import annotations

import json
import math
import resource
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from english7.modules.knowledge.embedding import BatchEmbedder, EmbeddingIdentity


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    id: str
    query: str
    expected_candidate_ids: frozenset[str]
    expected_units: frozenset[int]


@dataclass(frozen=True, slots=True)
class BenchmarkCandidate:
    id: str
    text: str
    unit_number: int


@dataclass(frozen=True, slots=True)
class BenchmarkDataset:
    cases: tuple[BenchmarkCase, ...]
    candidates: tuple[BenchmarkCandidate, ...]

    @classmethod
    def load(cls, path: Path) -> BenchmarkDataset:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            cases=tuple(
                BenchmarkCase(
                    id=str(item["id"]),
                    query=str(item["query"]),
                    expected_candidate_ids=frozenset(item["expected_candidate_ids"]),
                    expected_units=frozenset(int(unit) for unit in item["expected_units"]),
                )
                for item in payload["cases"]
            ),
            candidates=tuple(
                BenchmarkCandidate(
                    id=str(item["id"]),
                    text=str(item["text"]),
                    unit_number=int(item["unit_number"]),
                )
                for item in payload["candidates"]
            ),
        )


@dataclass(frozen=True, slots=True)
class EmbeddingBenchmarkReport:
    identity: EmbeddingIdentity
    query_count: int
    candidate_count: int
    top_k: int
    recall_at_k: float
    unit_accuracy: float
    p50_latency_ms: float
    p95_latency_ms: float
    peak_rss_mb: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Benchmark vectors must have matching dimensions")
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _percentile(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def benchmark(
    embedder: BatchEmbedder,
    cases: Sequence[BenchmarkCase],
    candidates: Sequence[BenchmarkCandidate],
    *,
    top_k: int = 5,
    clock: Callable[[], float] = time.perf_counter,
    peak_rss_mb: float | None = None,
) -> EmbeddingBenchmarkReport:
    if not cases or not candidates:
        raise ValueError("Benchmark requires cases and candidates")
    if top_k <= 0:
        raise ValueError("Benchmark top-k must be positive")
    candidate_ids = [item.id for item in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Benchmark candidate IDs must be unique")
    known_ids = set(candidate_ids)
    if any(not item.expected_candidate_ids <= known_ids for item in cases):
        raise ValueError("Benchmark case references an unknown candidate")

    document_vectors = embedder.embed_documents([item.text for item in candidates])
    hits = unit_hits = 0
    latencies = []
    for item in cases:
        started = clock()
        query_vector = embedder.embed_query(item.query)
        latencies.append((clock() - started) * 1000)
        ranked = sorted(
            zip(candidates, document_vectors, strict=True),
            key=lambda pair: (-_cosine(query_vector, pair[1]), pair[0].id),
        )
        selected = ranked[: min(top_k, len(ranked))]
        hits += int(any(candidate.id in item.expected_candidate_ids for candidate, _ in selected))
        unit_hits += int(bool(selected) and selected[0][0].unit_number in item.expected_units)

    return EmbeddingBenchmarkReport(
        identity=embedder.identity,
        query_count=len(cases),
        candidate_count=len(candidates),
        top_k=top_k,
        recall_at_k=hits / len(cases),
        unit_accuracy=unit_hits / len(cases),
        p50_latency_ms=round(_percentile(latencies, 0.50), 6),
        p95_latency_ms=round(_percentile(latencies, 0.95), 6),
        peak_rss_mb=peak_rss_mb if peak_rss_mb is not None else _peak_rss_mb(),
    )
