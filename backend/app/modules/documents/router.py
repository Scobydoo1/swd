from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.documents.schemas import DocumentOut
from app.modules.documents.service import DocumentService
from app.modules.users.models import Role
from app.shared.cache import list_cache
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/documents", tags=["documents"])


# FR-LEC-01: Upload tài liệu (PDF/DOCX/PPTX) -> ingest vào RAG pipeline.
# Endpoint SYNC có chủ đích: FastAPI chạy nó trong threadpool, nên pipeline
# ingest nặng (parse + chunk + embed, có thể hàng chục giây) không chiếm
# event loop — các request khác (chat, đăng nhập...) vẫn được phục vụ.
@router.post("", response_model=DocumentOut)
def upload_document(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    chapter_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    content = file.file.read()
    try:
        return DocumentService(db).ingest(
            content=content,
            filename=file.filename,
            content_type=file.content_type,
            course_id=course_id,
            chapter_id=chapter_id,
            uploaded_by=user.id,
            user=user,
        )
    finally:
        # Ingest lỗi vẫn tạo bản ghi FAILED -> luôn làm mới cache danh sách.
        list_cache.invalidate("documents")


# FR-LEC-03: Xem danh sách tài liệu đã index kèm trạng thái. Cache TTL theo
# course_id; invalidate ở upload/xóa (và xóa môn bên courses router).
@router.get("", response_model=list[DocumentOut])
def list_documents(
    course_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    key = f"documents:{course_id}"
    cached = list_cache.get(key)
    if cached is None:
        cached = [
            DocumentOut.model_validate(d).model_dump()
            for d in DocumentService(db).list(course_id)
        ]
        list_cache.set(key, cached)
    return cached


# FR-ADM-02 / FR-LEC: Xóa tài liệu (+ vector) — Lecturer của mình hoặc Admin
# (ownership kiểm tra trong service).
@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    DocumentService(db).delete(doc_id, user)
    list_cache.invalidate("documents")
