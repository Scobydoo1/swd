from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.courses.repository import CourseRepository
from app.modules.documents.schemas import DocumentOut
from app.modules.documents.service import DocumentService
from app.modules.quizzes.service import QuizService
from app.modules.rooms.models import Room
from app.modules.rooms.repository import RoomRepository
from app.modules.rooms.schemas import (
    MemberOut,
    RoomCreate,
    RoomDetail,
    RoomOut,
    StudentOut,
)
from app.modules.users.models import Role, User
from app.modules.users.repository import UserRepository


class RoomService:
    """FR-ROOM: Phòng học — Lecturer/Admin tạo, mời Sinh viên, giao quiz + tài liệu."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RoomRepository(db)
        self.courses = CourseRepository(db)
        self.users = UserRepository(db)

    # FR-ROOM-01: Chỉ Lecturer/Admin tạo phòng (role guard ở router).
    def create(self, payload: RoomCreate, user: User) -> RoomOut:
        if not self.courses.get(payload.course_id):
            raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
        room = self.repo.create(
            payload.name, payload.description, payload.course_id, user.id
        )
        return self._to_out(room)

    # FR-ROOM-02: Admin thấy mọi phòng; Lecturer phòng mình tạo; SV phòng được mời.
    def list_for(self, user: User) -> list[RoomOut]:
        if user.role == Role.ADMIN:
            rooms = self.repo.list_all()
        elif user.role == Role.LECTURER:
            rooms = self.repo.list_created_by(user.id)
        else:
            rooms = self.repo.list_joined(user.id)
        return [self._to_out(r) for r in rooms]

    # FR-ROOM-03: Chi tiết phòng = thành viên + quiz + tài liệu của môn.
    def detail(self, room_id: int, user: User) -> RoomDetail:
        room = self._require_access(room_id, user)
        members = []
        for m in sorted(room.members, key=lambda x: x.added_at):
            u = self.users.get(m.user_id)
            if u:
                members.append(
                    MemberOut(
                        user_id=u.id,
                        full_name=u.full_name,
                        email=u.email,
                        added_at=m.added_at,
                    )
                )
        quizzes = QuizService(self.db).list(room.course_id)
        documents = [
            DocumentOut.model_validate(d)
            for d in DocumentService(self.db).list(room.course_id)
        ]
        base = self._to_out(room)
        return RoomDetail(
            **base.model_dump(),
            members=members,
            quizzes=quizzes,
            documents=documents,
        )

    # FR-ROOM-04: Người tạo phòng / Admin mời Sinh viên qua email.
    def invite(self, room_id: int, email: str, user: User) -> MemberOut:
        room = self._require_manage(room_id, user)
        student = self.users.get_by_email(email)
        if not student:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy người dùng với email này"
            )
        if student.role != Role.USER:
            raise HTTPException(
                status_code=400, detail="Chỉ mời được tài khoản Sinh viên vào phòng"
            )
        if self.repo.get_member(room.id, student.id):
            raise HTTPException(
                status_code=400, detail="Sinh viên đã ở trong phòng"
            )
        member = self.repo.add_member(room.id, student.id)
        return MemberOut(
            user_id=student.id,
            full_name=student.full_name,
            email=student.email,
            added_at=member.added_at,
        )

    def remove_member(self, room_id: int, user_id: int, user: User) -> None:
        room = self._require_manage(room_id, user)
        member = self.repo.get_member(room.id, user_id)
        if not member:
            raise HTTPException(
                status_code=404, detail="Sinh viên không ở trong phòng"
            )
        self.repo.remove_member(member)

    def delete(self, room_id: int, user: User) -> None:
        room = self._require_manage(room_id, user)
        self.repo.delete(room)

    # Danh sách Sinh viên để Lecturer/Admin chọn khi mời.
    def list_students(self) -> list[StudentOut]:
        return [
            StudentOut(id=u.id, full_name=u.full_name, email=u.email)
            for u in self.users.list()
            if u.role == Role.USER
        ]

    # ---- helpers ----

    def _require(self, room_id: int) -> Room:
        room = self.repo.get(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")
        return room

    def _require_access(self, room_id: int, user: User) -> Room:
        room = self._require(room_id)
        if user.role == Role.ADMIN or room.created_by == user.id:
            return room
        if self.repo.get_member(room.id, user.id):
            return room
        raise HTTPException(
            status_code=403, detail="Bạn không phải thành viên của phòng này"
        )

    def _require_manage(self, room_id: int, user: User) -> Room:
        room = self._require(room_id)
        if user.role != Role.ADMIN and room.created_by != user.id:
            raise HTTPException(
                status_code=403,
                detail="Chỉ người tạo phòng hoặc Admin được quản lý phòng",
            )
        return room

    def _to_out(self, room: Room) -> RoomOut:
        course = self.courses.get(room.course_id)
        num_quizzes = len(QuizService(self.db).list(room.course_id))
        return RoomOut(
            id=room.id,
            name=room.name,
            description=room.description,
            course_id=room.course_id,
            course_name=course.name if course else "",
            created_by=room.created_by,
            num_members=len(room.members),
            num_quizzes=num_quizzes,
            created_at=room.created_at,
        )
