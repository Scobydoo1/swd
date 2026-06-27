"""Seed dữ liệu mẫu: 3 user (admin/lecturer/student) + 1 môn học demo.

Chạy: python seed.py

CHỈ DÙNG CHO LOCAL. Mật khẩu demo là kiến thức công khai (nằm trong source),
nên script từ chối chạy khi DATABASE_URL không phải SQLite (dấu hiệu production
Postgres/SQL Server) — ép bằng cờ --demo-users nếu thật sự muốn.
"""
import sys

# Windows console mặc định cp1252 -> ép UTF-8 để in được tiếng Việt.
sys.stdout.reconfigure(encoding="utf-8")

import json

from app.database import IS_SQLITE, SessionLocal, init_db
from app.modules.auth.security import hash_password
from app.modules.courses.models import Chapter, Course
from app.modules.quizzes.models import Question, Quiz
from app.modules.rooms.models import Room, RoomMember
from app.modules.users.models import Role, User

DEMO_USERS = [
    ("admin@demo.com", "admin123", "Quản trị viên", Role.ADMIN),
    ("lecturer@demo.com", "lecturer123", "Giảng viên Demo", Role.LECTURER),
    ("student@demo.com", "student123", "Sinh viên Demo", Role.USER),
]

DEMO_QUIZ = {
    "title": "Nhập môn UML & Use Case",
    "questions": [
        {
            "text": "Use case mô tả điều gì?",
            "options": [
                "Cấu trúc lớp của hệ thống",
                "Một chuỗi tương tác giữa actor và hệ thống để đạt mục tiêu",
                "Sơ đồ triển khai phần cứng",
                "Mã nguồn của hệ thống",
            ],
            "correct_index": 1,
        },
        {
            "text": "Actor trong mô hình use case là gì?",
            "options": [
                "Một lớp bên trong hệ thống",
                "Một bảng cơ sở dữ liệu",
                "Người hoặc hệ thống ngoài tương tác với hệ thống",
                "Một phương thức",
            ],
            "correct_index": 2,
        },
        {
            "text": "Quan hệ «include» giữa các use case nghĩa là gì?",
            "options": [
                "Một use case luôn dùng lại hành vi của use case khác",
                "Hai use case không liên quan",
                "Một actor kế thừa actor khác",
                "Một lớp hiện thực một interface",
            ],
            "correct_index": 0,
        },
    ],
}


def run():
    # Chốt an toàn: không seed tài khoản demo (mật khẩu công khai) lên production.
    if not IS_SQLITE and "--demo-users" not in sys.argv:
        print(
            "DATABASE_URL không phải SQLite — có vẻ đây là CSDL production.\n"
            "Từ chối seed tài khoản demo (mật khẩu nằm công khai trong source).\n"
            "Nếu chắc chắn muốn seed, chạy: python seed.py --demo-users"
        )
        return
    init_db()
    db = SessionLocal()
    try:
        for email, pwd, name, role in DEMO_USERS:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                db.add(
                    User(
                        email=email,
                        password_hash=hash_password(pwd),
                        full_name=name,
                        role=role,
                    )
                )
        db.commit()

        lecturer = db.query(User).filter(User.email == "lecturer@demo.com").first()
        course = db.query(Course).first()
        if not course:
            course = Course(
                name="Software Modeling and Design",
                description="UML, Use Cases, Patterns, and Software Architectures",
                owner_id=lecturer.id if lecturer else None,
            )
            db.add(course)
            db.flush()
            chapters = [
                "Introduction to UML",
                "Use Case Modeling",
                "Design Patterns",
                "Software Architectures",
            ]
            for i, title in enumerate(chapters):
                db.add(Chapter(course_id=course.id, title=title, order=i))
            db.commit()
            print(f"Đã tạo môn học demo (id={course.id}) + {len(chapters)} chương.")

        # Phòng học demo: Lecturer tạo, mời sẵn Student vào (tạo TRƯỚC quiz vì
        # quiz nay gắn theo phòng).
        student = db.query(User).filter(User.email == "student@demo.com").first()
        room = db.query(Room).first()
        if course and not room:
            room = Room(
                name="Lớp SE101 — Software Modeling",
                description="Phòng học demo: quiz + tài liệu môn Software Modeling and Design",
                course_id=course.id,
                created_by=lecturer.id if lecturer else None,
            )
            db.add(room)
            db.flush()
            if student:
                db.add(RoomMember(room_id=room.id, user_id=student.id))
            db.commit()
            print(f"Đã tạo phòng học demo (id={room.id}) + mời sinh viên demo.")

        if course and room and not db.query(Quiz).first():
            quiz = Quiz(
                course_id=course.id,
                room_id=room.id,
                title=DEMO_QUIZ["title"],
                created_by=lecturer.id if lecturer else None,
            )
            for i, q in enumerate(DEMO_QUIZ["questions"]):
                quiz.questions.append(
                    Question(
                        text=q["text"],
                        options_json=json.dumps(q["options"], ensure_ascii=False),
                        correct_index=q["correct_index"],
                        order=i,
                    )
                )
            db.add(quiz)
            db.commit()
            print(
                f"Đã tạo quiz demo (id={quiz.id}) gắn phòng {room.id} "
                f"+ {len(DEMO_QUIZ['questions'])} câu hỏi."
            )

        print("Seed xong. Tài khoản demo:")
        for email, pwd, _, role in DEMO_USERS:
            print(f"  {role.value:9} | {email} | {pwd}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
