from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.modules.documents.schemas import DocumentOut
from app.modules.quizzes.schemas import QuizOut


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    course_id: int


class RoomOut(BaseModel):
    id: int
    name: str
    description: str
    course_id: int
    course_name: str
    created_by: int | None
    num_members: int
    num_quizzes: int
    created_at: datetime


class MemberOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    added_at: datetime


class InviteRequest(BaseModel):
    email: EmailStr


class StudentOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr


class AnnouncementCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class AnnouncementOut(BaseModel):
    id: int
    content: str
    author_name: str | None
    created_at: datetime


class RoomDetail(RoomOut):
    members: list[MemberOut]
    quizzes: list[QuizOut]
    documents: list[DocumentOut]
    announcements: list[AnnouncementOut]


# FR-ROOM-06: Một dòng bảng điểm tổng của lớp (mọi lượt làm trong phòng).
class RoomGradeRow(BaseModel):
    quiz_id: int
    quiz_title: str
    user_id: int | None
    student_name: str | None
    student_email: str | None
    score: float
    created_at: datetime
