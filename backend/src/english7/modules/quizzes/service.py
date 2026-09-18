from typing import Protocol
from uuid import UUID

from english7.modules.quizzes.blueprint import BlueprintSelector
from english7.modules.quizzes.domain import GeneratedQuestion, QuizDraft
from english7.modules.quizzes.validator import QuestionValidator


class QuestionGenerator(Protocol):
    def generate(
        self, *, duration_minutes: int, difficulty: str, question_count: int
    ) -> list[GeneratedQuestion]: ...


class QuizRepository(Protocol):
    def create(
        self,
        *,
        user_id: UUID,
        blueprint_id: UUID,
        duration_minutes: int,
        difficulty: str,
        questions: tuple[GeneratedQuestion, ...],
    ) -> QuizDraft: ...


class QuizService:
    def __init__(
        self,
        selector: BlueprintSelector,
        generator: QuestionGenerator,
        validator: QuestionValidator,
        repository: QuizRepository,
    ) -> None:
        self._selector = selector
        self._generator = generator
        self._validator = validator
        self._repository = repository

    def generate(
        self, user_id: UUID, duration_minutes: int, difficulty: str
    ) -> QuizDraft:
        blueprint = self._selector.select(duration_minutes)
        count = blueprint.question_count(duration_minutes)
        questions = self._validator.validate(
            self._generator.generate(
                duration_minutes=duration_minutes,
                difficulty=difficulty,
                question_count=count,
            )
        )
        return self._repository.create(
            user_id=user_id,
            blueprint_id=blueprint.id,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            questions=questions,
        )
