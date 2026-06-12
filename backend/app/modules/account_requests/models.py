import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.modules.users.models import Role


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# FR-REQ: Người chưa có tài khoản gửi yêu cầu; Admin duyệt -> tạo tài khoản
# qua flow create_account sẵn có (mật khẩu tự sinh + email thông báo).
class AccountRequest(Base):
    __tablename__ = "account_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    requested_role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    message: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
