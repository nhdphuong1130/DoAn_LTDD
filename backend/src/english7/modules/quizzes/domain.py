from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class QuizBlueprintPolicy:
    id: UUID
    name: str
    minimum_minutes: int
    maximum_minutes: int
    question_rate: int
    mode: str

    def question_count(self, duration_minutes: int) -> int:
        if not self.minimum_minutes <= duration_minutes <= self.maximum_minutes:
            raise ValueError("Duration is outside the blueprint policy")
        if self.mode == "preset":
            return self.question_rate
        return duration_minutes * self.question_rate


@dataclass(frozen=True, slots=True)
class GeneratedQuestion:
    prompt: str
    answer: dict
    source_fragment_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class QuizDraft:
    id: UUID
    duration_minutes: int
    difficulty: str
    question_count: int
