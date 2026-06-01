from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    source_text: str
    document_name: str
    page: int | None = None
    score: float | None = None


class ChatRequest(BaseModel):
    # §11.6: input validation — câu hỏi không rỗng và có giới hạn độ dài.
    question: str = Field(min_length=1, max_length=4000)
    session_id: int | None = None
    course_id: int | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime
    citations: list[Citation] = []


class ChatResponse(BaseModel):
    session_id: int
    answer: str
    citations: list[Citation] = []


class SessionCreate(BaseModel):
    title: str | None = None
    course_id: int | None = None


class SessionUpdate(BaseModel):
    title: str | None = None
    pinned: bool | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    course_id: int | None
    pinned: bool = False
    created_at: datetime


class SessionDetail(SessionOut):
    messages: list[MessageOut] = []
