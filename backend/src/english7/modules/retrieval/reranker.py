from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankedItem:
    item_id: str
    score: float


def reciprocal_rank_fusion(
    *,
    vector_ids: tuple[str, ...],
    graph_ids: tuple[str, ...],
    rank_constant: int,
) -> tuple[RankedItem, ...]:
    if rank_constant <= 0:
        raise ValueError("RRF rank constant must be positive")
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    sequence = 0
    for ranking in (vector_ids, graph_ids):
        for rank, item_id in enumerate(ranking, start=1):
            if item_id not in first_seen:
                first_seen[item_id] = sequence
                sequence += 1
            scores[item_id] = scores.get(item_id, 0.0) + 1 / (
                rank_constant + rank
            )
    ordered = sorted(scores, key=lambda key: (-scores[key], first_seen[key]))
    return tuple(RankedItem(item_id, scores[item_id]) for item_id in ordered)


def weighted_reciprocal_rank_fusion(
    *,
    vector_ids: tuple[str, ...],
    graph_scored_ids: tuple[tuple[str, float], ...],
    rank_constant: int = 60,
    vector_multiplier: float = 1.0,
    graph_multiplier: float = 1.2,
) -> tuple[RankedItem, ...]:
    if rank_constant <= 0:
        raise ValueError("RRF rank constant must be positive")
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    sequence = 0

    for rank, item_id in enumerate(vector_ids, start=1):
        if item_id not in first_seen:
            first_seen[item_id] = sequence
            sequence += 1
        scores[item_id] = scores.get(item_id, 0.0) + (
            vector_multiplier / (rank_constant + rank)
        )

    for rank, (item_id, weight) in enumerate(graph_scored_ids, start=1):
        if item_id not in first_seen:
            first_seen[item_id] = sequence
            sequence += 1
        scores[item_id] = scores.get(item_id, 0.0) + (
            graph_multiplier * weight / (rank_constant + rank)
        )

    ordered = sorted(scores, key=lambda key: (-scores[key], first_seen[key]))
    return tuple(RankedItem(item_id, scores[item_id]) for item_id in ordered)

