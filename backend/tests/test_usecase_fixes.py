"""Regression tests cho các lỗi logic use case tìm thấy khi audit toàn hệ thống.

1. FR-USR-04: Sinh viên không được chat vào phiên của người khác (session hijack).
2. FR-ADM-01: Xóa user từng đăng thông báo phòng học không được vỡ FK
   room_announcements.author_id (Postgres/Neon enforce FK).
3. FR-LEC-01/§6: Giảng viên chỉ xóa tài liệu CỦA MÌNH (uploader/chủ môn).
4. FR-LEC-01: Upload phải kiểm tra môn học tồn tại + đúng giảng viên phụ trách.
5. FR-QZ-04: Giảng viên chỉ xem lại bài làm thuộc quiz mình tạo (hoặc Admin/chủ bài).
"""
from app.database import SessionLocal
from app.modules.auth.security import create_access_token
from app.modules.users.models import Role, User


def _headers_for(email: str, role: Role) -> tuple[dict[str, str], int]:
    """Tạo user trực tiếp trong DB (nếu chưa có) và trả (Bearer header, user_id)."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash="not-a-real-hash",
                full_name=email.split("@")[0],
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(str(user.id), user.role.value)
        return {"Authorization": f"Bearer {token}"}, user.id
    finally:
        db.close()


def _create_course(client, headers, name: str) -> int:
    res = client.post(
        "/api/courses", json={"name": name, "description": ""}, headers=headers
    )
    assert res.status_code == 200, res.text
    return res.json()["id"]


# ---- 1. Chat session hijack ----


def test_student_cannot_chat_into_another_users_session(client):
    h_a, _ = _headers_for("sv.a@uni.edu", Role.USER)
    h_b, _ = _headers_for("sv.b@uni.edu", Role.USER)

    res = client.post("/api/sessions", json={"title": "phiên của A"}, headers=h_a)
    assert res.status_code == 200, res.text
    sid = res.json()["id"]

    # B cố chat tiếp vào phiên của A -> không được thấy phiên đó tồn tại.
    res = client.post(
        "/api/chat",
        json={"session_id": sid, "question": "câu hỏi lén vào phiên người khác"},
        headers=h_b,
    )
    assert res.status_code == 404, res.text

    # Chính chủ vẫn chat được bình thường.
    res = client.post(
        "/api/chat",
        json={"session_id": sid, "question": "câu hỏi của chính chủ"},
        headers=h_a,
    )
    assert res.status_code == 200, res.text


# ---- 2. Xóa user từng đăng thông báo ----


def test_delete_user_who_posted_announcements(client, admin_headers):
    from app.modules.rooms.models import Announcement

    h_gv, gv_id = _headers_for("gv.ann@uni.edu", Role.LECTURER)
    cid = _create_course(client, h_gv, "Môn của GV đăng thông báo")
    res = client.post(
        "/api/rooms",
        json={"name": "Phòng có thông báo", "description": "", "course_id": cid},
        headers=h_gv,
    )
    assert res.status_code == 201, res.text
    rid = res.json()["id"]
    res = client.post(
        f"/api/rooms/{rid}/announcements",
        json={"content": "Chào lớp!"},
        headers=h_gv,
    )
    assert res.status_code == 201, res.text

    # Xóa GV: phải thành công; thông báo giữ lại nhưng gỡ liên kết tác giả.
    res = client.delete(f"/api/users/{gv_id}", headers=admin_headers)
    assert res.status_code == 204, res.text

    db = SessionLocal()
    try:
        anns = db.query(Announcement).filter(Announcement.room_id == rid).all()
        assert len(anns) == 1
        assert anns[0].author_id is None
    finally:
        db.close()


# ---- 3. Ownership khi xóa tài liệu ----


def _create_document(course_id: int, uploaded_by: int) -> int:
    from app.modules.documents.models import Document, FileType, Status

    db = SessionLocal()
    try:
        doc = Document(
            course_id=course_id,
            uploaded_by=uploaded_by,
            filename="tai-lieu.pdf",
            file_type=FileType.PDF,
            status=Status.INDEXED,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.id
    finally:
        db.close()


def test_lecturer_cannot_delete_others_document(client):
    h_owner, owner_id = _headers_for("gv.owner@uni.edu", Role.LECTURER)
    h_other, _ = _headers_for("gv.other@uni.edu", Role.LECTURER)

    cid = _create_course(client, h_owner, "Môn tài liệu của owner")
    did = _create_document(cid, owner_id)

    # Giảng viên khác không xóa được tài liệu của người khác.
    assert client.delete(f"/api/documents/{did}", headers=h_other).status_code == 403
    # Chính chủ (uploader kiêm chủ môn) xóa được.
    assert client.delete(f"/api/documents/{did}", headers=h_owner).status_code == 204


def test_admin_can_delete_any_document(client, admin_headers):
    h_owner, owner_id = _headers_for("gv.owner@uni.edu", Role.LECTURER)
    cid = _create_course(client, h_owner, "Môn tài liệu admin xóa")
    did = _create_document(cid, owner_id)
    assert client.delete(f"/api/documents/{did}", headers=admin_headers).status_code == 204


# ---- 4. Upload: môn phải tồn tại + đúng giảng viên phụ trách ----


def test_upload_validates_course_and_ownership(client):
    h_owner, _ = _headers_for("gv.owner@uni.edu", Role.LECTURER)
    h_other, _ = _headers_for("gv.other@uni.edu", Role.LECTURER)
    cid = _create_course(client, h_owner, "Môn upload ownership")

    files = {"file": ("x.pdf", b"%PDF-1.4 junk", "application/pdf")}

    # Giảng viên khác upload vào môn không phụ trách -> 403.
    res = client.post(
        "/api/documents", data={"course_id": str(cid)}, files=files, headers=h_other
    )
    assert res.status_code == 403, res.text

    # Môn không tồn tại -> 404.
    res = client.post(
        "/api/documents",
        data={"course_id": "999999"},
        files=files,
        headers=h_owner,
    )
    assert res.status_code == 404, res.text


# ---- 5. Quyền xem lại bài làm quiz ----


def test_attempt_review_scoped_to_quiz_creator(client, admin_headers):
    from app.modules.courses.models import Course
    from app.modules.quizzes.models import Question, Quiz, QuizAttempt

    h_creator, creator_id = _headers_for("gv.quiz@uni.edu", Role.LECTURER)
    h_other, _ = _headers_for("gv.other2@uni.edu", Role.LECTURER)
    h_sv, sv_id = _headers_for("sv.quiz@uni.edu", Role.USER)

    db = SessionLocal()
    try:
        course = Course(name="Môn quiz review", owner_id=creator_id)
        db.add(course)
        db.flush()
        quiz = Quiz(course_id=course.id, title="Quiz review", created_by=creator_id)
        quiz.questions.append(
            Question(text="1+1?", options_json='["1","2"]', correct_index=1, order=0)
        )
        db.add(quiz)
        db.flush()
        attempt = QuizAttempt(
            quiz_id=quiz.id, user_id=sv_id, score=100.0, answers_json="[1]"
        )
        db.add(attempt)
        db.commit()
        attempt_id = attempt.id
    finally:
        db.close()

    # Giảng viên KHÔNG tạo quiz -> không xem được bài làm.
    assert (
        client.get(f"/api/quizzes/attempts/{attempt_id}", headers=h_other).status_code
        == 403
    )
    # Người tạo quiz, chính chủ bài làm và Admin đều xem được.
    for h in (h_creator, h_sv, admin_headers):
        assert (
            client.get(f"/api/quizzes/attempts/{attempt_id}", headers=h).status_code
            == 200
        )
