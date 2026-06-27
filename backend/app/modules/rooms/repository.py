from sqlalchemy.orm import Session

from app.modules.rooms.models import Announcement, Room, RoomMember


class RoomRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, name: str, description: str, course_id: int, created_by: int
    ) -> Room:
        room = Room(
            name=name,
            description=description,
            course_id=course_id,
            created_by=created_by,
        )
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def get(self, room_id: int) -> Room | None:
        return self.db.query(Room).filter(Room.id == room_id).first()

    def list_all(self) -> list[Room]:
        return self.db.query(Room).order_by(Room.created_at.desc()).all()

    def list_created_by(self, user_id: int) -> list[Room]:
        return (
            self.db.query(Room)
            .filter(Room.created_by == user_id)
            .order_by(Room.created_at.desc())
            .all()
        )

    def list_joined(self, user_id: int) -> list[Room]:
        return (
            self.db.query(Room)
            .join(RoomMember, RoomMember.room_id == Room.id)
            .filter(RoomMember.user_id == user_id)
            .order_by(Room.created_at.desc())
            .all()
        )

    def get_member(self, room_id: int, user_id: int) -> RoomMember | None:
        return (
            self.db.query(RoomMember)
            .filter(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
            .first()
        )

    def add_member(self, room_id: int, user_id: int) -> RoomMember:
        member = RoomMember(room_id=room_id, user_id=user_id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, member: RoomMember) -> None:
        self.db.delete(member)
        self.db.commit()

    def delete(self, room: Room) -> None:
        # members xóa theo cascade ORM (delete-orphan).
        self.db.query(Announcement).filter(
            Announcement.room_id == room.id
        ).delete()
        self.db.delete(room)
        self.db.commit()

    # ---- Bảng tin / thông báo ----

    def list_announcements(self, room_id: int) -> list[Announcement]:
        return (
            self.db.query(Announcement)
            .filter(Announcement.room_id == room_id)
            .order_by(Announcement.created_at.desc())
            .all()
        )

    def add_announcement(
        self, room_id: int, author_id: int | None, content: str
    ) -> Announcement:
        ann = Announcement(
            room_id=room_id, author_id=author_id, content=content
        )
        self.db.add(ann)
        self.db.commit()
        self.db.refresh(ann)
        return ann

    def get_announcement(self, ann_id: int) -> Announcement | None:
        return (
            self.db.query(Announcement)
            .filter(Announcement.id == ann_id)
            .first()
        )

    def remove_announcement(self, ann: Announcement) -> None:
        self.db.delete(ann)
        self.db.commit()
