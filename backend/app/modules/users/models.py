import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    LECTURER = "LECTURER"
    USER = "USER"


class Plan(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    MAX = "MAX"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    plan: Mapped[Plan] = mapped_column(Enum(Plan), default=Plan.FREE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
