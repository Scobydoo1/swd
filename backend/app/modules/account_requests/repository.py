from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.account_requests.models import AccountRequest, RequestStatus


class AccountRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, email: str, full_name: str, requested_role, message: str
    ) -> AccountRequest:
        req = AccountRequest(
            email=email,
            full_name=full_name,
            requested_role=requested_role,
            message=message,
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def get(self, request_id: int) -> AccountRequest | None:
        return (
            self.db.query(AccountRequest)
            .filter(AccountRequest.id == request_id)
            .first()
        )

    def list(self, status: RequestStatus | None = None) -> list[AccountRequest]:
        q = self.db.query(AccountRequest)
        if status is not None:
            q = q.filter(AccountRequest.status == status)
        return q.order_by(AccountRequest.created_at.desc()).all()

    def get_pending_by_email(self, email: str) -> AccountRequest | None:
        return (
            self.db.query(AccountRequest)
            .filter(
                AccountRequest.email == email,
                AccountRequest.status == RequestStatus.PENDING,
            )
            .first()
        )

    def set_status(self, req: AccountRequest, status: RequestStatus) -> AccountRequest:
        req.status = status
        req.decided_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(req)
        return req
