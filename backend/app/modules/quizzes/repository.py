import json

from sqlalchemy.orm import Session

from app.modules.quizzes.models import Question, Quiz, QuizAttempt
from app.modules.quizzes.schemas import QuizCreate
from app.modules.users.models import User


class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: QuizCreate, created_by: int | None) -> Quiz:
        quiz = Quiz(
            course_id=payload.course_id,
            title=payload.title,
            created_by=created_by,
        )
        for i, q in enumerate(payload.questions):
            quiz.questions.append(
                Question(
                    text=q.text,
                    options_json=json.dumps(q.options, ensure_ascii=False),
                    correct_index=q.correct_index,
                    order=i,
                )
            )
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def get(self, quiz_id: int) -> Quiz | None:
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def list(self, course_id: int | None = None) -> list[Quiz]:
        q = self.db.query(Quiz)
        if course_id is not None:
            q = q.filter(Quiz.course_id == course_id)
        return q.order_by(Quiz.created_at.desc()).all()

    def delete(self, quiz: Quiz) -> None:
        # Xóa các lượt làm bài trước (FK quiz_attempts.quiz_id không cascade) để
        # tránh lỗi ràng buộc khoá ngoại khi quiz đã có người làm.
        self.db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id).delete()
        self.db.delete(quiz)
        self.db.commit()

    def add_attempt(
        self, quiz_id: int, user_id: int | None, score: float, answers: list[int]
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            score=score,
            answers_json=json.dumps(answers),
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def list_attempts(self, quiz_id: int) -> list[tuple[QuizAttempt, User | None]]:
        # Outer join User để vẫn hiển thị lượt làm của tài khoản đã bị xóa.
        return (
            self.db.query(QuizAttempt, User)
            .outerjoin(User, User.id == QuizAttempt.user_id)
            .filter(QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )
