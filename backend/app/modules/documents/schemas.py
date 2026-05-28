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
    created_at: datetime
