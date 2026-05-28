"""Seed dữ liệu mẫu: 3 user (admin/lecturer/student) + 1 môn học demo.

Chạy: python seed.py
"""
import sys

# Windows console mặc định cp1252 -> ép UTF-8 để in được tiếng Việt.
sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal, init_db
from app.modules.auth.security import hash_password
from app.modules.courses.models import Chapter, Course
from app.modules.users.models import Role, User

DEMO_USERS = [
    ("admin@demo.com", "admin123", "Quản trị viên", Role.ADMIN),
    ("lecturer@demo.com", "lecturer123", "Giảng viên Demo", Role.LECTURER),
    ("student@demo.com", "student123", "Sinh viên Demo", Role.USER),
]


def run():
    init_db()
    db = SessionLocal()
    try:
        for email, pwd, name, role in DEMO_USERS:
            if not db.query(User).filter(User.email == email).first():
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
        if not db.query(Course).first():
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

        print("Seed xong. Tài khoản demo:")
        for email, pwd, _, role in DEMO_USERS:
            print(f"  {role.value:9} | {email} | {pwd}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
