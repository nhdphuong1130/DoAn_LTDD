from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.modules.quizzes.blueprint import BlueprintSelector
from english7.modules.quizzes.domain import QuizBlueprintPolicy


class FakeBlueprintRepository:
    def __init__(self, policies):
        self.policies = policies

    def list_active(self):
        return self.policies


def policies():
    return [
        QuizBlueprintPolicy(uuid4(), "short", 15, 15, 10, "preset"),
        QuizBlueprintPolicy(uuid4(), "standard", 45, 45, 30, "preset"),
        QuizBlueprintPolicy(uuid4(), "long", 60, 60, 40, "preset"),
        QuizBlueprintPolicy(uuid4(), "custom", 10, 90, 1, "custom"),
    ]


@pytest.mark.parametrize("duration", [15, 45, 60])
def test_configured_preset_duration_selects_exact_policy(duration) -> None:
    selected = BlueprintSelector(FakeBlueprintRepository(policies())).select(duration)

    assert selected.mode == "preset"
    assert selected.minimum_minutes == duration
    assert selected.maximum_minutes == duration


def test_custom_duration_uses_configured_range_and_rate() -> None:
    selected = BlueprintSelector(FakeBlueprintRepository(policies())).select(35)

    assert selected.mode == "custom"
    assert selected.question_count(35) == 35


@pytest.mark.parametrize("duration", [9, 91])
def test_custom_duration_outside_configured_range_is_rejected(duration) -> None:
    with pytest.raises(ApplicationError) as captured:
        BlueprintSelector(FakeBlueprintRepository(policies())).select(duration)

    assert captured.value.code == "invalid_quiz_duration"
