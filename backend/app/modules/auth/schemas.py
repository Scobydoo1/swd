from pydantic import BaseModel

from app.modules.users.schemas import UserOut


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class GoogleLoginRequest(BaseModel):
    id_token: str
