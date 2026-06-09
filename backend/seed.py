"""Seed dữ liệu mẫu: 3 user (admin/lecturer/student) + 1 môn học demo.

Chạy: python seed.py
"""
import sys

# Windows console mặc định cp1252 -> ép UTF-8 để in được tiếng Việt.
sys.stdout.reconfigure(encoding="utf-8")

import json

from app.database import SessionLocal, init_db
from app.modules.auth.security import hash_password
from app.modules.courses.models import Chapter, Course
from app.modules.quizzes.models import Question, Quiz
from app.modules.users.models import Plan, Role, User

# Chỉ Sinh viên có gói dịch vụ; Giảng viên & Admin được miễn (plan FREE bị bỏ qua).
DEMO_USERS = [
    ("admin@demo.com", "admin123", "Quản trị viên", Role.ADMIN, Plan.FREE),
    ("lecturer@demo.com", "lecturer123", "Giảng viên Demo", Role.LECTURER, Plan.FREE),
    ("student@demo.com", "student123", "Sinh viên Demo", Role.USER, Plan.FREE),
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
    init_db()
    db = SessionLocal()
    try:
        for email, pwd, name, role, plan in DEMO_USERS:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                db.add(
                    User(
                        email=email,
                        password_hash=hash_password(pwd),
                        full_name=name,
                        role=role,
                        plan=plan,
                    )
                )
            else:
                # Tài khoản demo là fixture: luôn đặt lại gói mặc định cho rõ ràng.
                existing.plan = plan
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

        if course and not db.query(Quiz).first():
            quiz = Quiz(
                course_id=course.id,
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
                f"Đã tạo quiz demo (id={quiz.id}) "
                f"+ {len(DEMO_QUIZ['questions'])} câu hỏi."
            )

        print("Seed xong. Tài khoản demo:")
        for email, pwd, _, role, plan in DEMO_USERS:
            print(f"  {role.value:9} | {plan.value:4} | {email} | {pwd}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
