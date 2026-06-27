import json

from sqlalchemy.orm import Session

from app.modules.quizzes.models import Question, Quiz, QuizAttempt
from app.modules.quizzes.schemas import QuizCreate
from app.modules.rooms.models import RoomMember
from app.modules.users.models import User


class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, payload: QuizCreate, course_id: int, created_by: int | None
    ) -> Quiz:
        quiz = Quiz(
            course_id=course_id,
            room_id=payload.room_id,
            title=payload.title,
            password=(payload.password or None),
            opens_at=payload.opens_at,
            closes_at=payload.closes_at,
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

    def list_by_room(self, room_id: int) -> list[Quiz]:
        return (
            self.db.query(Quiz)
            .filter(Quiz.room_id == room_id)
            .order_by(Quiz.created_at.desc())
            .all()
        )

    def list_created_by(self, user_id: int) -> list[Quiz]:
        return (
            self.db.query(Quiz)
            .filter(Quiz.created_by == user_id)
            .order_by(Quiz.created_at.desc())
            .all()
        )

    # Quiz thuộc các phòng mà Sinh viên là thành viên.
    def list_for_member(self, user_id: int) -> list[Quiz]:
        return (
            self.db.query(Quiz)
            .join(RoomMember, RoomMember.room_id == Quiz.room_id)
            .filter(RoomMember.user_id == user_id)
            .order_by(Quiz.created_at.desc())
            .all()
        )

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

    def get_attempt(self, attempt_id: int) -> QuizAttempt | None:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.id == attempt_id)
            .first()
        )

    def list_user_attempts(
        self, user_id: int, course_id: int | None = None
    ) -> list[tuple[QuizAttempt, Quiz]]:
        # Bảng điểm của Sinh viên: join Quiz để lấy tiêu đề + lọc theo môn.
        q = (
            self.db.query(QuizAttempt, Quiz)
            .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
            .filter(QuizAttempt.user_id == user_id)
        )
        if course_id is not None:
            q = q.filter(Quiz.course_id == course_id)
        return q.order_by(QuizAttempt.created_at.desc()).all()
