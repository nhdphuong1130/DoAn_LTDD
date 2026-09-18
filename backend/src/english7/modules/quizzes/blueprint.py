from typing import Protocol

from english7.api.errors import ApplicationError
from english7.modules.quizzes.domain import QuizBlueprintPolicy


class BlueprintRepository(Protocol):
    def list_active(self) -> list[QuizBlueprintPolicy]: ...


class BlueprintSelector:
    def __init__(self, repository: BlueprintRepository) -> None:
        self._repository = repository

    def select(self, duration_minutes: int) -> QuizBlueprintPolicy:
        policies = self._repository.list_active()
        exact = [
            policy
            for policy in policies
            if policy.mode == "preset"
            and policy.minimum_minutes == duration_minutes
            and policy.maximum_minutes == duration_minutes
        ]
        if exact:
            return exact[0]
        custom = [
            policy
            for policy in policies
            if policy.mode == "custom"
            and policy.minimum_minutes <= duration_minutes <= policy.maximum_minutes
        ]
        if custom:
            return custom[0]
        raise ApplicationError(
            "invalid_quiz_duration",
            "No active quiz policy supports this duration",
            422,
        )

    def list_policies(self) -> list[QuizBlueprintPolicy]:
        return self._repository.list_active()
