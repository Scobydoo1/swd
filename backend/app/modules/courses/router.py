from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.courses.repository import CourseRepository
from app.modules.courses.schemas import ChapterOut, CourseCreate, CourseOut
from app.modules.users.models import Role
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return CourseRepository(db).list()


@router.post("", response_model=CourseOut)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return CourseRepository(db).create(
        payload.name, payload.description, owner_id=user.id
    )


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
