import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    LECTURER = "LECTURER"
    USER = "USER"


# Role được tách thành entity riêng (bảng roles) — users tham chiếu qua role_id
# (FK) thay vì nhúng enum vào cột. id cố định để map enum <-> khóa ngoại mà
# không cần truy DB; enum Role vẫn là "mã vai trò" dùng cho require_role(...).
ROLE_IDS: dict[Role, int] = {Role.ADMIN: 1, Role.LECTURER: 2, Role.USER: 3}
ID_TO_ROLE: dict[int, Role] = {v: k for k, v in ROLE_IDS.items()}

ROLE_SEED = [
    {
        "id": 1,
        "code": "ADMIN",
        "name": "Quản trị viên",
        "description": "Toàn quyền: người dùng, tài liệu, môn học, phòng học, giám sát",
    },
    {
        "id": 2,
        "code": "LECTURER",
        "name": "Giảng viên",
        "description": "Tài liệu, môn học/chương, quiz, phòng học của mình",
    },
    {
        "id": 3,
        "code": "USER",
        "name": "Sinh viên",
        "description": "Chat hỏi đáp RAG, làm quiz, tham gia phòng học",
    },
]


class RoleModel(Base):
    """Bảng tra cứu vai trò (RBAC) — tách khỏi users để chuẩn hóa."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), default="")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), default=ROLE_IDS[Role.USER]
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # role là entity riêng (bảng roles). hybrid_property cho phép vừa dùng
    # user.role / user.role = Role.X (instance) vừa filter User.role == Role.X
    # (SQL) như khi role còn là cột enum — nhờ vậy logic require_role không đổi.
    @hybrid_property
    def role(self) -> Role:
        return ID_TO_ROLE[self.role_id]

    @role.setter
    def role(self, value: Role) -> None:
        self.role_id = ROLE_IDS[value]

    @role.expression
    def role(cls):  # noqa: N805
        return case(
            (cls.role_id == ROLE_IDS[Role.ADMIN], Role.ADMIN.value),
            (cls.role_id == ROLE_IDS[Role.LECTURER], Role.LECTURER.value),
            else_=Role.USER.value,
        )
