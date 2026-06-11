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
