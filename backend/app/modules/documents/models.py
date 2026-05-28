import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FileType(str, enum.Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    PPTX = "PPTX"


class Status(str, enum.Enum):
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapters.id"), nullable=True
    )
    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType))
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.PROCESSING)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
