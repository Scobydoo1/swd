from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.documents.schemas import DocumentOut
from app.modules.documents.service import DocumentService
from app.modules.users.models import Role
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    chapter_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    content = await file.read()
    return DocumentService(db).ingest(
        content=content,
        filename=file.filename,
        course_id=course_id,
        chapter_id=chapter_id,
        uploaded_by=user.id,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(
    course_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return DocumentService(db).list(course_id)


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    DocumentService(db).delete(doc_id)
