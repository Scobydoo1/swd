"""FR-LEC-02 / FR-ADM-02: Xóa môn học kèm dọn dữ liệu liên quan.

Tái hiện lỗi production: Giảng viên xóa môn có phòng học kèm THÔNG BÁO
(room_announcements.room_id FK -> rooms.id). CourseService.delete xóa Room
nhưng bỏ sót Announcement -> vỡ FK trên Postgres/Neon -> 500, Giảng viên
không xóa được môn học của mình.
"""


def test_lecturer_deletes_own_course_with_room_announcement(
    client, lecturer_headers
):
    # Giảng viên tạo môn -> phòng học -> đăng thông báo trong phòng.
    res = client.post(
        "/api/courses",
        json={"name": "Môn test xóa (có phòng + thông báo)", "description": ""},
        headers=lecturer_headers,
    )
    assert res.status_code == 200, res.text
    course_id = res.json()["id"]

    res = client.post(
        "/api/rooms",
        json={"name": "Lớp test xóa môn", "description": "", "course_id": course_id},
        headers=lecturer_headers,
    )
    assert res.status_code == 201, res.text
    room_id = res.json()["id"]

    res = client.post(
        f"/api/rooms/{room_id}/announcements",
        json={"content": "Chào cả lớp!"},
        headers=lecturer_headers,
    )
    assert res.status_code == 201, res.text

    # Giảng viên (chủ môn) xóa môn học -> phải thành công.
    res = client.delete(f"/api/courses/{course_id}", headers=lecturer_headers)
    assert res.status_code == 204, res.text

    # Không để lại bản ghi mồ côi: phòng + thông báo phải bị dọn cùng môn.
    from app.database import SessionLocal
    from app.modules.courses.models import Course
    from app.modules.rooms.models import Announcement, Room

    db = SessionLocal()
    try:
        assert db.query(Course).filter(Course.id == course_id).count() == 0
        assert db.query(Room).filter(Room.course_id == course_id).count() == 0
        assert (
            db.query(Announcement)
            .filter(Announcement.room_id == room_id)
            .count()
            == 0
        )
    finally:
        db.close()


def test_lecturer_cannot_delete_other_lecturers_course(client, lecturer_headers):
    """Giảng viên KHÔNG được xóa môn của giảng viên khác -> 403."""
    from app.database import SessionLocal
    from app.modules.courses.models import Course

    db = SessionLocal()
    try:
        other = Course(name="Môn của GV khác", owner_id=None)
        db.add(other)
        db.commit()
        db.refresh(other)
        other_id = other.id
    finally:
        db.close()

    res = client.delete(f"/api/courses/{other_id}", headers=lecturer_headers)
    assert res.status_code == 403
