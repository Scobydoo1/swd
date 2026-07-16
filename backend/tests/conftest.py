"""Pytest fixtures: app test client trên SQLite riêng + token theo role.

QUAN TRỌNG: phải set env TRƯỚC khi import app (engine/settings tạo lúc import).
"""
import os
import pathlib

# DB test riêng, tắt SMTP/admin-seed/google để test tự kiểm soát.
os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["VECTOR_BACKEND"] = "chroma"
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""
os.environ["BREVO_API_KEY"] = ""
os.environ["ADMIN_EMAIL"] = ""
os.environ["ADMIN_PASSWORD"] = ""
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = ""

pathlib.Path("./data/test_app.db").unlink(missing_ok=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402


# SQLite mặc định KHÔNG kiểm tra khóa ngoại (khác Postgres trên production).
# Bật lên để test bắt được lỗi thứ tự xóa vi phạm FK như trên Neon.
@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def client():
    # Context manager để chạy startup event (init_db).
    with TestClient(app) as c:
        yield c


def _auth_headers(email: str, role_name: str) -> dict[str, str]:
    """Tạo user trực tiếp trong DB (nếu chưa có) và trả Bearer header."""
    from app.database import SessionLocal
    from app.modules.auth.security import create_access_token
    from app.modules.users.models import Role, User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash="not-a-real-hash",
                full_name=f"{role_name} Test",
                role=Role[role_name],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(str(user.id), user.role.value)
    finally:
        db.close()
    return {"Authorization": f"Bearer {token}"}


# Lưu ý: không dùng domain đặc biệt (.local/.test) — email-validator từ chối
# khi serialize EmailStr trong response.
@pytest.fixture()
def admin_headers(client) -> dict[str, str]:
    return _auth_headers("admin@maple-tests.com", "ADMIN")


@pytest.fixture()
def student_headers(client) -> dict[str, str]:
    return _auth_headers("student@maple-tests.com", "USER")


@pytest.fixture()
def lecturer_headers(client) -> dict[str, str]:
    return _auth_headers("lecturer@maple-tests.com", "LECTURER")
