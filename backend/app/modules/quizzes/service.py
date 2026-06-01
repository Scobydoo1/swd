import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.quizzes.repository import QuizRepository
from app.modules.quizzes.schemas import (
    AttemptOut,
    AttemptResult,
    QuestionOut,
    QuestionResult,
    QuizCreate,
    QuizDetail,
    QuizOut,
)
from app.modules.users.models import Role, User


class QuizService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = QuizRepository(db)

    def create(self, payload: QuizCreate, user: User) -> QuizOut:
        quiz = self.repo.create(payload, created_by=user.id)
        return self._to_out(quiz)

    def list(self, course_id: int | None) -> list[QuizOut]:
        return [self._to_out(q) for q in self.repo.list(course_id)]

    def get_detail(self, quiz_id: int) -> QuizDetail:
        quiz = self._require(quiz_id)
        return QuizDetail(
            id=quiz.id,
            course_id=quiz.course_id,
            title=quiz.title,
            questions=[
                QuestionOut(
                    id=q.id, text=q.text, options=json.loads(q.options_json)
                )
                for q in quiz.questions
            ],
        )

    def submit(
        self, quiz_id: int, answers: list[int], user_id: int | None
    ) -> AttemptResult:
        quiz = self._require(quiz_id)
        results: list[QuestionResult] = []
        correct = 0
        for i, q in enumerate(quiz.questions):
            your = answers[i] if i < len(answers) else None
            ok = your == q.correct_index
            if ok:
                correct += 1
            results.append(
                QuestionResult(
                    question_id=q.id,
                    your_index=your,
                    correct_index=q.correct_index,
                    is_correct=ok,
                )
            )
        total = len(quiz.questions)
        score = round(correct / total * 100, 1) if total else 0.0
        self.repo.add_attempt(quiz_id, user_id, score, answers)
        return AttemptResult(
            score=score, correct=correct, total=total, results=results
        )

    def delete(self, quiz_id: int, user: User) -> None:
        quiz = self._require(quiz_id)
        if user.role != Role.ADMIN and quiz.created_by != user.id:
            raise HTTPException(
                status_code=403, detail="Chỉ người tạo hoặc Admin được xóa quiz"
            )
        self.repo.delete(quiz)

    def list_attempts(self, quiz_id: int) -> list[AttemptOut]:
        self._require(quiz_id)
        return [
            AttemptOut(
                id=a.id,
                user_id=a.user_id,
                score=a.score,
                created_at=a.created_at,
            )
            for a in self.repo.list_attempts(quiz_id)
        ]

    def _require(self, quiz_id: int):
        quiz = self.repo.get(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        return quiz

    @staticmethod
    def _to_out(quiz) -> QuizOut:
        return QuizOut(
            id=quiz.id,
            course_id=quiz.course_id,
            title=quiz.title,
            num_questions=len(quiz.questions),
            created_at=quiz.created_at,
        )
