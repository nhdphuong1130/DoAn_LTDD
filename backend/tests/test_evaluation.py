from english7.evaluation import EvaluationCase, EvaluationObservation, evaluate


def test_evaluation_reports_retrieval_citation_grounding_and_refusal_metrics() -> None:
    cases = [
        EvaluationCase(
            id="unit-1-hobby",
            query="What is the speaker's hobby?",
            expected_units=frozenset({1}),
            expected_pages=frozenset({10}),
            in_scope=True,
        ),
        EvaluationCase(
            id="outside-math",
            query="Solve this algebra equation",
            expected_units=frozenset(),
            expected_pages=frozenset(),
            in_scope=False,
        ),
    ]
    observations = {
        "unit-1-hobby": EvaluationObservation(
            retrieved_units=frozenset({1}),
            retrieved_pages=frozenset({10}),
            citation_pages=frozenset({10}),
            answered=True,
            refused=False,
        ),
        "outside-math": EvaluationObservation(
            retrieved_units=frozenset(),
            retrieved_pages=frozenset(),
            citation_pages=frozenset(),
            answered=False,
            refused=True,
        ),
    }

    report = evaluate(cases, observations)

    assert report.total == 2
    assert report.retrieval_accuracy == 1.0
    assert report.citation_correctness == 1.0
    assert report.grounded_answer_success == 1.0
    assert report.out_of_scope_refusal == 1.0


def test_grounded_answer_fails_when_answer_has_no_valid_citation() -> None:
    case = EvaluationCase(
        "unit-2-health",
        "How can I stay healthy?",
        frozenset({2}),
        frozenset({20}),
        True,
    )
    observation = EvaluationObservation(
        retrieved_units=frozenset({2}),
        retrieved_pages=frozenset({20}),
        citation_pages=frozenset(),
        answered=True,
        refused=False,
    )

    report = evaluate([case], {case.id: observation})

    assert report.retrieval_accuracy == 1.0
    assert report.citation_correctness == 0.0
    assert report.grounded_answer_success == 0.0
