from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.account_requests.models import RequestStatus
from app.modules.account_requests.repository import AccountRequestRepository
from app.modules.account_requests.schemas import (
    AccountRequestCreate,
    AccountRequestOut,
    ApproveResult,
)
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


class AccountRequestService:
    """FR-REQ: Yêu cầu tài khoản công khai + Admin duyệt/từ chối."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountRequestRepository(db)
        self.users = UserRepository(db)

    # Public: gửi yêu cầu. Chặn email đã có tài khoản hoặc đã có yêu cầu chờ.
    def submit(self, payload: AccountRequestCreate) -> AccountRequestOut:
        if self.users.get_by_email(payload.email):
            raise HTTPException(
                status_code=400,
                detail="Email này đã có tài khoản — hãy đăng nhập hoặc dùng "
                "'Đăng nhập bằng Google'.",
            )
        if self.repo.get_pending_by_email(payload.email):
            raise HTTPException(
                status_code=400,
                detail="Email này đã có yêu cầu đang chờ duyệt. "
                "Vui lòng đợi Admin xử lý.",
            )
        req = self.repo.create(
            email=payload.email,
            full_name=payload.full_name,
            requested_role=payload.role,
            message=payload.message.strip(),
        )
        return AccountRequestOut.model_validate(req)

    def list(self, status: RequestStatus | None) -> list[AccountRequestOut]:
        return [AccountRequestOut.model_validate(r) for r in self.repo.list(status)]

    # Admin duyệt: tái dùng flow create_account (mật khẩu tự sinh + email).
    def approve(self, request_id: int) -> ApproveResult:
        req = self._require_pending(request_id)
        result = UserService(self.db).create_account(
            UserCreate(
                email=req.email,
                full_name=req.full_name,
                role=req.requested_role,
            )
        )
        req = self.repo.set_status(req, RequestStatus.APPROVED)
        return ApproveResult(
            request=AccountRequestOut.model_validate(req),
            email_sent=result.email_sent,
            temp_password=result.temp_password,
        )

    def reject(self, request_id: int) -> AccountRequestOut:
        req = self._require_pending(request_id)
        req = self.repo.set_status(req, RequestStatus.REJECTED)
        return AccountRequestOut.model_validate(req)

    def _require_pending(self, request_id: int):
        req = self.repo.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
        if req.status != RequestStatus.PENDING:
            raise HTTPException(
                status_code=400, detail="Yêu cầu này đã được xử lý trước đó"
            )
        return req
