from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.chat.models import ChatSession
from app.modules.courses.repository import CourseRepository
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.service import DocumentService
from app.modules.quizzes.repository import QuizRepository
from app.modules.rooms.models import Room, RoomMember
from app.modules.users.models import Role, User


class CourseService:
    """Orchestration cho môn học, gồm xóa kèm dọn dữ liệu liên quan (cascade)."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRepository(db)

    # FR-ADM-02 / FR-LEC-02: Admin xóa mọi môn; Giảng viên chỉ xóa môn của mình.
    def delete(self, course_id: int, user: User) -> None:
        course = self.repo.get(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
        if user.role != Role.ADMIN and course.owner_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Chỉ Admin hoặc giảng viên phụ trách được xóa môn học",
            )

        # 1) Tài liệu: xóa qua DocumentService để dọn cả vector trong ChromaDB.
        doc_service = DocumentService(self.db)
        for doc in DocumentRepository(self.db).list(course_id=course_id):
            doc_service.delete(doc.id)

        # 2) Quiz của môn (kèm câu hỏi + lượt làm) qua repo đã xử lý cascade.
        quiz_repo = QuizRepository(self.db)
        for quiz in quiz_repo.list(course_id=course_id):
            quiz_repo.delete(quiz)

        # 3) Phòng học gắn môn này: xóa kèm thành viên (room không còn ý nghĩa
        # khi môn bị xóa).
        room_ids = [
            rid
            for (rid,) in self.db.query(Room.id).filter(
                Room.course_id == course_id
            )
        ]
        if room_ids:
            self.db.query(RoomMember).filter(
                RoomMember.room_id.in_(room_ids)
            ).delete(synchronize_session=False)
            self.db.query(Room).filter(Room.id.in_(room_ids)).delete(
                synchronize_session=False
            )

        # 4) Phiên chat từng gắn môn này: gỡ liên kết (giữ lại lịch sử của user).
        self.db.query(ChatSession).filter(
            ChatSession.course_id == course_id
        ).update({ChatSession.course_id: None})
        self.db.commit()

        # 5) Xóa môn (chapters tự cascade qua ORM relationship).
        self.repo.delete(course)
