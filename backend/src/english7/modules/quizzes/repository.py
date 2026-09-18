from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.api.errors import ApplicationError
from english7.db.models import (
    QuestionSource,
    Quiz,
    QuizBlueprint,
    QuizQuestion,
    ReviewStatus,
    SourceFragment,
)
from english7.modules.quizzes.domain import (
    GeneratedQuestion,
    QuizBlueprintPolicy,
    QuizDraft,
)


class SQLAlchemyBlueprintRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def list_active(self) -> list[QuizBlueprintPolicy]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(QuizBlueprint)
                .where(QuizBlueprint.is_active == True)
                .order_by(QuizBlueprint.duration_minutes, QuizBlueprint.name)
            )
            policies = []
            for row in rows:
                config = row.policy
                mode = str(config["mode"])
                minimum = int(config.get("minimum_minutes", row.duration_minutes))
                maximum = int(config.get("maximum_minutes", row.duration_minutes))
                rate = int(config["question_rate"])
                policies.append(
                    QuizBlueprintPolicy(
                        row.id, row.name, minimum, maximum, rate, mode
                    )
                )
            return policies


class SQLAlchemyQuizRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _source_ids(questions: tuple[GeneratedQuestion, ...]) -> set[UUID]:
        return {
            source_id
            for question in questions
            for source_id in question.source_fragment_ids
        }

    def create(
        self,
        *,
        user_id: UUID,
        blueprint_id: UUID,
        duration_minutes: int,
        difficulty: str,
        questions: tuple[GeneratedQuestion, ...],
    ) -> QuizDraft:
        source_ids = self._source_ids(questions)
        with self._session_factory() as session, session.begin():
            verified = set(
                session.scalars(
                    select(SourceFragment.id).where(
                        SourceFragment.id.in_(source_ids),
                        SourceFragment.review_status == ReviewStatus.VERIFIED.value,
                    )
                )
            )
            if verified != source_ids:
                raise ApplicationError(
                    "invalid_question_source",
                    "Quiz questions must reference verified textbook fragments",
                    422,
                )
            quiz = Quiz(
                blueprint_id=blueprint_id,
                created_for_user_id=user_id,
                is_locked=False,
            )
            session.add(quiz)
            session.flush()
            for item in questions:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    prompt=item.prompt,
                    answer_payload=item.answer,
                    is_published=True,
                )
                session.add(question)
                session.flush()
                session.add_all(
                    QuestionSource(
                        question_id=question.id, source_fragment_id=source_id
                    )
                    for source_id in item.source_fragment_ids
                )
            return QuizDraft(
                quiz.id, duration_minutes, difficulty, len(questions)
            )
