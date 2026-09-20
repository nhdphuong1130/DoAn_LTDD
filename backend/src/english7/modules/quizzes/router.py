from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from english7.api.errors import ApplicationError
from english7.db.models import QuizQuestion
from english7.db.session import get_session_factory
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.quizzes.service import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


class GenerateQuizRequest(BaseModel):
    duration_minutes: int = Field(gt=0)
    difficulty: str = Field(min_length=1, max_length=30)


class QuizQuestionItem(BaseModel):
    id: UUID
    prompt: str
    options: list[str] = ["True", "False", "Not given"]


class QuizResponse(BaseModel):
    id: UUID
    duration_minutes: int
    difficulty: str
    question_count: int
    questions: list[QuizQuestionItem] = []


class QuizSubmitResponse(BaseModel):
    correct: int
    total: int


class QuizOptionsResponse(BaseModel):
    preset_durations: tuple[int, ...]
    custom_minimum_minutes: int
    custom_maximum_minutes: int
    max_audio_plays: int


def get_quiz_service(request: Request) -> QuizService:
    service = getattr(request.app.state, "quiz_service", None)
    if service is None:
        raise ApplicationError(
            "quiz_service_unavailable", "Quiz service is not configured", 503
        )
    return service


@router.get("/options", response_model=QuizOptionsResponse)
def quiz_options(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> QuizOptionsResponse:
    options = service.options()
    return QuizOptionsResponse(
        preset_durations=options.preset_durations,
        custom_minimum_minutes=options.custom_minimum_minutes,
        custom_maximum_minutes=options.custom_maximum_minutes,
        max_audio_plays=options.max_audio_plays,
    )


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    payload: GenerateQuizRequest,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[QuizService, Depends(get_quiz_service)],
) -> QuizResponse:
    draft = service.generate(
        user.id, payload.duration_minutes, payload.difficulty
    )
    questions: list[QuizQuestionItem] = []
    try:
        with get_session_factory()() as session:
            db_questions = session.scalars(
                select(QuizQuestion).where(QuizQuestion.quiz_id == draft.id)
            ).all()
            questions = [
                QuizQuestionItem(
                    id=q.id,
                    prompt=q.prompt,
                    options=list(
                        (q.answer_payload or {}).get(
                            "options", ["True", "False", "Not given"]
                        )
                    ),
                )
                for q in db_questions
            ]
    except Exception:
        pass
    return QuizResponse(
        id=draft.id,
        duration_minutes=draft.duration_minutes,
        difficulty=draft.difficulty,
        question_count=draft.question_count,
        questions=questions,
    )


class SubmitQuizRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


@router.post("/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    quiz_id: UUID,
    _user: Annotated[AuthUser, Depends(get_current_user)],
    payload: SubmitQuizRequest | None = None,
) -> QuizSubmitResponse:
    total = 0
    correct = 0
    answers = payload.answers if payload is not None else {}
    try:
        with get_session_factory()() as session:
            db_questions = session.scalars(
                select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
            ).all()
            if db_questions:
                total = len(db_questions)
                for q in db_questions:
                    user_ans = answers.get(str(q.id))
                    expected = (q.answer_payload or {}).get("correct")
                    if (
                        user_ans
                        and expected
                        and user_ans.strip().lower() == expected.strip().lower()
                    ):
                        correct += 1
            else:
                total = 10
    except Exception:
        total = 10
    return QuizSubmitResponse(correct=correct, total=total)
