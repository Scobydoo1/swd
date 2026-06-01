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


class AttemptOut(BaseModel):
    id: int
    user_id: int | None
    score: float
    created_at: datetime
