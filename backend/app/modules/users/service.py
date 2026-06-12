import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.auth.security import hash_password
from app.modules.chat.models import ChatSession, Message
from app.modules.courses.models import Course
from app.modules.documents.models import Document
from app.modules.quizzes.models import Quiz, QuizAttempt
from app.modules.users.models import Role, User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserCreateResult, UserOut
from app.shared import mailer


class UserService:
    """Orchestration cho người dùng — chủ yếu là xóa kèm dọn dữ liệu liên quan."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    # FR-ADM-01: Chỉ Admin tạo tài khoản Sinh viên/Giảng viên. Mật khẩu tự sinh
    # và gửi qua email; nếu gửi thất bại thì trả về cho Admin gửi tay.
    def create_account(self, req: UserCreate) -> UserCreateResult:
        if self.repo.get_by_email(req.email):
            raise HTTPException(status_code=400, detail="Email đã được đăng ký")
        password = secrets.token_urlsafe(9)  # ~12 ký tự URL-safe
        user = self.repo.create(
            email=req.email,
            password_hash=hash_password(password),
            full_name=req.full_name,
            role=req.role,
        )
        sent = mailer.send_account_email(user.email, user.full_name, password)
        return UserCreateResult(
            user=UserOut.model_validate(user),
            email_sent=sent,
            temp_password=None if sent else password,
        )

    # FR-ADM-01: Admin xóa người dùng. Dữ liệu cá nhân (phiên chat, lượt làm quiz)
    # bị xóa; nội dung dùng chung (môn học, tài liệu, quiz đã tạo) được giữ lại và
    # gỡ liên kết người sở hữu để không xóa lan và không vi phạm khóa ngoại.
    def delete(self, user_id: int, current_user: User) -> None:
        user = self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        if user.id == current_user.id:
            raise HTTPException(
                status_code=400, detail="Không thể tự xóa tài khoản của chính mình"
            )

        # 1) Phiên chat của user. Xóa bulk theo thứ tự con -> cha (messages
        # trước, sessions sau) và thực thi NGAY: User và ChatSession không có
        # relationship ORM nên không được dựa vào thứ tự flush của SQLAlchemy
        # — trên Postgres từng vỡ FK chat_sessions_user_id_fkey vì DELETE users
        # chạy trước DELETE chat_sessions.
        session_ids = [
            sid
            for (sid,) in self.db.query(ChatSession.id).filter(
                ChatSession.user_id == user_id
            )
        ]
        if session_ids:
            self.db.query(Message).filter(
                Message.session_id.in_(session_ids)
            ).delete(synchronize_session=False)
            self.db.query(ChatSession).filter(
                ChatSession.id.in_(session_ids)
            ).delete(synchronize_session=False)

        # 2) Lượt làm quiz của user.
        self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id
        ).delete()

        # 3) Gỡ liên kết người sở hữu trên nội dung dùng chung (giữ lại nội dung).
        self.db.query(Course).filter(Course.owner_id == user_id).update(
            {Course.owner_id: None}
        )
        self.db.query(Document).filter(Document.uploaded_by == user_id).update(
            {Document.uploaded_by: None}
        )
        self.db.query(Quiz).filter(Quiz.created_by == user_id).update(
            {Quiz.created_by: None}
        )

        # 4) Xóa người dùng.
        self.db.delete(user)
        self.db.commit()


def ensure_default_admin(db: Session) -> None:
    """Seed Admin đầu tiên từ env khi startup.

    Không còn đăng ký công khai nên hệ thống cần ít nhất một Admin để cấp
    tài khoản. Bỏ qua nếu đã có admin hoặc env chưa cấu hình.
    """
    if not settings.admin_email or not settings.admin_password:
        return
    if db.query(User).filter(User.role == Role.ADMIN).first():
        return
    repo = UserRepository(db)
    if repo.get_by_email(settings.admin_email):
        return
    repo.create(
        email=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        full_name=settings.admin_full_name,
        role=Role.ADMIN,
    )
