from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from english7.api.errors import ApplicationError
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.quizzes.service import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


class GenerateQuizRequest(BaseModel):
    duration_minutes: int = Field(gt=0)
    difficulty: str = Field(min_length=1, max_length=30)


class QuizResponse(BaseModel):
    id: UUID
    duration_minutes: int
    difficulty: str
    question_count: int


def get_quiz_service(request: Request) -> QuizService:
    service = getattr(request.app.state, "quiz_service", None)
    if service is None:
        raise ApplicationError(
            "quiz_service_unavailable", "Quiz service is not configured", 503
        )
    return service


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    payload: GenerateQuizRequest,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> QuizResponse:
    draft = service.generate(
        user.id, payload.duration_minutes, payload.difficulty
    )
    return QuizResponse(
        id=draft.id,
        duration_minutes=draft.duration_minutes,
        difficulty=draft.difficulty,
        question_count=draft.question_count,
    )
