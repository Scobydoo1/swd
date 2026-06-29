from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.users.models import Role
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    PasswordChange,
    ProfileUpdate,
    RoleUpdate,
    UserCreate,
    UserCreateResult,
    UserOut,
)
from app.modules.users.service import UserService
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/users", tags=["users"])


# FR-USR: Mọi người dùng tự sửa hồ sơ của mình (tên + ảnh đại diện). Khai báo
# trước các route /{user_id} để "me" không bị nuốt.
@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return UserService(db).update_profile(user, payload)


# FR-USR: Mọi người dùng tự đổi mật khẩu (cần mật khẩu hiện tại).
@router.patch("/me/password", status_code=204)
def change_my_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    UserService(db).change_password(user, payload)


# FR-ADM-01: Danh sách người dùng (chỉ Admin).
@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return UserRepository(db).list()


# FR-ADM-01: Admin tạo tài khoản Sinh viên/Giảng viên; mật khẩu tự sinh gửi
# qua email (xem UserService.create_account).
@router.post("", response_model=UserCreateResult, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return UserService(db).create_account(payload)


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


# FR-ADM-01: Admin xóa người dùng (kèm dọn phiên chat & lượt làm quiz của họ).
# Không cho tự xóa chính mình (kiểm tra trong service).
@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current=Depends(require_role(Role.ADMIN)),
):
    UserService(db).delete(user_id, current)
