from datetime import timezone

from sqlalchemy import case, func, select, update

from english7.api.errors import ApplicationError
from english7.db.models import Quiz, QuizQuestion, StudentAnswer, TestAttempt
from english7.modules.attempts.progress import AttemptResult, GradingQuestion


class SQLAlchemyProgressRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    @staticmethod
    def _results(session, user_id, quiz_id=None):
        statement = (
            select(TestAttempt.quiz_id, TestAttempt.created_at,
                   func.sum(case((StudentAnswer.is_correct == True, 1), else_=0)),
                   func.count(StudentAnswer.id))
            .join(StudentAnswer, StudentAnswer.test_attempt_id == TestAttempt.id)
            .where(TestAttempt.user_id == user_id, TestAttempt.status == 'submitted')
            .group_by(TestAttempt.id, TestAttempt.quiz_id, TestAttempt.created_at)
            .order_by(TestAttempt.created_at.desc(), TestAttempt.id.desc())
        )
        if quiz_id is not None:
            statement = statement.where(TestAttempt.quiz_id == quiz_id)
        return [AttemptResult(qid, date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date,
                              int(correct), total)
                for qid, date, correct, total in session.execute(statement)]

    def submit(self, user_id, quiz_id, grade):
        with self._session_factory() as session, session.begin():
            # UPDATE obtains a transaction-held row lock on SQL Server, serializing
            # simultaneous submissions before checking for an existing result.
            changed = session.execute(update(Quiz).where(
                Quiz.id == quiz_id, Quiz.created_for_user_id == user_id,
            ).values(is_locked=True))
            if changed.rowcount == 0:
                raise ApplicationError('quiz_not_found', 'Quiz was not found', 404)
            existing = self._results(session, user_id, quiz_id)
            if existing:
                return existing[0]
            questions = session.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)).all()
            answers = grade([GradingQuestion(q.id, (q.answer_payload or {}).get('correct')) for q in questions])
            attempt = TestAttempt(quiz_id=quiz_id, user_id=user_id, status='submitted')
            session.add(attempt)
            session.flush()
            session.add_all(StudentAnswer(test_attempt_id=attempt.id, question_id=a.question_id,
                                          answer_payload={'answer': a.answer}, is_correct=a.correct)
                            for a in answers)
            session.flush()
            return self._results(session, user_id, quiz_id)[0]

    def history(self, user_id):
        with self._session_factory() as session:
            return self._results(session, user_id)
