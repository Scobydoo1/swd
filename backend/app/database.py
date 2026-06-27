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

DB_DIALECT = engine.dialect.name
IS_MSSQL = DB_DIALECT == "mssql" or settings.database_url.startswith("mssql")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
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
    # create_all does not ALTER existing tables, so old databases need a
    # lightweight, dialect-specific migration pass.
    if IS_SQLITE:
        _run_lightweight_migrations()
    elif IS_MSSQL:
        _run_mssql_lightweight_migrations()


def ensure_schema_current() -> None:
    """Run idempotent schema fixes before ORM code touches migrated columns."""
    if IS_SQLITE:
        _run_lightweight_migrations()
    elif IS_MSSQL:
        _run_mssql_lightweight_migrations()


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
    except Exception:
        db.rollback()
        raise
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

        # FR-ROOM/FR-QZ: quiz gắn phòng + mật khẩu + hạn nộp (cột mới).
        quiz_cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(quizzes)"))
        }
        for col, ddl in (
            ("room_id", "ADD COLUMN room_id INTEGER"),
            ("password", "ADD COLUMN password VARCHAR(255)"),
            ("opens_at", "ADD COLUMN opens_at DATETIME"),
            ("closes_at", "ADD COLUMN closes_at DATETIME"),
        ):
            if quiz_cols and col not in quiz_cols:
                conn.execute(text(f"ALTER TABLE quizzes {ddl}"))


def _run_mssql_lightweight_migrations() -> None:
    """Bring existing SQL Server databases in line with the current models."""
    with engine.begin() as conn:
        if _mssql_table_exists(conn, "users"):
            if not _mssql_column_exists(conn, "users", "role_id"):
                conn.execute(text("ALTER TABLE [users] ADD role_id INTEGER NULL"))

            if _mssql_column_exists(conn, "users", "role"):
                conn.execute(
                    text(
                        "UPDATE [users] SET role_id = CASE [role] "
                        "WHEN 'ADMIN' THEN 1 WHEN 'LECTURER' THEN 2 ELSE 3 END "
                        "WHERE role_id IS NULL"
                    )
                )
            conn.execute(text("UPDATE [users] SET role_id = 3 WHERE role_id IS NULL"))
            conn.execute(
                text(
                    "UPDATE [users] SET role_id = 3 "
                    "WHERE role_id NOT IN (SELECT id FROM [roles])"
                )
            )
            conn.execute(
                text("ALTER TABLE [users] ALTER COLUMN role_id INTEGER NOT NULL")
            )
            if not _mssql_fk_exists(conn, "users", "role_id", "roles", "id"):
                conn.execute(
                    text(
                        "ALTER TABLE [users] WITH CHECK ADD CONSTRAINT "
                        "fk_users_role_id FOREIGN KEY (role_id) REFERENCES [roles] (id)"
                    )
                )
                conn.execute(
                    text("ALTER TABLE [users] CHECK CONSTRAINT fk_users_role_id")
                )
            _mssql_drop_column_if_exists(conn, "users", "role")
            _mssql_drop_column_if_exists(conn, "users", "plan")

        if _mssql_table_exists(conn, "account_requests"):
            if not _mssql_column_exists(
                conn, "account_requests", "requested_role_id"
            ):
                conn.execute(
                    text(
                        "ALTER TABLE [account_requests] "
                        "ADD requested_role_id INTEGER NULL"
                    )
                )

            if _mssql_column_exists(conn, "account_requests", "requested_role"):
                conn.execute(
                    text(
                        "UPDATE [account_requests] SET requested_role_id = CASE "
                        "[requested_role] WHEN 'ADMIN' THEN 1 "
                        "WHEN 'LECTURER' THEN 2 ELSE 3 END "
                        "WHERE requested_role_id IS NULL"
                    )
                )
            conn.execute(
                text(
                    "UPDATE [account_requests] SET requested_role_id = 3 "
                    "WHERE requested_role_id IS NULL"
                )
            )
            conn.execute(
                text(
                    "UPDATE [account_requests] SET requested_role_id = 3 "
                    "WHERE requested_role_id NOT IN (SELECT id FROM [roles])"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE [account_requests] "
                    "ALTER COLUMN requested_role_id INTEGER NOT NULL"
                )
            )
            if not _mssql_fk_exists(
                conn, "account_requests", "requested_role_id", "roles", "id"
            ):
                conn.execute(
                    text(
                        "ALTER TABLE [account_requests] WITH CHECK ADD CONSTRAINT "
                        "fk_account_requests_requested_role_id "
                        "FOREIGN KEY (requested_role_id) REFERENCES [roles] (id)"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE [account_requests] CHECK CONSTRAINT "
                        "fk_account_requests_requested_role_id"
                    )
                )
            _mssql_drop_column_if_exists(
                conn, "account_requests", "requested_role"
            )


def _mssql_table_exists(conn, table_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME = :table_name"
            ),
            {"table_name": table_name},
        ).scalar()
    )


def _mssql_column_exists(conn, table_name: str, column_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = :table_name AND COLUMN_NAME = :column_name"
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
    )


def _mssql_fk_exists(
    conn,
    table_name: str,
    column_name: str,
    ref_table_name: str,
    ref_column_name: str,
) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM sys.foreign_key_columns fkc
                JOIN sys.tables parent_table
                    ON parent_table.object_id = fkc.parent_object_id
                JOIN sys.columns parent_col
                    ON parent_col.object_id = fkc.parent_object_id
                    AND parent_col.column_id = fkc.parent_column_id
                JOIN sys.tables ref_table
                    ON ref_table.object_id = fkc.referenced_object_id
                JOIN sys.columns ref_col
                    ON ref_col.object_id = fkc.referenced_object_id
                    AND ref_col.column_id = fkc.referenced_column_id
                WHERE parent_table.name = :table_name
                    AND parent_col.name = :column_name
                    AND ref_table.name = :ref_table_name
                    AND ref_col.name = :ref_column_name
                """
            ),
            {
                "table_name": table_name,
                "column_name": column_name,
                "ref_table_name": ref_table_name,
                "ref_column_name": ref_column_name,
            },
        ).scalar()
    )


def _mssql_drop_column_if_exists(conn, table_name: str, column_name: str) -> None:
    if not _mssql_column_exists(conn, table_name, column_name):
        return
    conn.execute(
        text(
            """
            DECLARE @sql NVARCHAR(MAX) = N'';

            SELECT @sql = @sql + N'ALTER TABLE '
                + QUOTENAME(SCHEMA_NAME(t.schema_id)) + N'.' + QUOTENAME(t.name)
                + N' DROP CONSTRAINT ' + QUOTENAME(dc.name) + N';'
            FROM sys.default_constraints dc
            JOIN sys.tables t ON t.object_id = dc.parent_object_id
            JOIN sys.columns c
                ON c.object_id = dc.parent_object_id
                AND c.column_id = dc.parent_column_id
            WHERE t.name = :table_name AND c.name = :column_name;

            EXEC sp_executesql @sql;
            SET @sql = N'';

            SELECT @sql = @sql + N'DROP INDEX ' + QUOTENAME(i.name)
                + N' ON ' + QUOTENAME(SCHEMA_NAME(t.schema_id))
                + N'.' + QUOTENAME(t.name) + N';'
            FROM sys.indexes i
            JOIN sys.index_columns ic
                ON ic.object_id = i.object_id AND ic.index_id = i.index_id
            JOIN sys.tables t ON t.object_id = i.object_id
            JOIN sys.columns c
                ON c.object_id = ic.object_id AND c.column_id = ic.column_id
            WHERE t.name = :table_name
                AND c.name = :column_name
                AND i.is_primary_key = 0
                AND i.is_unique_constraint = 0;

            EXEC sp_executesql @sql;
            SET @sql = N'';

            SELECT @sql = @sql + N'ALTER TABLE '
                + QUOTENAME(SCHEMA_NAME(t.schema_id)) + N'.' + QUOTENAME(t.name)
                + N' DROP CONSTRAINT ' + QUOTENAME(cc.name) + N';'
            FROM sys.check_constraints cc
            JOIN sys.tables t ON t.object_id = cc.parent_object_id
            WHERE t.name = :table_name
                AND cc.definition LIKE N'%' + :column_name + N'%';

            EXEC sp_executesql @sql;
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    conn.execute(
        text(f"ALTER TABLE [{table_name}] DROP COLUMN [{column_name}]")
    )
