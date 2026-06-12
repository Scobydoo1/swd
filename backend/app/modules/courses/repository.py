from sqlalchemy.orm import Session

from app.modules.courses.models import Chapter, Course


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Course]:
        return self.db.query(Course).order_by(Course.id).all()

    def get(self, course_id: int) -> Course | None:
        return self.db.query(Course).filter(Course.id == course_id).first()

    def create(self, name: str, description: str, owner_id: int | None) -> Course:
        course = Course(name=name, description=description, owner_id=owner_id)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def list_chapters(self, course_id: int) -> list[Chapter]:
        return (
            self.db.query(Chapter)
            .filter(Chapter.course_id == course_id)
            .order_by(Chapter.order)
            .all()
        )

    def delete(self, course: Course) -> None:
        # Chapters tự xóa theo cascade="all, delete-orphan" trên Course.chapters.
        self.db.delete(course)
        self.db.commit()
