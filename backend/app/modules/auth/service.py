from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.auth.schemas import TokenResponse
from app.modules.auth.security import create_access_token, verify_password
from app.modules.users.repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng",
            )
        return self._token_for(user)

    # FR-USR-01 (mở rộng): Đăng nhập Google — chỉ email đã được Admin cấp.
    def login_google(self, token: str) -> TokenResponse:
        if not settings.google_oauth_client_id:
            raise HTTPException(
                status_code=503, detail="Đăng nhập Google chưa được cấu hình"
            )
        try:
            info = google_id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.google_oauth_client_id
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Google không hợp lệ",
            )
        # Chỉ chấp nhận email Google đã xác minh — tránh mạo danh qua tài
        # khoản Workspace/IdP chưa verify email.
        if not info.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email Google chưa được xác minh",
            )
        email = info.get("email")
        user = self.repo.get_by_email(email) if email else None
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản chưa được cấp. Vui lòng liên hệ Quản trị viên.",
            )
        return self._token_for(user)

    def _token_for(self, user) -> TokenResponse:
        token = create_access_token(str(user.id), user.role.value)
        return TokenResponse(access_token=token, user=user)
