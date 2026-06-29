# Hoãn đánh giá annotation (PEP 563): method `list` làm lu mờ builtin `list`
# trong class, nên annotation `list[int]` ở method khác sẽ vỡ nếu đánh giá ngay.
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.documents import chunker, parsers
from app.modules.documents.models import Document, FileType
from app.modules.documents.repository import DocumentRepository
from app.modules.rag.facade import RagFacade

# Content-Type chuẩn cho từng loại file khi không có sẵn lúc upload.
_DEFAULT_CONTENT_TYPE = {
    FileType.PDF: "application/pdf",
    FileType.DOCX: (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    FileType.PPTX: (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
}


@dataclass
class DownloadFile:
    content: bytes
    filename: str
    content_type: str


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)
        self.rag = RagFacade()

    def ingest(
        self,
        content: bytes,
        filename: str,
        content_type: str | None,
        course_id: int,
        chapter_id: int | None,
        uploaded_by: int | None,
    ) -> Document:
        try:
            file_type = parsers.detect_file_type(filename)
            parsers.validate_mime(file_type, content_type)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        doc = self.repo.create(
            course_id=course_id,
            chapter_id=chapter_id,
            uploaded_by=uploaded_by,
            filename=filename,
            file_type=file_type,
        )
        # FR-ROOM-03: lưu nguyên bản để Sinh viên tải về (bỏ qua nếu quá lớn để
        # không phình DB Neon — tài liệu vẫn index bình thường).
        if len(content) <= settings.max_download_mb * 1024 * 1024:
            self.repo.save_file(doc.id, content, content_type)
        try:
            pages = parsers.parse(content, file_type)
            chunks = chunker.chunk_pages(pages)
            if not chunks:
                raise ValueError("Không trích xuất được nội dung từ tài liệu")
            n = self.rag.index_chunks(
                document_id=doc.id,
                course_id=course_id,
                document_name=filename,
                chunks=chunks,
            )
            return self.repo.mark_indexed(doc, n)
        except Exception as e:
            self.db.rollback()
            self.repo.mark_failed(doc, str(e))
            raise HTTPException(status_code=500, detail=f"Index thất bại: {e}")

    def list(self, course_id: int | None = None) -> list[Document]:
        return self.repo.list(course_id)

    def ids_with_file(self, document_ids: list[int]) -> set[int]:
        return self.repo.ids_with_file(document_ids)

    # FR-ROOM-03: lấy nguyên bản file để tải; None nếu không lưu (file cũ/quá lớn).
    def get_file(self, document_id: int) -> DownloadFile | None:
        doc = self.repo.get(document_id)
        if not doc:
            return None
        stored = self.repo.get_file(document_id)
        if not stored:
            return None
        content_type = stored.content_type or _DEFAULT_CONTENT_TYPE.get(
            doc.file_type, "application/octet-stream"
        )
        return DownloadFile(
            content=stored.content,
            filename=doc.filename,
            content_type=content_type,
        )

    def delete(self, doc_id: int) -> None:
        doc = self.repo.get(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        self.rag.delete_document(doc_id)
        self.repo.delete(doc)
