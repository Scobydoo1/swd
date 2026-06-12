from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.quizzes.schemas import (
    AttemptOut,
    AttemptResult,
    QuizCreate,
    QuizDetail,
    QuizOut,
    SubmitRequest,
)
from app.modules.quizzes.service import QuizService
from app.modules.users.models import Role
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


# FR-LEC-02: Giảng viên/Admin tạo quiz cho môn học.
@router.post("", response_model=QuizOut)
def create_quiz(
    payload: QuizCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return QuizService(db).create(payload, user)


# Mọi người xem danh sách quiz (lọc theo môn nếu cần).
@router.get("", response_model=list[QuizOut])
def list_quizzes(
    course_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return QuizService(db).list(course_id)


# FR-STU: Sinh viên mở quiz để làm (đáp án đúng được ẩn).
@router.get("/{quiz_id}", response_model=QuizDetail)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return QuizService(db).get_detail(quiz_id)


# FR-STU: Nộp bài và chấm điểm.
@router.post("/{quiz_id}/submit", response_model=AttemptResult)
def submit_quiz(
    quiz_id: int,
    payload: SubmitRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return QuizService(db).submit(quiz_id, payload.answers, user)


# FR-QZ-04: Người tạo quiz (Lecturer) / Admin xem bảng điểm các lượt làm bài.
@router.get("/{quiz_id}/attempts", response_model=list[AttemptOut])
def quiz_attempts(
    quiz_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return QuizService(db).list_attempts(quiz_id, user)


# Giảng viên (của mình) hoặc Admin xóa quiz.
@router.delete("/{quiz_id}", status_code=204)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    QuizService(db).delete(quiz_id, user)
