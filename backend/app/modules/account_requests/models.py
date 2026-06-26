import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.modules.users.models import ID_TO_ROLE, ROLE_IDS, Role


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
    # Vai trò mong muốn tham chiếu bảng roles (tách entity, không nhúng enum).
    requested_role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), default=ROLE_IDS[Role.USER]
    )
    message: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Giữ API cũ: đọc/ghi requested_role bằng enum Role như khi còn là cột enum.
    @hybrid_property
    def requested_role(self) -> Role:
        return ID_TO_ROLE[self.requested_role_id]

    @requested_role.setter
    def requested_role(self, value: Role) -> None:
        self.requested_role_id = ROLE_IDS[value]

    @requested_role.expression
    def requested_role(cls):  # noqa: N805
        return case(
            (cls.requested_role_id == ROLE_IDS[Role.ADMIN], Role.ADMIN.value),
            (cls.requested_role_id == ROLE_IDS[Role.LECTURER], Role.LECTURER.value),
            else_=Role.USER.value,
        )
