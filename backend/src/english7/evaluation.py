import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    id: str
    query: str
    expected_units: frozenset[int]
    expected_pages: frozenset[int]
    in_scope: bool


@dataclass(frozen=True, slots=True)
class EvaluationObservation:
    retrieved_units: frozenset[int]
    retrieved_pages: frozenset[int]
    citation_pages: frozenset[int]
    answered: bool
    refused: bool


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    total: int
    retrieval_accuracy: float
    citation_correctness: float
    grounded_answer_success: float
    out_of_scope_refusal: float


def _ratio(successes: int, total: int) -> float:
    return successes / total if total else 1.0


def evaluate(
    cases: Iterable[EvaluationCase],
    observations: Mapping[str, EvaluationObservation],
) -> EvaluationReport:
    items = tuple(cases)
    in_scope = tuple(item for item in items if item.in_scope)
    out_of_scope = tuple(item for item in items if not item.in_scope)
    retrieval_hits = citation_hits = grounded_hits = refusal_hits = 0
    for item in in_scope:
        observed = observations.get(item.id)
        if observed is None:
            continue
        retrieval_ok = (
            bool(item.expected_units & observed.retrieved_units)
            and bool(item.expected_pages & observed.retrieved_pages)
        )
        citation_ok = (
            bool(observed.citation_pages)
            and observed.citation_pages.issubset(observed.retrieved_pages)
            and bool(item.expected_pages & observed.citation_pages)
        )
        retrieval_hits += int(retrieval_ok)
        citation_hits += int(citation_ok)
        grounded_hits += int(
            retrieval_ok and citation_ok and observed.answered and not observed.refused
        )
    for item in out_of_scope:
        observed = observations.get(item.id)
        refusal_hits += int(
            observed is not None and observed.refused and not observed.answered
        )
    return EvaluationReport(
        total=len(items),
        retrieval_accuracy=_ratio(retrieval_hits, len(in_scope)),
        citation_correctness=_ratio(citation_hits, len(in_scope)),
        grounded_answer_success=_ratio(grounded_hits, len(in_scope)),
        out_of_scope_refusal=_ratio(refusal_hits, len(out_of_scope)),
    )


def _load_cases(path: Path) -> list[EvaluationCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvaluationCase(
            id=item["id"],
            query=item["query"],
            expected_units=frozenset(item["expected_units"]),
            expected_pages=frozenset(item["expected_pages"]),
            in_scope=item["in_scope"],
        )
        for item in payload
    ]


def _load_observations(path: Path) -> dict[str, EvaluationObservation]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["id"]: EvaluationObservation(
            retrieved_units=frozenset(item["retrieved_units"]),
            retrieved_pages=frozenset(item["retrieved_pages"]),
            citation_pages=frozenset(item["citation_pages"]),
            answered=item["answered"],
            refused=item["refused"],
        )
        for item in payload
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(_load_cases(args.cases), _load_observations(args.observations))
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()
