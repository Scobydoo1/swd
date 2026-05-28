from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.users.models import Role
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import RoleUpdate, UserOut
from app.shared.dependencies import require_role

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return UserRepository(db).list()


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
