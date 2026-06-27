from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class QuestionIn(BaseModel):
    text: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_correct(self):
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index vượt quá số lựa chọn")
        return self


class QuizCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=1, max_length=200)
    questions: list[QuestionIn] = Field(min_length=1, max_length=50)


# FR-QZ-05: Yêu cầu AI soạn nháp đề (Lecturer duyệt/sửa trước khi lưu).
class QuizGenerateRequest(BaseModel):
    course_id: int
    num_questions: int = Field(default=5, ge=1, le=50)
    topic: str | None = Field(default=None, max_length=300)


# Kết quả AI soạn — chỉ là NHÁP, chưa lưu DB. Lecturer chỉnh rồi gọi QuizCreate.
class GeneratedQuiz(BaseModel):
    title: str
    questions: list[QuestionIn]


# Dạng gọn cho danh sách quiz.
class QuizOut(BaseModel):
    id: int
    course_id: int
    title: str
    num_questions: int
    created_at: datetime


# Dạng cho học sinh LÀM BÀI — KHÔNG lộ đáp án đúng.
class QuestionOut(BaseModel):
    id: int
    text: str
    options: list[str]


class QuizDetail(BaseModel):
    id: int
    course_id: int
    title: str
    questions: list[QuestionOut]


class SubmitRequest(BaseModel):
    answers: list[int]


class QuestionResult(BaseModel):
    question_id: int
    your_index: int | None
    correct_index: int
    is_correct: bool


class AttemptResult(BaseModel):
    score: float
    correct: int
    total: int
    results: list[QuestionResult]


# FR-QZ: Lecturer xem điểm của từng Sinh viên — kèm tên & email để nhận diện.
class AttemptOut(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None
    user_email: str | None
    score: float
    created_at: datetime


# FR-QZ: Một dòng trong "Bảng điểm" (Grade) của Sinh viên theo môn học.
class GradeItem(BaseModel):
    quiz_id: int
    quiz_title: str
    course_id: int
    attempt_id: int
    score: float
    correct: int
    total: int
    created_at: datetime


# Một câu trong màn xem lại bài làm: kèm đề, đáp án đã chọn và đáp án đúng.
class ReviewQuestion(BaseModel):
    id: int
    text: str
    options: list[str]
    your_index: int | None
    correct_index: int
    is_correct: bool


# FR-QZ-02 (mở rộng): Sinh viên xem lại chi tiết một lượt làm đã nộp.
class AttemptReview(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    score: float
    correct: int
    total: int
    created_at: datetime
    questions: list[ReviewQuestion]
