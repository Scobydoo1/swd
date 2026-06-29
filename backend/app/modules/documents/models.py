import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)
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
    filename: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[FileType] = mapped_column(Enum(FileType))
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.PROCESSING)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# FR-ROOM-03: Lưu nguyên bản file để Sinh viên trong phòng tải tài liệu học tập.
# Tách bảng riêng để bytes nặng không bị nạp theo mỗi truy vấn list/detail; chỉ
# đọc khi tải. create_all tự tạo bảng mới này trên mọi dialect (không cần migrate).
class DocumentFile(Base):
    __tablename__ = "document_files"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), primary_key=True
    )
    content: Mapped[bytes] = mapped_column(LargeBinary)  # bytea trên Postgres/Neon
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
