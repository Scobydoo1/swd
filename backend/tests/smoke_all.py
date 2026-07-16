"""Smoke test TOÀN BỘ chức năng qua API (DB SQLite tạm, không đụng data thật).

Chạy: python -m tests.smoke_all

Bao phủ: health, auth, yêu cầu tài khoản (form public + admin duyệt/từ chối),
quản lý người dùng (tạo/role/xóa), môn học/chương, tài liệu (validate định
dạng), chat + phiên (chỉ SV/Admin), quiz (tạo/làm/chấm/bảng điểm), phòng học
(tạo/mời/chi tiết/quyền).
"""
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

_tmp = tempfile.mkdtemp(prefix="maple_smoke_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/smoke.db"
os.environ["CHROMA_DIR"] = f"{_tmp}/chroma"
os.environ["EMBED_PROVIDER"] = "local"
os.environ["LLM_PROVIDER"] = "local"
os.environ["ADMIN_EMAIL"] = "admin@smokemail.com"
os.environ["ADMIN_PASSWORD"] = "admin123"
# Tắt mọi đường gửi email — kẻo .env của dev có Brevo/SMTP thật.
os.environ["BREVO_API_KEY"] = ""
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASS = 0


def check(cond: bool, label: str) -> None:
    global PASS
    assert cond, f"FAIL: {label}"
    PASS += 1
    print(f"  ok - {label}")


def login(client: TestClient, email: str, password: str) -> dict:
    r = client.post(
        "/api/auth/login", data={"username": email, "password": password}
    )
    assert r.status_code == 200, f"login {email}: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def run() -> None:  # noqa: PLR0915
    with TestClient(app) as client:
        # ---------- Health + Auth ----------
        print("\n[Health + Auth]")
        check(client.get("/api/health").json()["status"] == "ok", "Health OK")
        admin = login(client, "admin@smokemail.com", "admin123")
        r = client.post(
            "/api/auth/login",
            data={"username": "admin@smokemail.com", "password": "sai-mat-khau"},
        )
        check(r.status_code == 401, "Sai mật khẩu bị 401")

        # ---------- Yêu cầu tài khoản (FR-REQ) ----------
        print("\n[Yêu cầu tài khoản]")
        r = client.post(
            "/api/account-requests",
            json={
                "email": "lec@smokemail.com",
                "full_name": "GV Smoke",
                "role": "LECTURER",
                "message": "Em là giảng viên SE101",
            },
        )
        check(r.status_code == 201, "Public gửi yêu cầu (Lecturer)")
        req_lec = r.json()["id"]
        r = client.post(
            "/api/account-requests",
            json={"email": "lec@smokemail.com", "full_name": "GV Smoke 2"},
        )
        check(r.status_code == 400, "Email đã có yêu cầu PENDING bị chặn")
        r = client.post(
            "/api/account-requests",
            json={"email": "admin@smokemail.com", "full_name": "Giả Admin"},
        )
        check(r.status_code == 400, "Email đã có tài khoản bị chặn")
        r = client.post(
            "/api/account-requests",
            json={"email": "x@smokemail.com", "full_name": "X", "role": "ADMIN"},
        )
        check(r.status_code == 422, "Không xin được role ADMIN")
        r = client.post(
            "/api/account-requests",
            json={"email": "tu-choi@smokemail.com", "full_name": "Bị Từ Chối"},
        )
        req_rejected = r.json()["id"]
        r = client.get("/api/account-requests", params={"status": "PENDING"})
        check(r.status_code == 401, "Xem danh sách yêu cầu cần đăng nhập Admin")
        r = client.get(
            "/api/account-requests", params={"status": "PENDING"}, headers=admin
        )
        check(len(r.json()) == 2, "Admin thấy 2 yêu cầu PENDING")
        r = client.post(
            f"/api/account-requests/{req_lec}/approve", headers=admin
        )
        lec_password = r.json()["temp_password"]
        check(
            r.status_code == 200 and lec_password,
            "Duyệt yêu cầu -> tạo tài khoản + mật khẩu tạm",
        )
        r = client.post(
            f"/api/account-requests/{req_lec}/approve", headers=admin
        )
        check(r.status_code == 400, "Duyệt lại yêu cầu đã xử lý bị chặn")
        r = client.post(
            f"/api/account-requests/{req_rejected}/reject", headers=admin
        )
        check(r.json()["status"] == "REJECTED", "Từ chối yêu cầu")
        lec = login(client, "lec@smokemail.com", lec_password)
        check(True, "Đăng nhập bằng tài khoản vừa duyệt")

        # ---------- Quản lý người dùng (FR-ADM) ----------
        print("\n[Quản lý người dùng]")
        users = {}
        for email, name in [
            ("sv1@smokemail.com", "SV Một"),
            ("sv2@smokemail.com", "SV Hai"),
        ]:
            r = client.post(
                "/api/users",
                json={"email": email, "full_name": name, "role": "USER"},
                headers=admin,
            )
            check(r.status_code == 201, f"Admin tạo tài khoản {email}")
            users[email] = r.json()["temp_password"]
        sv1 = login(client, "sv1@smokemail.com", users["sv1@smokemail.com"])
        sv2 = login(client, "sv2@smokemail.com", users["sv2@smokemail.com"])
        r = client.get("/api/users", headers=sv1)
        check(r.status_code == 403, "SV không xem được danh sách người dùng")
        r = client.get("/api/users", headers=admin)
        all_users = {u["email"]: u for u in r.json()}
        check(len(all_users) == 4, "Admin thấy đủ 4 người dùng")
        sv2_id = all_users["sv2@smokemail.com"]["id"]

        # ---------- Môn học / chương (FR-LEC-02) ----------
        print("\n[Môn học]")
        r = client.post(
            "/api/courses",
            json={"name": "Môn Smoke", "description": "demo"},
            headers=lec,
        )
        check(r.status_code == 200, "Lecturer tạo môn học")
        course_id = r.json()["id"]
        r = client.post(
            "/api/courses", json={"name": "Môn SV", "description": ""}, headers=sv1
        )
        check(r.status_code == 403, "SV không tạo được môn học")
        r = client.get("/api/courses", headers=sv1)
        check(len(r.json()) == 1, "SV xem được danh sách môn")
        r = client.get(f"/api/courses/{course_id}/chapters", headers=sv1)
        check(r.status_code == 200, "Xem chương của môn")

        # ---------- Tài liệu (FR-LEC-01/03) ----------
        print("\n[Tài liệu]")
        r = client.post(
            "/api/documents",
            files={"file": ("hack.exe", b"MZ...", "application/octet-stream")},
            data={"course_id": str(course_id)},
            headers=lec,
        )
        check(r.status_code in (400, 415, 422), "Chặn file sai định dạng")
        r = client.post(
            "/api/documents",
            files={"file": ("bai-giang.pdf", b"%PDF-1.4", "application/pdf")},
            data={"course_id": str(course_id)},
            headers=sv1,
        )
        check(r.status_code == 403, "SV không upload được tài liệu")
        r = client.get("/api/documents", headers=sv1)
        check(r.status_code == 200, "Mọi người xem danh sách tài liệu")

        # ---------- Chat + phiên (FR-USR-02/04) ----------
        print("\n[Chat]")
        r = client.post(
            "/api/chat", json={"question": "use case là gì?"}, headers=sv1
        )
        check(
            r.status_code == 200 and "citations" in r.json(),
            "SV chat được (answer + citations)",
        )
        session_id = r.json()["session_id"]
        r = client.post("/api/chat", json={"question": "test?"}, headers=lec)
        check(r.status_code == 403, "Lecturer bị chặn chat AI")
        r = client.post("/api/sessions", json={"title": "GV"}, headers=lec)
        check(r.status_code == 403, "Lecturer bị chặn tạo phiên chat")
        r = client.get("/api/sessions", headers=sv1)
        check(len(r.json()) >= 1, "SV xem phiên của mình")
        r = client.get(f"/api/sessions/{session_id}", headers=sv2)
        check(r.status_code == 403, "SV khác không xem được phiên người khác")
        r = client.get(f"/api/sessions/{session_id}", headers=admin)
        check(r.status_code == 200, "Admin giám sát được mọi phiên")
        r = client.patch(
            f"/api/sessions/{session_id}", json={"pinned": True}, headers=sv1
        )
        check(r.json()["pinned"] is True, "Ghim phiên chat")

        # ---------- Phòng học (FR-ROOM) ----------
        print("\n[Phòng học]")
        r = client.post(
            "/api/rooms",
            json={"name": "Lớp Smoke", "description": "demo", "course_id": course_id},
            headers=lec,
        )
        check(r.status_code == 201, "Lecturer tạo phòng")
        room_id = r.json()["id"]
        r = client.post(
            "/api/rooms", json={"name": "R", "course_id": course_id}, headers=sv1
        )
        check(r.status_code == 403, "SV không tạo được phòng")
        r = client.get("/api/rooms/students", headers=lec)
        check(len(r.json()) == 2, "Lecturer thấy danh sách SV để mời")
        r = client.post(
            f"/api/rooms/{room_id}/members",
            json={"email": "sv1@smokemail.com"},
            headers=lec,
        )
        check(r.status_code == 201, "Mời SV1 vào phòng")
        r = client.post(
            f"/api/rooms/{room_id}/members",
            json={"email": "sv1@smokemail.com"},
            headers=lec,
        )
        check(r.status_code == 400, "Không mời trùng")
        r = client.post(
            f"/api/rooms/{room_id}/members",
            json={"email": "lec@smokemail.com"},
            headers=lec,
        )
        check(r.status_code == 400, "Chỉ mời được tài khoản Sinh viên")
        r = client.get("/api/rooms", headers=sv1)
        check(len(r.json()) == 1, "SV1 thấy phòng được mời")
        r = client.get("/api/rooms", headers=sv2)
        check(len(r.json()) == 0, "SV2 không thấy phòng")
        r = client.get("/api/rooms", headers=admin)
        check(len(r.json()) == 1, "Admin thấy mọi phòng")

        # ---------- Quiz (FR-QZ) — quiz gắn theo phòng học ----------
        print("\n[Quiz]")
        r = client.post(
            "/api/quizzes",
            json={
                "room_id": room_id,
                "title": "Quiz Smoke",
                "questions": [
                    {"text": "1+1?", "options": ["1", "2"], "correct_index": 1},
                    {"text": "2+2?", "options": ["4", "5"], "correct_index": 0},
                ],
            },
            headers=lec,
        )
        check(r.status_code == 200, "Lecturer tạo quiz cho phòng của mình")
        quiz_id = r.json()["id"]
        r = client.get(f"/api/quizzes/{quiz_id}", headers=sv1)
        check(
            "correct_index" not in str(r.json()["questions"]),
            "Đề trả cho SV ẩn đáp án đúng",
        )
        r = client.get(f"/api/quizzes/{quiz_id}", headers=sv2)
        check(r.status_code == 403, "SV ngoài phòng không mở được quiz")
        r = client.post(
            f"/api/quizzes/{quiz_id}/submit", json={"answers": [1, 1]}, headers=sv1
        )
        check(r.json()["score"] == 50.0, "SV nộp bài -> chấm 50 điểm")
        client.post(
            f"/api/quizzes/{quiz_id}/submit", json={"answers": [1, 0]}, headers=lec
        )
        r = client.get(f"/api/quizzes/{quiz_id}/attempts", headers=lec)
        attempts = r.json()
        check(
            len(attempts) == 1 and attempts[0]["user_email"] == "sv1@smokemail.com",
            "Bảng điểm chỉ ghi SV, kèm tên + email",
        )
        r = client.get(f"/api/quizzes/{quiz_id}/attempts", headers=sv1)
        check(r.status_code == 403, "SV không xem được bảng điểm")
        r = client.delete(f"/api/quizzes/{quiz_id}", headers=sv1)
        check(r.status_code == 403, "SV không xóa được quiz")

        # Chi tiết phòng sau khi có quiz: thành viên + quiz gắn phòng.
        r = client.get(f"/api/rooms/{room_id}", headers=sv1)
        detail = r.json()
        check(
            len(detail["members"]) == 1 and len(detail["quizzes"]) == 1,
            "Chi tiết phòng: thành viên + quiz của phòng",
        )
        r = client.get(f"/api/rooms/{room_id}", headers=sv2)
        check(r.status_code == 403, "SV ngoài phòng bị chặn")
        sv1_id = detail["members"][0]["user_id"]
        r = client.delete(f"/api/rooms/{room_id}/members/{sv1_id}", headers=lec)
        check(r.status_code == 204, "Gỡ SV khỏi phòng")

        # ---------- Dọn dẹp: xóa user / course / room không vỡ FK ----------
        print("\n[Xóa dữ liệu an toàn]")
        r = client.delete(f"/api/users/{sv2_id}", headers=admin)
        check(r.status_code == 204, "Admin xóa SV2 (dọn phiên/attempt/membership)")
        r = client.delete(f"/api/rooms/{room_id}", headers=lec)
        check(r.status_code == 204, "Xóa phòng")
        r = client.delete(f"/api/courses/{course_id}", headers=lec)
        check(r.status_code == 204, "Xóa môn (kèm quiz, tài liệu, room của môn)")

    print(f"\nSmoke test PASS ({PASS} checks).")


if __name__ == "__main__":
    run()
