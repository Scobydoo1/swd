# Admin-Managed Accounts + Google Sign-In + Email + Free Deploy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chỉ Admin tạo tài khoản Sinh viên/Giảng viên (gửi email mật khẩu tự sinh qua Gmail SMTP), thêm đăng nhập Google (chỉ email đã được cấp), và deploy free: Vercel (frontend) + Render (backend) + Neon Postgres/pgvector (dữ liệu bền vững).

**Architecture:** Bỏ `POST /api/auth/register`; thêm `POST /api/users` (Admin) tự sinh mật khẩu + gửi mail đồng bộ qua `app/shared/mailer.py`; thêm `POST /api/auth/google` verify ID token bằng `google-auth`; seed Admin đầu tiên từ env khi startup. Vector store có 2 implementation cùng interface (`VectorStore` Chroma cho dev local, `PgVectorStore` cho production) chọn qua env `VECTOR_BACKEND`.

**Tech Stack:** FastAPI, SQLAlchemy, pytest + httpx TestClient, google-auth, smtplib (Gmail App Password), pgvector trên Neon Postgres, React + Google Identity Services, Vercel + Render.

**Spec:** `docs/superpowers/specs/2026-06-11-admin-accounts-google-login-deploy-design.md`

**Quy ước chung:**
- Chạy lệnh backend từ thư mục `backend/` (`cd backend` trước).
- Mọi commit message tiếng Việt/Anh đều được, kèm `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- KHÔNG log mật khẩu ở bất kỳ đâu (CLAUDE.md quy tắc 8).

---

### Task 1: Hạ tầng test (pytest + TestClient)

Dự án chưa có pytest. Tạo conftest với DB SQLite test riêng + fixtures token Admin/Student.

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Tạo `backend/requirements-dev.txt`**

```
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 2: Cài dependencies dev**

Run: `cd backend; pip install -r requirements-dev.txt`
Expected: cài thành công.

- [ ] **Step 3: Tạo `backend/tests/conftest.py`**

```python
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
os.environ["ADMIN_EMAIL"] = ""
os.environ["ADMIN_PASSWORD"] = ""
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = ""

pathlib.Path("./data/test_app.db").unlink(missing_ok=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


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


@pytest.fixture()
def admin_headers(client) -> dict[str, str]:
    return _auth_headers("admin@test.local", "ADMIN")


@pytest.fixture()
def student_headers(client) -> dict[str, str]:
    return _auth_headers("student@test.local", "USER")
```

Lưu ý: `VECTOR_BACKEND` và `GOOGLE_OAUTH_CLIENT_ID` chưa tồn tại trong Settings — set trước vô hại (extra="ignore"), Task 2 sẽ thêm.

- [ ] **Step 4: Tạo `backend/tests/test_health.py`**

```python
def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
```

- [ ] **Step 5: Chạy test**

Run: `cd backend; python -m pytest tests/test_health.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/requirements-dev.txt backend/tests/conftest.py backend/tests/test_health.py
git commit -m "test: pytest infrastructure with isolated SQLite test DB"
```

---

### Task 2: Mở rộng Settings + .env.example

**Files:**
- Modify: `backend/app/config.py` (thêm field sau `jwt_expire_minutes`)
- Modify: `backend/.env.example` (nếu chưa có thì tạo)

- [ ] **Step 1: Thêm settings mới vào `backend/app/config.py`**

Chèn vào class `Settings`, ngay sau `jwt_expire_minutes: int = 720`:

```python
    # Google OAuth (đăng nhập Google) — Client ID từ Google Cloud Console.
    google_oauth_client_id: str = ""

    # Gmail SMTP (App Password) để gửi email cấp tài khoản.
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""  # mặc định dùng smtp_user
    app_login_url: str = "http://localhost:5173"

    # Seed Admin đầu tiên khi startup (vì không còn đăng ký công khai).
    admin_email: str = ""
    admin_password: str = ""
    admin_full_name: str = "Quản trị viên"

    # Vector store backend: "chroma" (dev local) | "pgvector" (Neon/Postgres).
    vector_backend: str = "chroma"
```

- [ ] **Step 2: Cập nhật `backend/.env.example`** — thêm block (tạo file nếu chưa có, giữ nội dung cũ):

```
# --- Google OAuth login ---
GOOGLE_OAUTH_CLIENT_ID=

# --- Gmail SMTP (App Password: https://myaccount.google.com/apppasswords) ---
SMTP_USER=
SMTP_PASSWORD=
MAIL_FROM=
APP_LOGIN_URL=http://localhost:5173

# --- Admin đầu tiên (tự tạo khi startup nếu DB chưa có admin) ---
ADMIN_EMAIL=you@example.com
ADMIN_PASSWORD=<mat-khau-manh-cua-ban>
ADMIN_FULL_NAME=Quản trị viên

# --- Vector backend: chroma (local) | pgvector (Neon Postgres) ---
VECTOR_BACKEND=chroma
```

- [ ] **Step 3: Smoke test**

Run: `cd backend; python -c "from app.config import settings; print(settings.vector_backend, repr(settings.google_oauth_client_id))"`
Expected: `chroma ''`

- [ ] **Step 4: Commit**

```bash
git add backend/app/config.py backend/.env.example
git commit -m "feat(config): settings for Google OAuth, SMTP mailer, admin seed, vector backend"
```

---

### Task 3: Mailer (Gmail SMTP)

**Files:**
- Create: `backend/app/shared/mailer.py`
- Test: `backend/tests/test_mailer.py`

- [ ] **Step 1: Viết test fail `backend/tests/test_mailer.py`**

```python
import smtplib


def test_send_returns_false_when_smtp_not_configured(client):
    # conftest đã set SMTP_USER="" -> không cấu hình.
    from app.shared import mailer

    assert mailer.send_account_email("a@b.com", "Tên", "pw123") is False


def test_send_success_via_smtp(client, monkeypatch):
    from app.config import settings
    from app.shared import mailer

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            sent["host"] = host

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, user, password):
            sent["login"] = user

        def send_message(self, msg):
            sent["to"] = msg["To"]

    monkeypatch.setattr(settings, "smtp_user", "bot@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is True
    assert sent == {"host": "smtp.gmail.com", "login": "bot@gmail.com", "to": "sv@uni.edu"}


def test_send_returns_false_on_smtp_error(client, monkeypatch):
    from app.config import settings
    from app.shared import mailer

    def boom(*a, **kw):
        raise OSError("connection refused")

    monkeypatch.setattr(settings, "smtp_user", "bot@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(smtplib, "SMTP_SSL", boom)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is False
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `cd backend; python -m pytest tests/test_mailer.py -v`
Expected: FAIL — `ModuleNotFoundError`/`ImportError` (mailer chưa tồn tại).

- [ ] **Step 3: Tạo `backend/app/shared/mailer.py`**

```python
"""Gửi email qua Gmail SMTP (App Password).

Dùng cho FR: Admin tạo tài khoản -> gửi thông tin đăng nhập cho người dùng.
KHÔNG log mật khẩu (CLAUDE.md quy tắc 8).
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_account_email(to: str, full_name: str, password: str) -> bool:
    """Gửi email + mật khẩu tạm cho tài khoản mới. True nếu gửi thành công.

    SMTP chưa cấu hình -> False ngay; caller sẽ trả temp_password cho Admin
    để gửi tay (không chặn luồng tạo tài khoản khi demo).
    """
    if not settings.smtp_user or not settings.smtp_password:
        return False

    body = (
        f"Xin chào {full_name},\n\n"
        "Tài khoản Maple của bạn đã được Quản trị viên tạo:\n\n"
        f"  Email đăng nhập: {to}\n"
        f"  Mật khẩu: {password}\n\n"
        f"Đăng nhập tại: {settings.app_login_url}\n"
        'Bạn cũng có thể bấm "Đăng nhập bằng Google" với chính email này.\n\n'
        "-- Maple 🍁"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Tài khoản Maple của bạn đã được tạo"
    msg["From"] = settings.mail_from or settings.smtp_user
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True
    except Exception:
        logger.warning("Gửi email cấp tài khoản tới %s thất bại", to)
        return False
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `cd backend; python -m pytest tests/test_mailer.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/shared/mailer.py backend/tests/test_mailer.py
git commit -m "feat(mail): Gmail SMTP mailer for account credential emails"
```

---

### Task 4: Admin tạo tài khoản — `POST /api/users`

**Files:**
- Modify: `backend/app/modules/users/schemas.py`
- Modify: `backend/app/modules/users/service.py`
- Modify: `backend/app/modules/users/router.py`
- Test: `backend/tests/test_users_create.py`

- [ ] **Step 1: Viết test fail `backend/tests/test_users_create.py`**

```python
def test_admin_creates_user_smtp_off_returns_temp_password(client, admin_headers):
    res = client.post(
        "/api/users",
        json={"email": "newsv@uni.edu", "full_name": "Sinh Viên Mới", "role": "USER"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "newsv@uni.edu"
    assert data["user"]["role"] == "USER"
    assert data["email_sent"] is False
    # SMTP tắt -> trả mật khẩu tạm để Admin gửi tay.
    assert isinstance(data["temp_password"], str) and len(data["temp_password"]) >= 8


def test_created_user_can_login_with_temp_password(client, admin_headers):
    res = client.post(
        "/api/users",
        json={"email": "newgv@uni.edu", "full_name": "Giảng Viên Mới", "role": "LECTURER"},
        headers=admin_headers,
    )
    password = res.json()["temp_password"]
    login = client.post(
        "/api/auth/login",
        data={"username": "newgv@uni.edu", "password": password},
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "LECTURER"


def test_email_sent_hides_temp_password(client, admin_headers, monkeypatch):
    from app.shared import mailer

    monkeypatch.setattr(mailer, "send_account_email", lambda *a, **kw: True)
    res = client.post(
        "/api/users",
        json={"email": "mailok@uni.edu", "full_name": "Mail OK", "role": "USER"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    assert res.json()["email_sent"] is True
    assert res.json()["temp_password"] is None


def test_duplicate_email_400(client, admin_headers):
    payload = {"email": "dup@uni.edu", "full_name": "Dup", "role": "USER"}
    assert client.post("/api/users", json=payload, headers=admin_headers).status_code == 201
    assert client.post("/api/users", json=payload, headers=admin_headers).status_code == 400


def test_non_admin_cannot_create(client, student_headers):
    res = client.post(
        "/api/users",
        json={"email": "x@uni.edu", "full_name": "X", "role": "USER"},
        headers=student_headers,
    )
    assert res.status_code == 403


def test_cannot_create_admin_role(client, admin_headers):
    res = client.post(
        "/api/users",
        json={"email": "evil@uni.edu", "full_name": "Evil", "role": "ADMIN"},
        headers=admin_headers,
    )
    assert res.status_code == 422
```

Lưu ý monkeypatch: service phải gọi `mailer.send_account_email(...)` qua module (`from app.shared import mailer`) để patch được.

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `cd backend; python -m pytest tests/test_users_create.py -v`
Expected: FAIL — POST /api/users trả 405 (route chưa có).

- [ ] **Step 3: Thêm schemas vào `backend/app/modules/users/schemas.py`** (cuối file)

```python
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
```

Đồng thời sửa dòng import đầu file thành:

```python
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
```

- [ ] **Step 4: Thêm method vào `UserService` trong `backend/app/modules/users/service.py`**

Thêm imports đầu file:

```python
import secrets

from app.modules.auth.security import hash_password
from app.modules.users.schemas import UserCreate, UserCreateResult, UserOut
from app.shared import mailer
```

Thêm method vào class `UserService` (trên method `delete`):

```python
    # FR-ADM-01: Chỉ Admin tạo tài khoản Sinh viên/Giảng viên. Mật khẩu tự sinh
    # và gửi qua email; nếu gửi thất bại thì trả về cho Admin gửi tay.
    def create_account(self, req: UserCreate) -> UserCreateResult:
        if self.repo.get_by_email(req.email):
            raise HTTPException(status_code=400, detail="Email đã được đăng ký")
        password = secrets.token_urlsafe(9)  # ~12 ký tự URL-safe
        user = self.repo.create(
            email=req.email,
            password_hash=hash_password(password),
            full_name=req.full_name,
            role=req.role,
        )
        sent = mailer.send_account_email(user.email, user.full_name, password)
        return UserCreateResult(
            user=UserOut.model_validate(user),
            email_sent=sent,
            temp_password=None if sent else password,
        )
```

- [ ] **Step 5: Thêm route vào `backend/app/modules/users/router.py`**

Sửa import schemas:

```python
from app.modules.users.schemas import (
    PlanUpdate,
    RoleUpdate,
    UserCreate,
    UserCreateResult,
    UserOut,
)
```

Thêm route ngay sau `list_users`:

```python
# FR-ADM-01: Admin tạo tài khoản Sinh viên/Giảng viên; mật khẩu tự sinh gửi
# qua email (xem UserService.create_account).
@router.post("", response_model=UserCreateResult, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    return UserService(db).create_account(payload)
```

- [ ] **Step 6: Chạy test, xác nhận pass**

Run: `cd backend; python -m pytest tests/test_users_create.py -v`
Expected: 6 passed.

- [ ] **Step 7: Chạy toàn bộ test**

Run: `cd backend; python -m pytest tests/ -v --ignore=tests/evaluate.py`
Expected: tất cả pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/modules/users/ backend/tests/test_users_create.py
git commit -m "feat(users): admin-only account creation with emailed temp password (FR-ADM-01)"
```

---

### Task 5: Bỏ đăng ký công khai `POST /api/auth/register`

**Files:**
- Modify: `backend/app/modules/auth/router.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/app/modules/auth/schemas.py`
- Test: `backend/tests/test_auth.py` (tạo mới)

- [ ] **Step 1: Viết test fail `backend/tests/test_auth.py`**

```python
def test_public_register_removed(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "any@x.com", "password": "pw", "full_name": "Any"},
    )
    assert res.status_code in (404, 405)
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `cd backend; python -m pytest tests/test_auth.py -v`
Expected: FAIL (hiện trả 200).

- [ ] **Step 3: Xóa endpoint + code chết**

Trong `backend/app/modules/auth/router.py`: xóa hàm `register` (cả decorator) và bỏ `RegisterRequest` khỏi import (giữ `TokenResponse`).

Trong `backend/app/modules/auth/service.py`: xóa method `register`, bỏ `RegisterRequest` và `hash_password` khỏi import (giữ `create_access_token`, `verify_password`).

Trong `backend/app/modules/auth/schemas.py`: xóa class `RegisterRequest`, bỏ import `Role` nếu không còn dùng.

Kiểm tra không còn nơi nào import `RegisterRequest`: `cd backend; python -c "import app.main"` phải chạy sạch.

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `cd backend; python -m pytest tests/ -v`
Expected: tất cả pass (test login ở Task 4 vẫn dùng /auth/login — không ảnh hưởng).

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/auth/ backend/tests/test_auth.py
git commit -m "feat(auth)!: remove public registration — accounts are admin-issued only"
```

---

### Task 6: Seed Admin đầu tiên khi startup

**Files:**
- Modify: `backend/app/modules/users/service.py` (thêm hàm module-level)
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_seed_admin.py`

- [ ] **Step 1: Viết test fail `backend/tests/test_seed_admin.py`**

```python
def test_seed_creates_admin_once(client, monkeypatch):
    from app.config import settings
    from app.database import SessionLocal
    from app.modules.users.models import Role, User
    from app.modules.users.service import ensure_default_admin

    monkeypatch.setattr(settings, "admin_email", "boot@admin.local")
    monkeypatch.setattr(settings, "admin_password", "boot-secret")

    db = SessionLocal()
    try:
        # DB test có thể đã có admin từ fixture khác -> dọn để test sạch.
        db.query(User).filter(User.role == Role.ADMIN).delete()
        db.commit()

        ensure_default_admin(db)
        admins = db.query(User).filter(User.role == Role.ADMIN).all()
        assert [a.email for a in admins] == ["boot@admin.local"]

        # Idempotent: gọi lần 2 không tạo thêm.
        ensure_default_admin(db)
        assert db.query(User).filter(User.role == Role.ADMIN).count() == 1
    finally:
        db.close()


def test_seed_skipped_without_env(client, monkeypatch):
    from app.config import settings
    from app.database import SessionLocal
    from app.modules.users.models import Role, User
    from app.modules.users.service import ensure_default_admin

    monkeypatch.setattr(settings, "admin_email", "")

    db = SessionLocal()
    try:
        db.query(User).filter(User.role == Role.ADMIN).delete()
        db.commit()
        ensure_default_admin(db)
        assert db.query(User).filter(User.role == Role.ADMIN).count() == 0
    finally:
        db.close()
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `cd backend; python -m pytest tests/test_seed_admin.py -v`
Expected: FAIL — `ImportError: ensure_default_admin`.

- [ ] **Step 3: Thêm hàm vào cuối `backend/app/modules/users/service.py`**

```python
def ensure_default_admin(db: Session) -> None:
    """Seed Admin đầu tiên từ env khi startup.

    Không còn đăng ký công khai nên hệ thống cần ít nhất một Admin để cấp
    tài khoản. Bỏ qua nếu đã có admin hoặc env chưa cấu hình.
    """
    if not settings.admin_email or not settings.admin_password:
        return
    if db.query(User).filter(User.role == Role.ADMIN).first():
        return
    repo = UserRepository(db)
    if repo.get_by_email(settings.admin_email):
        return
    repo.create(
        email=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        full_name=settings.admin_full_name,
        role=Role.ADMIN,
    )
```

Bổ sung import đầu file (nếu chưa có): `from app.config import settings` và `Role` trong dòng import models:

```python
from app.modules.users.models import Role, User
```

- [ ] **Step 4: Gọi từ startup trong `backend/app/main.py`**

Thay hàm `on_startup` hiện tại bằng:

```python
@app.on_event("startup")
def on_startup():
    init_db()
    # Seed Admin đầu tiên (không còn đăng ký công khai).
    from app.database import SessionLocal
    from app.modules.users.service import ensure_default_admin

    db = SessionLocal()
    try:
        ensure_default_admin(db)
    finally:
        db.close()
```

- [ ] **Step 5: Chạy test, xác nhận pass**

Run: `cd backend; python -m pytest tests/ -v`
Expected: tất cả pass. (conftest đã set `ADMIN_EMAIL=""` nên startup không seed vào DB test.)

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/users/service.py backend/app/main.py backend/tests/test_seed_admin.py
git commit -m "feat(users): seed first admin from env on startup"
```

---

### Task 7: Đăng nhập Google — `POST /api/auth/google`

**Files:**
- Modify: `backend/requirements.txt` (thêm `google-auth`)
- Modify: `backend/app/modules/auth/schemas.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/app/modules/auth/router.py`
- Test: `backend/tests/test_auth.py` (bổ sung)

- [ ] **Step 1: Thêm dependency**

Thêm vào `backend/requirements.txt` (sau `bcrypt>=4.2.0`):

```
google-auth>=2.35.0
```

Run: `cd backend; pip install "google-auth>=2.35.0"`

- [ ] **Step 2: Viết test fail — thêm vào `backend/tests/test_auth.py`**

```python
def _patch_google_verify(monkeypatch, email: str):
    """Mock google-auth verify: trả payload với email cho trước."""
    from app.modules.auth import service as auth_service

    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda token, request, audience: {"email": email},
    )


def _enable_google(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "google_oauth_client_id", "test-client-id")


def test_google_login_not_configured_returns_503(client):
    res = client.post("/api/auth/google", json={"id_token": "any"})
    assert res.status_code == 503


def test_google_login_unknown_email_403(client, monkeypatch):
    _enable_google(monkeypatch)
    _patch_google_verify(monkeypatch, "stranger@gmail.com")
    res = client.post("/api/auth/google", json={"id_token": "fake"})
    assert res.status_code == 403


def test_google_login_known_email_returns_jwt(client, monkeypatch, admin_headers):
    # admin_headers fixture đảm bảo admin@test.local tồn tại trong DB.
    _enable_google(monkeypatch)
    _patch_google_verify(monkeypatch, "admin@test.local")
    res = client.post("/api/auth/google", json={"id_token": "fake"})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["user"]["email"] == "admin@test.local"


def test_google_login_invalid_token_401(client, monkeypatch):
    from app.modules.auth import service as auth_service

    _enable_google(monkeypatch)

    def raise_invalid(token, request, audience):
        raise ValueError("invalid token")

    monkeypatch.setattr(
        auth_service.google_id_token, "verify_oauth2_token", raise_invalid
    )
    res = client.post("/api/auth/google", json={"id_token": "bad"})
    assert res.status_code == 401
```

- [ ] **Step 3: Chạy test, xác nhận fail**

Run: `cd backend; python -m pytest tests/test_auth.py -v`
Expected: 4 test mới FAIL (405/AttributeError), test cũ pass.

- [ ] **Step 4: Thêm schema vào `backend/app/modules/auth/schemas.py`**

```python
class GoogleLoginRequest(BaseModel):
    id_token: str
```

- [ ] **Step 5: Thêm method vào `AuthService` trong `backend/app/modules/auth/service.py`**

Imports đầu file:

```python
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import settings
```

Method mới trong class (sau `login`):

```python
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
        email = info.get("email")
        user = self.repo.get_by_email(email) if email else None
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản chưa được cấp. Vui lòng liên hệ Quản trị viên.",
            )
        return self._token_for(user)
```

- [ ] **Step 6: Thêm route vào `backend/app/modules/auth/router.py`**

Import: thêm `GoogleLoginRequest` vào dòng import schemas. Route sau `login`:

```python
# Đăng nhập bằng Google (ID token từ Google Identity Services).
@router.post("/google", response_model=TokenResponse)
def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login_google(req.id_token)
```

- [ ] **Step 7: Chạy test, xác nhận pass**

Run: `cd backend; python -m pytest tests/ -v`
Expected: tất cả pass.

- [ ] **Step 8: Commit**

```bash
git add backend/requirements.txt backend/app/modules/auth/ backend/tests/test_auth.py
git commit -m "feat(auth): Google sign-in — only admin-issued emails may log in"
```

---

### Task 8: PgVectorStore (Neon Postgres + pgvector)

**Files:**
- Modify: `backend/requirements.txt` (thêm `psycopg2-binary`)
- Modify: `backend/app/modules/rag/vector_store.py` (thêm `PgVectorStore` + factory)
- Modify: `backend/app/modules/rag/facade.py` (dùng factory)
- Test: `backend/tests/test_vector_store.py`

- [ ] **Step 1: Thêm dependency**

Thêm vào `backend/requirements.txt`:

```
psycopg2-binary>=2.9.10   # driver Postgres (Neon) cho metadata + pgvector
google-auth>=2.35.0
```

(`google-auth` đã thêm ở Task 7 — không lặp lại nếu đã có.)

Run: `cd backend; pip install "psycopg2-binary>=2.9.10"`

- [ ] **Step 2: Viết test fail `backend/tests/test_vector_store.py`**

```python
def test_factory_returns_chroma_by_default(client):
    from app.modules.rag.vector_store import VectorStore, get_vector_store

    store = get_vector_store()
    assert isinstance(store, VectorStore)


def test_factory_returns_pgvector_when_configured(client, monkeypatch):
    from app.config import settings
    from app.modules.rag import vector_store

    monkeypatch.setattr(settings, "vector_backend", "pgvector")
    # Không có Postgres thật trong test -> chặn phần tạo bảng.
    monkeypatch.setattr(
        vector_store.PgVectorStore, "_ensure_schema", lambda self: None
    )
    store = vector_store.get_vector_store()
    assert isinstance(store, vector_store.PgVectorStore)


def test_pgvector_literal_format(client):
    from app.modules.rag.vector_store import PgVectorStore

    assert PgVectorStore._vec([0.1, 0.25, -1]) == "[0.1,0.25,-1.0]"
```

- [ ] **Step 3: Chạy test, xác nhận fail**

Run: `cd backend; python -m pytest tests/test_vector_store.py -v`
Expected: FAIL — `ImportError: get_vector_store`.

- [ ] **Step 4: Thêm vào cuối `backend/app/modules/rag/vector_store.py`**

```python
class PgVectorStore:
    """Vector store trên Postgres + pgvector (Neon free).

    Dùng khi deploy Render free (disk ephemeral): vector lưu DB ngoài nên
    không mất khi service restart. Cùng interface với VectorStore (Chroma).
    Cột `embedding vector` không khai báo số chiều -> một bảng theo
    provider (chiều local 512 / gemini 3072 không trộn lẫn, như Chroma).
    """

    def __init__(self) -> None:
        # Import muộn để dev local (SQLite + Chroma) không cần psycopg2.
        from app.database import engine

        self._engine = engine
        self._table = f"rag_chunks_{settings.embed_provider}"
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        from sqlalchemy import text

        with self._engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table} (
                        id TEXT PRIMARY KEY,
                        document_id INTEGER NOT NULL,
                        course_id INTEGER,
                        document_name TEXT NOT NULL DEFAULT '',
                        page INTEGER,
                        chunk_index INTEGER,
                        text TEXT NOT NULL,
                        embedding vector NOT NULL
                    )
                    """
                )
            )

    @staticmethod
    def _vec(embedding) -> str:
        # Literal pgvector: "[0.1,0.2,...]".
        return "[" + ",".join(str(float(x)) for x in embedding) + "]"

    def add(self, ids: list[str], embeddings, documents, metadatas) -> None:
        from sqlalchemy import text

        rows = [
            {
                "id": id_,
                "document_id": meta["document_id"],
                "course_id": meta.get("course_id"),
                "document_name": meta.get("document_name", ""),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index"),
                "text": doc,
                "embedding": self._vec(emb),
            }
            for id_, emb, doc, meta in zip(ids, embeddings, documents, metadatas)
        ]
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    f"""
                    INSERT INTO {self._table}
                        (id, document_id, course_id, document_name, page,
                         chunk_index, text, embedding)
                    VALUES
                        (:id, :document_id, :course_id, :document_name, :page,
                         :chunk_index, :text, CAST(:embedding AS vector))
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding
                    """
                ),
                rows,
            )

    def query(self, embedding, k: int, where: dict | None = None) -> list[dict]:
        from sqlalchemy import text

        filter_sql = ""
        params: dict = {"vec": self._vec(embedding), "k": k}
        if where and where.get("course_id") is not None:
            filter_sql = "WHERE course_id = :course_id"
            params["course_id"] = where["course_id"]

        sql = text(
            f"""
            SELECT text, document_id, course_id, document_name, page,
                   chunk_index,
                   1 - (embedding <=> CAST(:vec AS vector)) AS score
            FROM {self._table}
            {filter_sql}
            ORDER BY embedding <=> CAST(:vec AS vector)
            LIMIT :k
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
        return [
            {
                "text": r["text"],
                "meta": {
                    "document_id": r["document_id"],
                    "course_id": r["course_id"],
                    "document_name": r["document_name"],
                    "page": r["page"],
                    "chunk_index": r["chunk_index"],
                },
                "score": float(r["score"]),
            }
            for r in rows
        ]

    def delete_document(self, document_id: int) -> None:
        from sqlalchemy import text

        with self._engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {self._table} WHERE document_id = :doc_id"),
                {"doc_id": document_id},
            )


def get_vector_store():
    """Factory chọn backend vector theo env VECTOR_BACKEND."""
    if settings.vector_backend == "pgvector":
        return PgVectorStore()
    return VectorStore()
```

- [ ] **Step 5: Facade dùng factory — sửa `backend/app/modules/rag/facade.py`**

Đổi import:

```python
from app.modules.rag.vector_store import get_vector_store
```

Đổi dòng khởi tạo trong `__init__`:

```python
        self.store = get_vector_store()
```

(`Retriever` nhận store qua tham số — type hint `VectorStore` trong `retriever.py` đổi thành không bắt buộc; sửa signature thành `store` không annotation hoặc giữ nguyên đều chạy được. Sửa cho sạch: trong `retriever.py` xóa import `VectorStore` và bỏ annotation `store: VectorStore` → `store`.)

- [ ] **Step 6: Chạy test, xác nhận pass**

Run: `cd backend; python -m pytest tests/ -v`
Expected: tất cả pass.

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/modules/rag/ backend/tests/test_vector_store.py
git commit -m "feat(rag): pgvector store on Postgres for persistent vectors on free hosting"
```

---

### Task 9: Frontend — bỏ đăng ký, thêm nút Google

**Files:**
- Modify: `frontend/src/auth/AuthContext.tsx`
- Create: `frontend/src/components/GoogleSignInButton.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/i18n/translations.ts`

- [ ] **Step 1: Sửa `frontend/src/auth/AuthContext.tsx`**

Thay interface `AuthCtx`: xóa `register`, thêm `loginWithGoogle`:

```tsx
interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}
```

Xóa hàm `register` trong `AuthProvider`, thêm:

```tsx
  const loginWithGoogle = async (idToken: string) => {
    const { data } = await api.post<TokenResponse>("/auth/google", {
      id_token: idToken,
    });
    localStorage.setItem("token", data.access_token);
    setUser(data.user);
  };
```

Cập nhật `value`:

```tsx
  const value = useMemo(
    () => ({ user, loading, login, loginWithGoogle, logout, refresh }),
    [user, loading]
  );
```

Bỏ import `Role` nếu không còn dùng trong file.

- [ ] **Step 2: Tạo `frontend/src/components/GoogleSignInButton.tsx`**

```tsx
import { useEffect, useRef } from "react";

// Client ID OAuth từ Google Cloud Console; thiếu env -> ẩn nút.
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (res: { credential: string }) => void;
          }) => void;
          renderButton: (el: HTMLElement, options: object) => void;
        };
      };
    };
  }
}

export function GoogleSignInButton({
  onCredential,
}: {
  onCredential: (idToken: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!CLIENT_ID) return;
    const init = () => {
      if (!window.google || !ref.current) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: (res) => onCredential(res.credential),
      });
      window.google.accounts.id.renderButton(ref.current, {
        theme: "outline",
        size: "large",
        width: 300,
      });
    };
    if (window.google) {
      init();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = init;
    document.head.appendChild(script);
  }, [onCredential]);

  if (!CLIENT_ID) return null;
  return <div ref={ref} className="flex justify-center" />;
}
```

- [ ] **Step 3: Viết lại `frontend/src/pages/LoginPage.tsx`** (toàn bộ file)

```tsx
import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../theme/ThemeContext";
import { useLang } from "../i18n/LanguageContext";
import { GoogleSignInButton } from "../components/GoogleSignInButton";
import { IconMaple, IconMoon, IconSun } from "../components/Icons";

export function LoginPage() {
  const { user, login, loginWithGoogle } = useAuth();
  const { dark, toggle } = useTheme();
  const { t } = useLang();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  const googleLogin = async (idToken: string) => {
    setError("");
    setBusy(true);
    try {
      await loginWithGoogle(idToken);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4">
      <button
        onClick={toggle}
        className="absolute right-5 top-5 grid h-[38px] w-[38px] place-items-center rounded-[11px] text-ink-soft transition hover:bg-surface-2 hover:text-ink"
        title={t("common.toggleTheme")}
      >
        {dark ? <IconSun size={19} /> : <IconMoon size={19} />}
      </button>

      <div className="grid w-full max-w-4xl overflow-hidden rounded-[28px] border border-line bg-surface shadow-maple md:grid-cols-2">
        {/* Brand panel */}
        <div
          className="hidden flex-col justify-between p-10 text-white md:flex"
          style={{
            background:
              "linear-gradient(150deg, var(--accent), color-mix(in oklab, var(--accent) 60%, #6b3318))",
          }}
        >
          <div>
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/20 backdrop-blur">
              <IconMaple size={30} />
            </div>
            <h1 className="mt-8 font-display text-3xl font-bold leading-tight">
              Maple 🍁
            </h1>
            <p className="mt-3 text-white/80">{t("login.tagline")}</p>
          </div>
          <ul className="space-y-3 text-sm text-white/85">
            <li className="flex items-center gap-2">{t("login.feature1")}</li>
            <li className="flex items-center gap-2">{t("login.feature2")}</li>
            <li className="flex items-center gap-2">{t("login.feature3")}</li>
          </ul>
        </div>

        {/* Form panel */}
        <div className="p-8 sm:p-10">
          <h2 className="font-display text-2xl font-bold text-ink">
            {t("login.signIn")}
          </h2>
          <p className="mt-1 text-sm text-ink-faint">{t("login.welcomeBack")}</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <Field
              label={t("login.email")}
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
            />
            <Field
              label={t("login.password")}
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="••••••••"
            />

            {error && (
              <p className="rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
                {error}
              </p>
            )}

            <button
              disabled={busy}
              className="w-full rounded-xl py-3 font-semibold text-white shadow-maple-sm transition hover:brightness-105 disabled:opacity-60"
              style={{ background: "var(--accent)" }}
            >
              {busy ? t("login.processing") : t("login.signIn")}
            </button>
          </form>

          <div className="mt-5 flex items-center gap-3 text-xs text-ink-faint">
            <span className="h-px flex-1 bg-line" />
            {t("login.or")}
            <span className="h-px flex-1 bg-line" />
          </div>

          <div className="mt-4">
            <GoogleSignInButton onCredential={googleLogin} />
          </div>

          <p className="mt-6 text-center text-sm text-ink-faint">
            {t("login.adminIssued")}
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-ink-soft">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        className="w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-ink outline-none transition focus:border-accent placeholder:text-ink-faint"
      />
    </div>
  );
}
```

- [ ] **Step 4: Cập nhật `frontend/src/i18n/translations.ts`**

Trong **cả hai** block vi và en:

XÓA các key: `login.createAccount`, `login.fillToStart`, `login.fullName`, `login.fullNamePlaceholder`, `login.role`, `login.register`, `login.noAccount`, `login.haveAccount`, `login.registerNow`, `login.demoAccounts`, `login.demoPassword`.

THÊM các key (block vi):

```ts
  "login.or": "hoặc",
  "login.adminIssued":
    "Tài khoản do Quản trị viên cấp qua email. Chưa có? Liên hệ Admin.",
```

Block en:

```ts
  "login.or": "or",
  "login.adminIssued":
    "Accounts are issued by the Administrator via email. Need one? Contact your admin.",
```

Sau đó grep toàn frontend để chắc không còn nơi nào dùng key đã xóa:
Run: `cd frontend; npx tsc --noEmit` (và tìm `registerNow|demoAccounts|fillToStart` trong `src/` — phải 0 kết quả ngoài translations).

- [ ] **Step 5: Kiểm tra ChatSessionContext** — file này có nhắc `register` (grep từ trước). Mở `frontend/src/chat/ChatSessionContext.tsx`, xác nhận `register` ở đó là khái niệm khác (đăng ký callback nội bộ, không phải auth) — nếu là auth thì sửa; nếu không, để nguyên.

- [ ] **Step 6: Build verify**

Run: `cd frontend; npm run build`
Expected: build thành công, 0 lỗi TypeScript.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): Google sign-in button, remove self-registration UI"
```

---

### Task 10: Frontend — AdminPage form tạo tài khoản

**Files:**
- Modify: `frontend/src/pages/AdminPage.tsx`
- Modify: `frontend/src/i18n/translations.ts`

- [ ] **Step 1: Thêm i18n keys**

Block vi:

```ts
  "admin.createUser": "Tạo tài khoản",
  "admin.createUserHint":
    "Mật khẩu tự sinh và gửi tới email người dùng. Họ cũng có thể đăng nhập bằng Google với email này.",
  "admin.fullName": "Họ và tên",
  "admin.email": "Email",
  "admin.role": "Vai trò",
  "admin.create": "Tạo",
  "admin.creating": "Đang tạo…",
  "admin.created": "Đã tạo tài khoản và gửi email tới {email}.",
  "admin.createdNoEmail":
    "Đã tạo tài khoản nhưng gửi email thất bại. Mật khẩu tạm: {password} — hãy gửi cho người dùng.",
```

Block en:

```ts
  "admin.createUser": "Create account",
  "admin.createUserHint":
    "A password is generated and emailed to the user. They can also sign in with Google using this email.",
  "admin.fullName": "Full name",
  "admin.email": "Email",
  "admin.role": "Role",
  "admin.create": "Create",
  "admin.creating": "Creating…",
  "admin.created": "Account created — credentials emailed to {email}.",
  "admin.createdNoEmail":
    "Account created but the email failed to send. Temp password: {password} — share it with the user.",
```

(Interpolation `{email}` / `{password}` dùng đúng cơ chế sẵn có như `admin.deleteUserConfirm`.)

- [ ] **Step 2: Thêm form vào `frontend/src/pages/AdminPage.tsx`**

Thêm state + handler trong `AdminPage` (sau `const [users, setUsers] = ...`):

```tsx
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState<Role>("USER");
  const [creating, setCreating] = useState(false);
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(
    null
  );

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotice(null);
    setCreating(true);
    try {
      const { data } = await api.post<{
        user: User;
        email_sent: boolean;
        temp_password: string | null;
      }>("/users", { email: newEmail, full_name: newName, role: newRole });
      setNotice({
        ok: true,
        text: data.email_sent
          ? t("admin.created", { email: data.user.email })
          : t("admin.createdNoEmail", { password: data.temp_password ?? "" }),
      });
      setNewEmail("");
      setNewName("");
      setNewRole("USER");
      load();
    } catch (err: any) {
      setNotice({
        ok: false,
        text: err.response?.data?.detail ?? t("common.error"),
      });
    } finally {
      setCreating(false);
    }
  };
```

Thêm JSX card form ngay **trước** `<div className="overflow-hidden rounded-[20px] border border-line bg-surface">` (bảng users):

```tsx
        {/* FR-ADM-01: Admin cấp tài khoản — mật khẩu tự sinh gửi qua email */}
        <form
          onSubmit={createUser}
          className="mb-6 rounded-[20px] border border-line bg-surface p-5"
        >
          <h2 className="font-display text-lg font-bold text-ink">
            {t("admin.createUser")}
          </h2>
          <p className="mt-1 text-xs text-ink-faint">
            {t("admin.createUserHint")}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto_auto]">
            <input
              type="email"
              required
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder={t("admin.email")}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            <input
              required
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder={t("admin.fullName")}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent placeholder:text-ink-faint"
            />
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as Role)}
              className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            >
              <option value="USER">{t("role.USER")}</option>
              <option value="LECTURER">{t("role.LECTURER")}</option>
            </select>
            <button
              disabled={creating}
              className="rounded-xl px-5 py-2 text-sm font-semibold text-white transition hover:brightness-105 disabled:opacity-60"
              style={{ background: "var(--accent)" }}
            >
              {creating ? t("admin.creating") : t("admin.create")}
            </button>
          </div>
          {notice && (
            <p
              className={`mt-3 rounded-xl px-4 py-2.5 text-sm ${
                notice.ok
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                  : "bg-danger/10 text-danger"
              }`}
            >
              {notice.text}
            </p>
          )}
        </form>
```

- [ ] **Step 3: Build verify**

Run: `cd frontend; npm run build`
Expected: build thành công.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AdminPage.tsx frontend/src/i18n/translations.ts
git commit -m "feat(admin): create-account form with emailed credentials (FR-ADM-01)"
```

---

### Task 11: Cấu hình deploy — Vercel + Render + README

**Files:**
- Create: `frontend/vercel.json`
- Create: `render.yaml`
- Modify: `README.md` (thêm mục Deploy)

- [ ] **Step 1: Tạo `frontend/vercel.json`**

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

- [ ] **Step 2: Tạo `render.yaml`** (repo root)

```yaml
# Render Blueprint — backend FastAPI (free tier).
# Dữ liệu bền vững nằm trên Neon Postgres (DATABASE_URL + VECTOR_BACKEND=pgvector)
# vì disk free tier là ephemeral.
services:
  - type: web
    name: maple-backend
    runtime: python
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: DATABASE_URL
        sync: false # postgresql+psycopg2://... (Neon)
      - key: VECTOR_BACKEND
        value: pgvector
      - key: EMBED_PROVIDER
        value: gemini
      - key: LLM_PROVIDER
        value: gemini
      - key: GOOGLE_API_KEY
        sync: false
      - key: GOOGLE_OAUTH_CLIENT_ID
        sync: false
      - key: SMTP_USER
        sync: false
      - key: SMTP_PASSWORD
        sync: false
      - key: APP_LOGIN_URL
        sync: false # https://<app>.vercel.app
      - key: ADMIN_EMAIL
        sync: false
      - key: ADMIN_PASSWORD
        sync: false
      - key: JWT_SECRET
        generateValue: true
      - key: CORS_ORIGINS
        sync: false # thêm https://<app>.vercel.app
```

- [ ] **Step 3: Thêm mục "Deploy (free)" vào `README.md`** — nội dung từng bước:

```markdown
## Deploy free: Vercel + Render + Neon

### 1. Neon (Postgres + pgvector — dữ liệu bền vững)
1. Tạo project free tại https://neon.tech → copy connection string.
2. Đổi prefix `postgresql://` thành `postgresql+psycopg2://` khi dùng làm `DATABASE_URL`.
   (pgvector được bật tự động bởi app: `CREATE EXTENSION IF NOT EXISTS vector`.)

### 2. Render (backend FastAPI)
1. https://render.com → New → Blueprint → trỏ repo này (đọc `render.yaml`).
2. Điền env: `DATABASE_URL` (Neon), `GOOGLE_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`,
   `SMTP_USER`/`SMTP_PASSWORD` (Gmail App Password), `ADMIN_EMAIL`/`ADMIN_PASSWORD`,
   `CORS_ORIGINS` (gồm domain Vercel), `APP_LOGIN_URL` (URL Vercel).
3. Lưu ý free tier: service ngủ sau ~15 phút — request đầu mất 30–60s đánh thức.

### 3. Vercel (frontend React)
1. https://vercel.com → Add New Project → import repo, **Root Directory: `frontend`**.
2. Env: `VITE_API_BASE=https://<app>.onrender.com/api`, `VITE_GOOGLE_CLIENT_ID=<client-id>`.
3. Deploy → lấy URL `https://<app>.vercel.app`, quay lại Render thêm vào `CORS_ORIGINS`.

### 4. Google OAuth Client ID (đăng nhập Google)
1. https://console.cloud.google.com → APIs & Services → Credentials →
   Create Credentials → OAuth client ID → Web application.
2. Authorized JavaScript origins: `http://localhost:5173` và `https://<app>.vercel.app`.
3. Copy Client ID → set `GOOGLE_OAUTH_CLIENT_ID` (Render) và `VITE_GOOGLE_CLIENT_ID` (Vercel) — cùng một giá trị.

### 5. Gmail App Password (gửi email cấp tài khoản)
1. Bật 2FA cho Gmail → https://myaccount.google.com/apppasswords → tạo App Password.
2. Set `SMTP_USER=<gmail của bạn>`, `SMTP_PASSWORD=<app password>` trên Render.
```

- [ ] **Step 4: Commit**

```bash
git add frontend/vercel.json render.yaml README.md
git commit -m "chore(deploy): Vercel + Render + Neon configs and deploy guide"
```

---

### Task 12: Verification cuối

- [ ] **Step 1: Toàn bộ test backend**

Run: `cd backend; python -m pytest tests/ -v`
Expected: tất cả pass.

- [ ] **Step 2: Lint/format backend**

Run: `cd backend; python -m ruff check app/ tests/; python -m black --check app/ tests/`
Expected: sạch (nếu black/ruff chưa cài thì `pip install ruff black` rồi chạy; auto-fix nếu cần và commit).

- [ ] **Step 3: Build frontend**

Run: `cd frontend; npm run build`
Expected: thành công.

- [ ] **Step 4: Smoke test thủ công local**

1. `cd backend; uvicorn app.main:app --reload --port 8000` với `.env` có `ADMIN_EMAIL`/`ADMIN_PASSWORD`.
2. `cd frontend; npm run dev` → đăng nhập admin → trang Admin → tạo tài khoản USER → thấy thông báo mật khẩu tạm (SMTP chưa cấu hình) → logout → login bằng email mới + mật khẩu tạm.
3. Xác nhận trang Login không còn tab Đăng ký.

- [ ] **Step 5: Commit cuối (nếu có sửa lint) + báo cáo**

```bash
git add -A
git commit -m "chore: lint fixes after feature work"
```

---

## Self-review (đã chạy)

- **Spec coverage:** Phần 1 → Tasks 4, 5, 6, 10; Phần 2 → Tasks 7, 9; Phần 3 → Task 3; Phần 4 → Task 8; Phần 5 → Task 11. Đủ.
- **Type consistency:** `UserCreateResult{user, email_sent, temp_password}` khớp giữa Task 4 (backend) và Task 10 (frontend). `send_account_email(to, full_name, password)` khớp Task 3 ↔ Task 4. `get_vector_store()` khớp Task 8 facade. `loginWithGoogle(idToken)` khớp Task 9 AuthContext ↔ LoginPage.
- **Lưu ý executor:** conftest set env trước khi import app — không đổi thứ tự import trong `conftest.py`.
