from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.account_requests.models import RequestStatus
from app.modules.account_requests.schemas import (
    AccountRequestCreate,
    AccountRequestOut,
    ApproveResult,
)
from app.modules.account_requests.service import AccountRequestService
from app.modules.users.models import Role
from app.shared.dependencies import require_role
from app.shared.rate_limit import account_request_rate_limit

router = APIRouter(prefix="/api/account-requests", tags=["account-requests"])


# FR-REQ-01: Public — ai chưa có tài khoản gửi yêu cầu (rate-limit theo IP).
@router.post("", response_model=AccountRequestOut, status_code=201)
def submit_request(
    payload: AccountRequestCreate,
    db: Session = Depends(get_db),
    _=Depends(account_request_rate_limit),
):
    return AccountRequestService(db).submit(payload)


# FR-REQ-02: Admin xem danh sách yêu cầu (lọc theo trạng thái nếu cần).
@router.get("", response_model=list[AccountRequestOut])
def list_requests(
    status: RequestStatus | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return AccountRequestService(db).list(status)


# FR-REQ-03: Admin duyệt — tạo tài khoản + gửi email mật khẩu tự sinh.
@router.post("/{request_id}/approve", response_model=ApproveResult)
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return AccountRequestService(db).approve(request_id)


# FR-REQ-03: Admin từ chối yêu cầu.
@router.post("/{request_id}/reject", response_model=AccountRequestOut)
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return AccountRequestService(db).reject(request_id)
