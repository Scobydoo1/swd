from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.rooms.schemas import (
    AnnouncementCreate,
    AnnouncementOut,
    InviteRequest,
    MemberOut,
    RoomCreate,
    RoomDetail,
    RoomGradeRow,
    RoomOut,
    StudentOut,
)
from app.modules.rooms.service import RoomService
from app.modules.users.models import Role
from app.shared.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


# FR-ROOM-01: Tạo phòng học — chỉ Lecturer/Admin.
@router.post("", response_model=RoomOut, status_code=201)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return RoomService(db).create(payload, user)


# FR-ROOM-02: Danh sách phòng theo vai trò (Admin/Lecturer/Student).
@router.get("", response_model=list[RoomOut])
def list_rooms(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return RoomService(db).list_for(user)


# Danh sách Sinh viên để mời (đặt trước /{room_id} để không bị nuốt route).
@router.get("/students", response_model=list[StudentOut])
def list_students(
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return RoomService(db).list_students()


# FR-ROOM-03: Chi tiết phòng — thành viên + quiz + tài liệu của môn.
@router.get("/{room_id}", response_model=RoomDetail)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return RoomService(db).detail(room_id, user)


# FR-ROOM-04: Mời Sinh viên vào phòng — người tạo phòng / Admin.
@router.post("/{room_id}/members", response_model=MemberOut, status_code=201)
def invite_member(
    room_id: int,
    payload: InviteRequest,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return RoomService(db).invite(room_id, payload.email, user)


@router.delete("/{room_id}/members/{user_id}", status_code=204)
def remove_member(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    RoomService(db).remove_member(room_id, user_id, user)


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    RoomService(db).delete(room_id, user)


# FR-ROOM-05: Bảng tin — thành viên xem; người tạo phòng / Admin đăng & xoá.
@router.post(
    "/{room_id}/announcements", response_model=AnnouncementOut, status_code=201
)
def post_announcement(
    room_id: int,
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return RoomService(db).add_announcement(room_id, payload.content, user)


@router.delete("/{room_id}/announcements/{ann_id}", status_code=204)
def delete_announcement(
    room_id: int,
    ann_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    RoomService(db).delete_announcement(room_id, ann_id, user)


# FR-ROOM-06: Bảng điểm tổng của lớp — chỉ người tạo phòng / Admin.
@router.get("/{room_id}/grades", response_model=list[RoomGradeRow])
def room_grades(
    room_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.LECTURER, Role.ADMIN)),
):
    return RoomService(db).room_grades(room_id, user)
