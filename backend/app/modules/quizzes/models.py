from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    # FR-ROOM: Quiz thuộc về một phòng học (lớp). Nullable cho dữ liệu cũ;
    # quiz tạo mới luôn gắn room. Chỉ thành viên phòng thấy & làm được.
    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("rooms.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    # Mật khẩu vào quiz (tuỳ chọn) — chỉ Lecturer/Admin xem lại được.
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Hạn nộp: ngoài [opens_at, closes_at] thì Sinh viên không làm được.
    opens_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closes_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    questions: Mapped[list["Question"]] = relationship(
        cascade="all, delete-orphan",
        order_by="Question.order",
        backref="quiz",
    )


class Question(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    text: Mapped[str] = mapped_column(Text)
    options_json: Mapped[str] = mapped_column(Text)  # JSON: list[str]
    correct_index: Mapped[int] = mapped_column(Integer)
    order: Mapped[int] = mapped_column(Integer, default=0)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float)
    answers_json: Mapped[str] = mapped_column(Text)  # JSON: list[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
