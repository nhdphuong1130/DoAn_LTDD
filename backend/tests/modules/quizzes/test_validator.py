from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.modules.quizzes.domain import GeneratedQuestion
from english7.modules.quizzes.validator import QuestionValidator


def question(prompt="Choose the healthy habit", answer=None, sources=None):
    return GeneratedQuestion(
        prompt=prompt,
        answer=answer if answer is not None else {"correct": "exercise"},
        source_fragment_ids=sources if sources is not None else (uuid4(),),
    )


class FakeSimilarity:
    def __init__(self, score):
        self.score = score

    def compare(self, left, right):
        return self.score


@pytest.mark.parametrize(
    "invalid",
    [
        GeneratedQuestion("Question", {}, (uuid4(),)),
        GeneratedQuestion("Question", {"correct": "answer"}, ()),
    ],
)
def test_every_question_requires_answer_and_verified_source(invalid) -> None:
    with pytest.raises(ApplicationError) as captured:
        QuestionValidator(FakeSimilarity(0), 0.85).validate([invalid])

    assert captured.value.code == "invalid_generated_question"


def test_duplicate_questions_are_rejected_by_configured_threshold() -> None:
    validator = QuestionValidator(FakeSimilarity(0.9), duplicate_threshold=0.85)

    with pytest.raises(ApplicationError) as captured:
        validator.validate([question("one"), question("two")])

    assert captured.value.code == "duplicate_generated_questions"


def test_questions_below_duplicate_threshold_are_accepted() -> None:
    items = [question("one"), question("two")]

    assert QuestionValidator(FakeSimilarity(0.8), 0.85).validate(items) == tuple(items)
