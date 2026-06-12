from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# FR-ROOM: Phòng học do Lecturer/Admin tạo, gắn với một môn học. Quiz và tài
# liệu của môn tự xuất hiện trong phòng; Lecturer mời Sinh viên vào làm bài.
class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000), default="")
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    members: Mapped[list["RoomMember"]] = relationship(
        cascade="all, delete-orphan", backref="room"
    )


class RoomMember(Base):
    __tablename__ = "room_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
