# Hoãn đánh giá annotation (PEP 563): method `list` làm lu mờ builtin `list`
# trong class, nên các annotation `-> list[QuizOut]` phía dưới sẽ vỡ nếu đánh
# giá ngay khi load. Stringized annotations tránh TypeError lúc import.
from __future__ import annotations

import json
import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.llm.client import LlmClient
from app.modules.quizzes.models import Quiz
from app.modules.quizzes.repository import QuizRepository
from app.modules.quizzes.schemas import (
    AttemptOut,
    AttemptResult,
    AttemptReview,
    GeneratedQuiz,
    GradeItem,
    QuestionIn,
    QuestionOut,
    QuestionResult,
    QuizCreate,
    QuizDetail,
    QuizGenerateRequest,
    QuizOut,
    QuizPasswordOut,
    ReviewQuestion,
)
from app.modules.rag.facade import RagFacade
from app.modules.rooms.repository import RoomRepository
from app.modules.users.models import Role, User

# FR-QZ-05: System prompt buộc AI trả về JSON thuần để parse được an toàn.
_GEN_SYSTEM_PROMPT = """Bạn là trợ lý soạn đề trắc nghiệm cho giảng viên đại học.
Dựa CHỦ YẾU trên NGỮ CẢNH tài liệu môn học (nếu có), hãy soạn câu hỏi trắc nghiệm chất lượng.

QUY TẮC:
- Mỗi câu có ĐÚNG 4 lựa chọn, chỉ 1 đáp án đúng.
- Câu hỏi và lựa chọn bằng tiếng Việt, rõ ràng, không trùng lặp.
- Bám sát nội dung tài liệu; không bịa thông tin ngoài phạm vi.
- CHỈ trả về một mảng JSON hợp lệ, KHÔNG kèm giải thích hay markdown.

Định dạng bắt buộc (correct_index là chỉ số 0-based của đáp án đúng):
[{"text": "...", "options": ["A", "B", "C", "D"], "correct_index": 0}]
"""


class QuizService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = QuizRepository(db)

    def create(self, payload: QuizCreate, user: User) -> QuizOut:
        # FR-ROOM: quiz gắn 1 phòng; chỉ người tạo phòng / Admin được giao quiz.
        room = RoomRepository(self.db).get(payload.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")
        if user.role != Role.ADMIN and room.created_by != user.id:
            raise HTTPException(
                status_code=403,
                detail="Chỉ người tạo phòng hoặc Admin được giao quiz cho phòng",
            )
        if (
            payload.opens_at
            and payload.closes_at
            and payload.closes_at <= payload.opens_at
        ):
            raise HTTPException(
                status_code=400, detail="Hạn đóng phải sau hạn mở"
            )
        quiz = self.repo.create(
            payload, course_id=room.course_id, created_by=user.id
        )
        return self._to_out(quiz)

    # FR-QZ-05: AI soạn NHÁP đề từ tài liệu môn học để Lecturer duyệt/sửa.
    def generate(self, payload: QuizGenerateRequest) -> GeneratedQuiz:
        if settings.llm_provider == "local":
            raise HTTPException(
                status_code=400,
                detail="Tính năng AI soạn đề cần bật Gemini "
                "(đặt GOOGLE_API_KEY và LLM_PROVIDER=gemini).",
            )

        # Lấy ngữ cảnh từ tài liệu của môn để bám sát nội dung.
        query = payload.topic or "tổng quan kiến thức trọng tâm của môn học"
        retrieved = RagFacade().retrieve(
            query, k=8, course_id=payload.course_id
        )
        if not retrieved:
            raise HTTPException(
                status_code=400,
                detail="Môn học chưa có tài liệu đã index để AI soạn đề.",
            )
        context = "\n\n---\n".join(
            f"[{r['document_name']} - trang {r['page']}]\n{r['source_text']}"
            for r in retrieved
        )[:12000]

        topic_line = (
            f"Chủ đề/yêu cầu cụ thể: {payload.topic}\n" if payload.topic else ""
        )
        user_msg = (
            f"{topic_line}Số câu hỏi cần soạn: {payload.num_questions}.\n\n"
            f"NGỮ CẢNH TÀI LIỆU:\n{context}"
        )
        messages = [
            {"role": "system", "content": _GEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        try:
            raw = LlmClient().chat(messages, temperature=0.7)
        except Exception as e:  # lỗi gọi Gemini -> báo rõ, không lộ stack.
            raise HTTPException(
                status_code=502, detail=f"Gọi AI thất bại: {e}"
            )

        questions = self._parse_generated(raw, payload.num_questions)
        if not questions:
            raise HTTPException(
                status_code=502,
                detail="AI không trả về đề hợp lệ, hãy thử lại.",
            )
        title = payload.topic.strip() if payload.topic else "Quiz do AI soạn"
        return GeneratedQuiz(title=title[:200], questions=questions)

    @staticmethod
    def _parse_generated(raw: str, limit: int) -> list[QuestionIn]:
        """Tách mảng JSON từ output của LLM rồi validate từng câu (bỏ câu lỗi)."""
        text = raw.strip()
        # Bỏ rào ```json ... ``` nếu có.
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL)
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            items = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
        out: list[QuestionIn] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            try:
                out.append(QuestionIn(**it))
            except Exception:
                continue  # bỏ qua câu sai định dạng, giữ phần hợp lệ.
            if len(out) >= limit:
                break
        return out

    def list(self, course_id: int | None) -> list[QuizOut]:
        return [self._to_out(q) for q in self.repo.list(course_id)]

    # Danh sách quiz theo vai trò: Admin tất cả; Lecturer quiz mình tạo;
    # Sinh viên quiz của các phòng mình tham gia.
    def list_for(self, user: User) -> list[QuizOut]:
        if user.role == Role.ADMIN:
            quizzes = self.repo.list()
        elif user.role == Role.LECTURER:
            quizzes = self.repo.list_created_by(user.id)
        else:
            quizzes = self.repo.list_for_member(user.id)
        return [self._to_out(q) for q in quizzes]

    def list_for_room(self, room_id: int) -> list[QuizOut]:
        return [self._to_out(q) for q in self.repo.list_by_room(room_id)]

    def get_detail(
        self, quiz_id: int, user: User, password: str | None = None
    ) -> QuizDetail:
        quiz = self._require(quiz_id)
        self._check_take_access(quiz, user, password)
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

    # FR-QZ: Mật khẩu chỉ Lecturer (người tạo) / Admin xem lại được.
    def get_password(self, quiz_id: int, user: User) -> QuizPasswordOut:
        quiz = self._require(quiz_id)
        if user.role != Role.ADMIN and quiz.created_by != user.id:
            raise HTTPException(
                status_code=403,
                detail="Chỉ người tạo quiz hoặc Admin được xem mật khẩu",
            )
        return QuizPasswordOut(password=quiz.password)

    # Kiểm soát quyền vào làm quiz: thành viên phòng + còn hạn + đúng mật khẩu.
    def _check_take_access(
        self,
        quiz: Quiz,
        user: User,
        password: str | None,
        require_password: bool = True,
    ) -> None:
        # Người quản lý (Admin / người tạo) luôn xem & thử đề được.
        if user.role == Role.ADMIN or quiz.created_by == user.id:
            return
        if quiz.room_id is None or not RoomRepository(self.db).get_member(
            quiz.room_id, user.id
        ):
            raise HTTPException(
                status_code=403, detail="Bạn không thuộc lớp của quiz này"
            )
        now = datetime.utcnow()
        if quiz.opens_at and now < quiz.opens_at:
            raise HTTPException(status_code=403, detail="Quiz chưa mở")
        if quiz.closes_at and now > quiz.closes_at:
            raise HTTPException(
                status_code=403, detail="Quiz đã đóng (quá hạn nộp)"
            )
        if require_password and quiz.password and password != quiz.password:
            raise HTTPException(status_code=403, detail="Sai mật khẩu quiz")

    @staticmethod
    def _grade(
        quiz: Quiz, answers: list[int]
    ) -> tuple[float, int, int, list[QuestionResult]]:
        """Chấm một lượt làm: trả (score%, số đúng, tổng, chi tiết từng câu)."""
        results: list[QuestionResult] = []
        correct = 0
        for i, q in enumerate(quiz.questions):
            your = answers[i] if i < len(answers) else None
            # -1 (frontend gửi khi bỏ trống) coi như chưa chọn.
            if your is not None and your < 0:
                your = None
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
        return score, correct, total, results

    def submit(
        self, quiz_id: int, answers: list[int], user: User
    ) -> AttemptResult:
        quiz = self._require(quiz_id)
        # Còn hạn + đúng lớp (đã nhập mật khẩu lúc mở đề nên bỏ qua mật khẩu).
        self._check_take_access(quiz, user, None, require_password=False)
        score, correct, total, results = self._grade(quiz, answers)
        # FR-QZ-03: Chỉ lưu điểm của Sinh viên — Lecturer/Admin xem thử đề
        # không ghi attempt để bảng kết quả của lớp không bị nhiễu.
        if user.role == Role.USER:
            self.repo.add_attempt(quiz_id, user.id, score, answers)
        return AttemptResult(
            score=score, correct=correct, total=total, results=results
        )

    # FR-QZ: Bảng điểm — mọi lượt làm của Sinh viên (lọc theo môn nếu có).
    def list_my_grades(
        self, user_id: int, course_id: int | None
    ) -> list[GradeItem]:
        items: list[GradeItem] = []
        for attempt, quiz in self.repo.list_user_attempts(user_id, course_id):
            answers = json.loads(attempt.answers_json)
            score, correct, total, _ = self._grade(quiz, answers)
            items.append(
                GradeItem(
                    quiz_id=quiz.id,
                    quiz_title=quiz.title,
                    course_id=quiz.course_id,
                    attempt_id=attempt.id,
                    score=score,
                    correct=correct,
                    total=total,
                    created_at=attempt.created_at,
                )
            )
        return items

    # FR-QZ-02: Sinh viên xem lại chi tiết một lượt làm đã nộp.
    def get_attempt_review(self, attempt_id: int, user: User) -> AttemptReview:
        attempt = self.repo.get_attempt(attempt_id)
        if not attempt:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài làm")
        quiz = self._require(attempt.quiz_id)
        # FR-QZ-04: chính chủ bài làm, người tạo quiz hoặc Admin — giảng viên
        # khác không xem được bài làm thuộc quiz không phải của mình.
        if (
            user.role != Role.ADMIN
            and attempt.user_id != user.id
            and quiz.created_by != user.id
        ):
            raise HTTPException(
                status_code=403, detail="Không có quyền xem bài làm này"
            )
        answers = json.loads(attempt.answers_json)
        score, correct, total, results = self._grade(quiz, answers)
        questions = [
            ReviewQuestion(
                id=q.id,
                text=q.text,
                options=json.loads(q.options_json),
                your_index=r.your_index,
                correct_index=r.correct_index,
                is_correct=r.is_correct,
            )
            for q, r in zip(quiz.questions, results)
        ]
        return AttemptReview(
            attempt_id=attempt.id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            score=score,
            correct=correct,
            total=total,
            created_at=attempt.created_at,
            questions=questions,
        )

    def delete(self, quiz_id: int, user: User) -> None:
        quiz = self._require(quiz_id)
        if user.role != Role.ADMIN and quiz.created_by != user.id:
            raise HTTPException(
                status_code=403, detail="Chỉ người tạo hoặc Admin được xóa quiz"
            )
        self.repo.delete(quiz)

    # FR-QZ-04: Bảng điểm chỉ dành cho người tạo quiz (Lecturer) hoặc Admin.
    def list_attempts(self, quiz_id: int, user: User) -> list[AttemptOut]:
        quiz = self._require(quiz_id)
        if user.role != Role.ADMIN and quiz.created_by != user.id:
            raise HTTPException(
                status_code=403,
                detail="Chỉ người tạo quiz hoặc Admin được xem kết quả",
            )
        return [
            AttemptOut(
                id=a.id,
                user_id=a.user_id,
                user_name=u.full_name if u else None,
                user_email=u.email if u else None,
                score=a.score,
                created_at=a.created_at,
            )
            for a, u in self.repo.list_attempts(quiz_id)
        ]

    def _require(self, quiz_id: int):
        quiz = self.repo.get(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        return quiz

    def _to_out(self, quiz) -> QuizOut:
        room_name = None
        if quiz.room_id is not None:
            room = RoomRepository(self.db).get(quiz.room_id)
            room_name = room.name if room else None
        return QuizOut(
            id=quiz.id,
            course_id=quiz.course_id,
            room_id=quiz.room_id,
            room_name=room_name,
            title=quiz.title,
            num_questions=len(quiz.questions),
            has_password=bool(quiz.password),
            opens_at=quiz.opens_at,
            closes_at=quiz.closes_at,
            created_at=quiz.created_at,
        )
