from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.documents.models import FileType, Status


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    chapter_id: int | None
    filename: str
    file_type: FileType
    status: Status
    num_chunks: int
    # FR-ROOM-03: có nguyên bản file để tải xuống hay không (tài liệu cũ = False).
    has_file: bool = False
    created_at: datetime
