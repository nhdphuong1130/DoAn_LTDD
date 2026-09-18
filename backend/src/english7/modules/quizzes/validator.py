from typing import Protocol

from english7.api.errors import ApplicationError
from english7.modules.quizzes.domain import GeneratedQuestion


class SimilarityCalculator(Protocol):
    def compare(self, left: str, right: str) -> float: ...


class QuestionValidator:
    def __init__(
        self, similarity: SimilarityCalculator, duplicate_threshold: float
    ) -> None:
        if not 0 <= duplicate_threshold <= 1:
            raise ValueError("Duplicate threshold must be between zero and one")
        self._similarity = similarity
        self._threshold = duplicate_threshold

    def validate(
        self, questions: list[GeneratedQuestion]
    ) -> tuple[GeneratedQuestion, ...]:
        for question in questions:
            if (
                not question.prompt.strip()
                or not question.answer
                or not question.source_fragment_ids
            ):
                raise ApplicationError(
                    "invalid_generated_question",
                    "Every question requires a prompt, answer, and verified source",
                    422,
                )
        for left_index, left in enumerate(questions):
            for right in questions[left_index + 1 :]:
                if self._similarity.compare(left.prompt, right.prompt) >= self._threshold:
                    raise ApplicationError(
                        "duplicate_generated_questions",
                        "Generated questions are too similar",
                        422,
                    )
        return tuple(questions)
