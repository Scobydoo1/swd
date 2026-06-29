from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.users.models import Role

# Giới hạn kích thước data URI ảnh đại diện (~1MB sau base64) để DB không phình.
MAX_AVATAR_CHARS = 1_500_000


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: Role
    avatar_url: str | None = None
    created_at: datetime


class RoleUpdate(BaseModel):
    role: Role


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: Role = Role.USER

    @field_validator("role")
    @classmethod
    def no_admin(cls, v: Role) -> Role:
        # Chỉ tạo được LECTURER/USER qua API; ADMIN seed qua env.
        if v == Role.ADMIN:
            raise ValueError("Không thể tạo tài khoản ADMIN qua API")
        return v


class UserCreateResult(BaseModel):
    user: UserOut
    email_sent: bool
    # Chỉ trả khi gửi email thất bại để Admin gửi tay; không bao giờ log.
    temp_password: str | None = None


# FR-USR: Mọi người dùng tự sửa hồ sơ của mình (tên + ảnh đại diện).
class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    # data URI ảnh, hoặc None để xóa ảnh. Trường vắng mặt = giữ nguyên (xem router).
    avatar_url: str | None = None

    @field_validator("avatar_url")
    @classmethod
    def valid_avatar(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.startswith("data:image/"):
            raise ValueError("Ảnh đại diện phải là data URI hình ảnh hợp lệ")
        if len(v) > MAX_AVATAR_CHARS:
            raise ValueError("Ảnh đại diện quá lớn (tối đa ~1MB)")
        return v


# FR-USR: Đổi mật khẩu — yêu cầu mật khẩu hiện tại để xác thực.
class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)
