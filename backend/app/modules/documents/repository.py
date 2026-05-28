from sqlalchemy.orm import Session

from app.modules.documents.models import Document, FileType, Status


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
        self.db.delete(doc)
        self.db.commit()
