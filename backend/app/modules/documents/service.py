from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.documents import chunker, parsers
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.rag.facade import RagFacade


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

    def delete(self, doc_id: int) -> None:
        doc = self.repo.get(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        self.rag.delete_document(doc_id)
        self.repo.delete(doc)
