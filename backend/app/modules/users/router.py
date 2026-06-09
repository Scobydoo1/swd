from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.users.models import Role
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import PlanUpdate, RoleUpdate, UserOut
from app.shared.dependencies import require_role

router = APIRouter(prefix="/api/users", tags=["users"])


# FR-ADM-01: Danh sách người dùng (chỉ Admin).
@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return UserRepository(db).list()


# FR-ADM-01: Đổi role người dùng (ADMIN/LECTURER/USER) — chỉ Admin.
@router.patch("/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    return repo.update_role(user, payload.role)


# FR-ADM-03: Admin đổi gói đăng ký của người dùng (Lecturer/Student).
@router.patch("/{user_id}/plan", response_model=UserOut)
def update_plan(
    user_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    # Gói dịch vụ chỉ áp dụng cho Sinh viên; Giảng viên & Admin được miễn.
    if user.role != Role.USER:
        raise HTTPException(
            status_code=400,
            detail="Chỉ tài khoản sinh viên mới có gói dịch vụ.",
        )
    return repo.update_plan(user, payload.plan)
