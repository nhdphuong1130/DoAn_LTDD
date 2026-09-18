from typing import Protocol
from uuid import UUID

from english7.modules.quizzes.blueprint import BlueprintSelector
from english7.modules.quizzes.domain import GeneratedQuestion, QuizDraft, QuizOptions
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
        max_audio_plays: int,
    ) -> None:
        self._selector = selector
        self._generator = generator
        self._validator = validator
        self._repository = repository
        self._max_audio_plays = max_audio_plays

    def options(self) -> QuizOptions:
        policies = self._selector.list_policies()
        presets = tuple(
            sorted(
                policy.minimum_minutes
                for policy in policies
                if policy.mode == "preset"
                and policy.minimum_minutes == policy.maximum_minutes
            )
        )
        custom = [policy for policy in policies if policy.mode == "custom"]
        if not presets or len(custom) != 1:
            raise ApplicationError(
                "quiz_policy_invalid", "Active quiz policies are incomplete", 503
            )
        return QuizOptions(
            presets,
            custom[0].minimum_minutes,
            custom[0].maximum_minutes,
            self._max_audio_plays,
        )

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
