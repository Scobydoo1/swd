from sqlalchemy.orm import Session

from app.modules.users.models import Role, User

# Sentinel để phân biệt "không truyền" với "truyền None" (xóa ảnh đại diện).
_UNSET = object()


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def list(self) -> list[User]:
        return self.db.query(User).order_by(User.created_at.desc()).all()

    def create(
        self, email: str, password_hash: str, full_name: str, role: Role
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_role(self, user: User, role: Role) -> User:
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(
        self,
        user: User,
        *,
        full_name: str | None = None,
        avatar_url=_UNSET,
    ) -> User:
        if full_name is not None:
            user.full_name = full_name
        if avatar_url is not _UNSET:  # None => xóa ảnh; bỏ qua nếu không truyền
            user.avatar_url = avatar_url
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self.db.commit()
        self.db.refresh(user)
        return user
