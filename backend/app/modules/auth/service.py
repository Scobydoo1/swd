from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.schemas import RegisterRequest, TokenResponse
from app.modules.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.users.repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, req: RegisterRequest) -> TokenResponse:
        if self.repo.get_by_email(req.email):
            raise HTTPException(status_code=400, detail="Email đã được đăng ký")
        user = self.repo.create(
            email=req.email,
            password_hash=hash_password(req.password),
            full_name=req.full_name,
            role=req.role,
        )
        return self._token_for(user)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng",
            )
        return self._token_for(user)

    def _token_for(self, user) -> TokenResponse:
        token = create_access_token(str(user.id), user.role.value)
        return TokenResponse(access_token=token, user=user)
