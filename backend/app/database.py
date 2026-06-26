import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Hỗ trợ cả SQLite (mặc định, chạy ngay) lẫn SQL Server (mssql+pyodbc).
# Đổi DATABASE_URL trong .env để chuyển — xem README mục "Kết nối SQL Server".
IS_SQLITE = settings.database_url.startswith("sqlite")

if IS_SQLITE:
    # SQLite: tạo sẵn thư mục chứa file .db + tắt check_same_thread cho FastAPI.
    _db_path = settings.database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(_db_path)), exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
else:
    # SQL Server / DB khác: pool_pre_ping tránh dùng connection đã chết.
    engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register on Base before create_all.
    from app.modules.users import models as user_models  # noqa: F401
    from app.modules.courses import models as course_models  # noqa: F401
    from app.modules.documents import models as doc_models  # noqa: F401
    from app.modules.chat import models as chat_models  # noqa: F401
    from app.modules.quizzes import models as quiz_models  # noqa: F401
    from app.modules.rooms import models as room_models  # noqa: F401
    from app.modules.account_requests import models as req_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _seed_roles()
    # Migration tay chỉ cần cho SQLite cũ; SQL Server luôn tạo mới đủ cột
    # qua create_all nên bỏ qua (PRAGMA là cú pháp riêng của SQLite).
    if IS_SQLITE:
        _run_lightweight_migrations()


def _seed_roles() -> None:
    """Seed 3 vai trò cố định (ADMIN/LECTURER/USER) vào bảng roles.

    Idempotent: chỉ thêm khi chưa có. Chạy cho mọi backend vì users.role_id
    là FK trỏ tới đây — phải có sẵn trước khi tạo bất kỳ user nào.
    """
    from app.modules.users.models import ROLE_SEED, RoleModel

    db = SessionLocal()
    try:
        for r in ROLE_SEED:
            if db.get(RoleModel, r["id"]) is None:
                db.add(RoleModel(**r))
        db.commit()
    finally:
        db.close()


def _run_lightweight_migrations() -> None:
    """Thêm cột mới vào bảng đã tồn tại (create_all không tự ALTER).

    Dự án không dùng Alembic cho gọn, nên đây là "migration tay" idempotent:
    chỉ ALTER khi cột chưa có. Chỉ dùng cho SQLite (PRAGMA table_info).
    """
    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(chat_sessions)"))
        }
        if "pinned" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE chat_sessions "
                    "ADD COLUMN pinned BOOLEAN NOT NULL DEFAULT 0"
                )
            )

        user_cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(users)"))
        }
        # Đã bỏ subscription: gỡ cột plan cũ nếu DB cũ còn (SQLite 3.35+).
        if "plan" in user_cols:
            conn.execute(text("ALTER TABLE users DROP COLUMN plan"))

        # role (enum) -> roles table: thêm role_id, backfill từ cột role cũ rồi
        # bỏ cột role (SQLite 3.35+ hỗ trợ DROP COLUMN; Python 3.11 đủ mới).
        if "role_id" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN role_id INTEGER"))
            if "role" in user_cols:
                conn.execute(
                    text(
                        "UPDATE users SET role_id = CASE role "
                        "WHEN 'ADMIN' THEN 1 WHEN 'LECTURER' THEN 2 ELSE 3 END"
                    )
                )
                conn.execute(text("ALTER TABLE users DROP COLUMN role"))
            else:
                conn.execute(
                    text("UPDATE users SET role_id = 3 WHERE role_id IS NULL")
                )

        # account_requests.requested_role (enum) -> requested_role_id (FK roles).
        req_cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(account_requests)"))
        }
        if req_cols and "requested_role_id" not in req_cols:
            conn.execute(
                text("ALTER TABLE account_requests ADD COLUMN requested_role_id INTEGER")
            )
            if "requested_role" in req_cols:
                conn.execute(
                    text(
                        "UPDATE account_requests SET requested_role_id = CASE "
                        "requested_role WHEN 'ADMIN' THEN 1 "
                        "WHEN 'LECTURER' THEN 2 ELSE 3 END"
                    )
                )
                conn.execute(
                    text("ALTER TABLE account_requests DROP COLUMN requested_role")
                )
            else:
                conn.execute(
                    text(
                        "UPDATE account_requests SET requested_role_id = 3 "
                        "WHERE requested_role_id IS NULL"
                    )
                )
