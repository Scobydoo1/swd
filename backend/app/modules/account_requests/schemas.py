from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.account_requests.models import RequestStatus
from app.modules.users.models import Role


class AccountRequestCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: Role = Role.USER
    message: str = Field(default="", max_length=1000)

    @field_validator("role")
    @classmethod
    def no_admin(cls, v: Role) -> Role:
        # Chỉ xin được tài khoản Sinh viên/Giảng viên — ADMIN seed qua env.
        if v == Role.ADMIN:
            raise ValueError("Không thể yêu cầu tài khoản ADMIN")
        return v


class AccountRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    requested_role: Role
    message: str
    status: RequestStatus
    created_at: datetime
    decided_at: datetime | None


# Kết quả duyệt: yêu cầu đã chuyển APPROVED + thông tin gửi email mật khẩu.
class ApproveResult(BaseModel):
    request: AccountRequestOut
    email_sent: bool
    # Chỉ trả khi gửi email thất bại để Admin gửi tay; không bao giờ log.
    temp_password: str | None = None
