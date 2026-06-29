# Hoãn đánh giá annotation (PEP 563): method `list` làm lu mờ builtin `list`
# trong class, nên annotation `list[int]` ở method khác sẽ vỡ nếu đánh giá ngay.
from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.documents.models import (
    Document,
    DocumentFile,
    FileType,
    Status,
)


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        course_id: int,
        chapter_id: int | None,
        uploaded_by: int | None,
        filename: str,
        file_type: FileType,
    ) -> Document:
        doc = Document(
            course_id=course_id,
            chapter_id=chapter_id,
            uploaded_by=uploaded_by,
            filename=filename,
            file_type=file_type,
            status=Status.PROCESSING,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list(self, course_id: int | None = None) -> list[Document]:
        q = self.db.query(Document)
        if course_id is not None:
            q = q.filter(Document.course_id == course_id)
        return q.order_by(Document.created_at.desc()).all()

    def get(self, doc_id: int) -> Document | None:
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def mark_indexed(self, doc: Document, num_chunks: int) -> Document:
        doc.status = Status.INDEXED
        doc.num_chunks = num_chunks
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def mark_failed(self, doc: Document, error: str) -> Document:
        doc.status = Status.FAILED
        doc.error = error[:500]
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete(self, doc: Document) -> None:
        # Xóa bytes file kèm tài liệu để không còn bản mồ côi.
        self.db.query(DocumentFile).filter(
            DocumentFile.document_id == doc.id
        ).delete()
        self.db.delete(doc)
        self.db.commit()

    # FR-ROOM-03: lưu / đọc nguyên bản file để tải xuống.
    def save_file(
        self, document_id: int, content: bytes, content_type: str | None
    ) -> None:
        existing = self.db.get(DocumentFile, document_id)
        if existing:
            existing.content = content
            existing.content_type = content_type
        else:
            self.db.add(
                DocumentFile(
                    document_id=document_id,
                    content=content,
                    content_type=content_type,
                )
            )
        self.db.commit()

    def get_file(self, document_id: int) -> DocumentFile | None:
        return self.db.get(DocumentFile, document_id)

    def ids_with_file(self, document_ids: list[int]) -> set[int]:
        if not document_ids:
            return set()
        rows = (
            self.db.query(DocumentFile.document_id)
            .filter(DocumentFile.document_id.in_(document_ids))
            .all()
        )
        return {r[0] for r in rows}
