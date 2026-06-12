def _create_user(client, admin_headers, email: str) -> int:
    res = client.post(
        "/api/users",
        json={"email": email, "full_name": "User Xoa", "role": "USER"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    return res.json()["user"]["id"]


def test_delete_user_with_chat_history(client, admin_headers):
    """Tái hiện lỗi production: xóa user còn phiên chat + messages.

    Trên Postgres (Neon) từng vỡ FK chat_sessions_user_id_fkey vì thứ tự
    DELETE không đảm bảo (User và ChatSession không có relationship ORM).
    """
    from app.database import SessionLocal
    from app.modules.chat.models import ChatSession, Message, MsgRole

    uid = _create_user(client, admin_headers, "delme.chat@uni.edu")

    db = SessionLocal()
    try:
        s = ChatSession(user_id=uid, title="phiên test")
        db.add(s)
        db.commit()
        db.refresh(s)
        db.add(Message(session_id=s.id, role=MsgRole.USER, content="hi"))
        db.commit()
        sid = s.id
    finally:
        db.close()

    res = client.delete(f"/api/users/{uid}", headers=admin_headers)
    assert res.status_code == 204

    db = SessionLocal()
    try:
        assert db.query(ChatSession).filter(ChatSession.id == sid).count() == 0
        assert db.query(Message).filter(Message.session_id == sid).count() == 0
    finally:
        db.close()


def test_delete_lecturer_keeps_shared_content(client, admin_headers):
    """Xóa giảng viên: môn học/tài liệu giữ lại nhưng gỡ liên kết chủ sở hữu."""
    from app.database import SessionLocal
    from app.modules.courses.models import Course

    res = client.post(
        "/api/users",
        json={
            "email": "delme.gv@uni.edu",
            "full_name": "GV Xoa",
            "role": "LECTURER",
        },
        headers=admin_headers,
    )
    uid = res.json()["user"]["id"]

    db = SessionLocal()
    try:
        course = Course(name="Môn test xóa GV", owner_id=uid)
        db.add(course)
        db.commit()
        db.refresh(course)
        cid = course.id
    finally:
        db.close()

    assert client.delete(f"/api/users/{uid}", headers=admin_headers).status_code == 204

    db = SessionLocal()
    try:
        kept = db.query(Course).filter(Course.id == cid).one()
        assert kept.owner_id is None
    finally:
        db.close()
