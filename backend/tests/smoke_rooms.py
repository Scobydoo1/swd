"""Smoke test cho tính năng Rooms + chat student-only + flow quiz.

Chạy: python -m tests.smoke_rooms (dùng DB SQLite tạm, không đụng data thật).
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


def run() -> None:
    with TestClient(app) as client:
        admin = login(client, "admin@smokemail.com", "admin123")

        # Admin cấp tài khoản Lecturer + 2 Student (mail tắt -> temp_password).
        users = {}
        for email, name, role in [
            ("lec@smokemail.com", "GV Smoke", "LECTURER"),
            ("sv1@smokemail.com", "SV Một", "USER"),
            ("sv2@smokemail.com", "SV Hai", "USER"),
        ]:
            r = client.post(
                "/api/users",
                json={"email": email, "full_name": name, "role": role},
                headers=admin,
            )
            assert r.status_code == 201, r.text
            users[email] = r.json()["temp_password"]
        lec = login(client, "lec@smokemail.com", users["lec@smokemail.com"])
        sv1 = login(client, "sv1@smokemail.com", users["sv1@smokemail.com"])
        sv2 = login(client, "sv2@smokemail.com", users["sv2@smokemail.com"])

        # Lecturer tạo môn + quiz.
        r = client.post(
            "/api/courses", json={"name": "Môn Smoke", "description": ""}, headers=lec
        )
        course_id = r.json()["id"]
        r = client.post(
            "/api/quizzes",
            json={
                "course_id": course_id,
                "title": "Quiz Smoke",
                "questions": [
                    {"text": "1+1?", "options": ["1", "2"], "correct_index": 1},
                    {"text": "2+2?", "options": ["4", "5"], "correct_index": 0},
                ],
            },
            headers=lec,
        )
        quiz_id = r.json()["id"]

        # FR-ROOM-01: Student không tạo được room; Lecturer tạo được.
        r = client.post(
            "/api/rooms",
            json={"name": "Room SV", "course_id": course_id},
            headers=sv1,
        )
        check(r.status_code == 403, "Student bị chặn tạo room")
        r = client.post(
            "/api/rooms",
            json={"name": "Lớp Smoke", "description": "demo", "course_id": course_id},
            headers=lec,
        )
        check(r.status_code == 201, "Lecturer tạo room")
        room_id = r.json()["id"]

        # FR-ROOM-04: mời SV1 (ok), mời lại (400), mời Lecturer (400).
        r = client.post(
            f"/api/rooms/{room_id}/members",
            json={"email": "sv1@smokemail.com"},
            headers=lec,
        )
        check(r.status_code == 201, "Mời SV1 vào room")
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
        check(r.status_code == 400, "Chỉ mời được Sinh viên")

        # FR-ROOM-02/03: SV1 thấy room + chi tiết (quiz, tài liệu); SV2 bị chặn.
        r = client.get("/api/rooms", headers=sv1)
        check(len(r.json()) == 1, "SV1 thấy room được mời")
        r = client.get("/api/rooms", headers=sv2)
        check(len(r.json()) == 0, "SV2 không thấy room")
        r = client.get(f"/api/rooms/{room_id}", headers=sv1)
        detail = r.json()
        check(
            r.status_code == 200
            and len(detail["quizzes"]) == 1
            and detail["course_name"] == "Môn Smoke",
            "Chi tiết room gồm quiz của môn",
        )
        r = client.get(f"/api/rooms/{room_id}", headers=sv2)
        check(r.status_code == 403, "SV ngoài room bị chặn xem chi tiết")

        # FR-QZ: SV1 nộp bài -> có điểm; Lecturer xem thử -> không ghi attempt;
        # bảng điểm kèm tên SV, chỉ người tạo quiz / Admin xem được.
        r = client.post(
            f"/api/quizzes/{quiz_id}/submit", json={"answers": [1, 0]}, headers=sv1
        )
        check(r.json()["score"] == 100.0, "SV1 nộp bài được 100 điểm")
        client.post(
            f"/api/quizzes/{quiz_id}/submit", json={"answers": [0, 1]}, headers=lec
        )
        r = client.get(f"/api/quizzes/{quiz_id}/attempts", headers=lec)
        attempts = r.json()
        check(
            len(attempts) == 1 and attempts[0]["user_name"] == "SV Một",
            "Bảng điểm chỉ ghi SV, kèm tên",
        )
        r = client.get(f"/api/quizzes/{quiz_id}/attempts", headers=sv1)
        check(r.status_code == 403, "SV không xem được bảng điểm")

        # Chat: SV chat được, Lecturer bị 403.
        r = client.post(
            "/api/chat", json={"question": "use case là gì?"}, headers=sv1
        )
        check(r.status_code == 200, "Student chat được")
        r = client.post(
            "/api/chat", json={"question": "use case là gì?"}, headers=lec
        )
        check(r.status_code == 403, "Lecturer bị chặn chat AI")

        # Xóa member rồi xóa room.
        sv1_id = next(
            m["user_id"]
            for m in client.get(f"/api/rooms/{room_id}", headers=lec).json()[
                "members"
            ]
        )
        r = client.delete(
            f"/api/rooms/{room_id}/members/{sv1_id}", headers=lec
        )
        check(r.status_code == 204, "Gỡ SV khỏi room")
        r = client.delete(f"/api/rooms/{room_id}", headers=lec)
        check(r.status_code == 204, "Xóa room")

    print(f"\nSmoke test PASS ({PASS} checks).")


if __name__ == "__main__":
    run()
