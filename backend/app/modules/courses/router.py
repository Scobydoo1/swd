from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.courses.repository import CourseRepository
from app.modules.courses.schemas import ChapterOut, CourseCreate, CourseOut
from app.modules.courses.service import CourseService
from app.modules.users.models import Role
from app.shared.cache import list_cache
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/courses", tags=["courses"])


# FR-LEC-02: Danh sách môn học (mọi người dùng đã đăng nhập). Cache TTL vì
# mọi role đều gọi khi mở app; invalidate ở các đường ghi bên dưới.
@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db), _=Depends(get_current_user)):
    cached = list_cache.get("courses")
    if cached is None:
        cached = [
            CourseOut.model_validate(c).model_dump()
            for c in CourseRepository(db).list()
        ]
        list_cache.set("courses", cached)
    return cached


# FR-LEC-02: Tạo môn học — Lecturer hoặc Admin.
@router.post("", response_model=CourseOut)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    course = CourseRepository(db).create(
        payload.name, payload.description, owner_id=user.id
    )
    list_cache.invalidate("courses")
    return course


# FR-LEC-02: Danh sách chương của một môn.
@router.get("/{course_id}/chapters", response_model=list[ChapterOut])
def list_chapters(
    course_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = CourseRepository(db)
    if not repo.get(course_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
    return repo.list_chapters(course_id)


# FR-ADM-02 / FR-LEC-02: Xóa môn học (kèm tài liệu, vector, quiz). Admin xóa mọi
# môn; Giảng viên chỉ xóa môn mình phụ trách (kiểm tra trong service).
@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    CourseService(db).delete(course_id, user)
    # Xóa môn cascade cả tài liệu -> làm mới cả hai danh sách cache.
    list_cache.invalidate("courses")
    list_cache.invalidate("documents")
