from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.modules.users.models import Plan, Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: Role
    plan: Plan = Plan.FREE
    created_at: datetime


class RoleUpdate(BaseModel):
    role: Role


class PlanUpdate(BaseModel):
    plan: Plan


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
