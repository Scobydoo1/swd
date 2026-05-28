from pydantic import BaseModel, EmailStr

from app.modules.users.models import Role
from app.modules.users.schemas import UserOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.USER


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
