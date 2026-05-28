from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.modules.users.models import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: Role
    created_at: datetime


class RoleUpdate(BaseModel):
    role: Role
