"""Seed tài liệu chính (textbook) vào RAG pipeline để demo chạy sẵn.

Ingest cuốn *Software Modeling and Design* (Gomaa) vào ChromaDB qua đúng
pipeline upload (parse -> chunk -> embed -> index) nên câu hỏi RAG hoạt động
ngay sau khi seed, không cần upload thủ công.

Chạy:  cd backend && python -m scripts.seed_textbook
Tuỳ chọn đường dẫn PDF khác:  python -m scripts.seed_textbook "đường/dẫn.pdf"

Idempotent: nếu môn học đã có tài liệu thì bỏ qua (không index trùng).
Mặc định dùng embed_provider=local nên chạy offline được, không cần API key.
"""

import sys
from pathlib import Path

# Console Windows mặc định cp1252 không in được tiếng Việt -> ép UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Cho phép chạy trực tiếp: thêm thư mục backend/ vào sys.path.
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal, ensure_schema_current, init_db  # noqa: E402
from app.modules.courses.repository import CourseRepository  # noqa: E402
from app.modules.documents.repository import DocumentRepository  # noqa: E402
from app.modules.documents.service import DocumentService  # noqa: E402
from app.modules.users.models import Role, User  # noqa: E402

COURSE_NAME = "Software Modeling and Design"
COURSE_DESC = (
    "UML, Use Cases, Patterns, and Software Architectures — Hassan Gomaa. "
    "Tài liệu giáo trình chính của hệ thống."
)
DEFAULT_PDF = REPO_ROOT / "gomaa-softwaremodellinganddesign (1).pdf"


def _resolve_pdf() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    return DEFAULT_PDF


def _pick_owner(db) -> int | None:
    """Chọn người sở hữu môn/tài liệu: ưu tiên Lecturer, rồi Admin, không thì None."""
    for role in (Role.LECTURER, Role.ADMIN):
        user = db.query(User).filter(User.role == role).first()
        if user:
            return user.id
    return None


def main() -> None:
    pdf_path = _resolve_pdf()
    if not pdf_path.exists():
        print(f"❌ Không tìm thấy file PDF: {pdf_path}")
        sys.exit(1)

    init_db()
    ensure_schema_current()

    db = SessionLocal()
    try:
        courses = CourseRepository(db)
        course = next(
            (c for c in courses.list() if c.name == COURSE_NAME), None
        )
        owner_id = _pick_owner(db)
        if course is None:
            course = courses.create(COURSE_NAME, COURSE_DESC, owner_id)
            print(f"✓ Tạo môn học #{course.id}: {COURSE_NAME}")
        else:
            print(f"• Môn học đã tồn tại #{course.id}: {COURSE_NAME}")

        existing = DocumentRepository(db).list(course_id=course.id)
        if existing:
            print(
                f"• Môn đã có {len(existing)} tài liệu — bỏ qua để tránh "
                "index trùng. (Xóa tài liệu cũ nếu muốn seed lại.)"
            )
            return

        print(f"… Đang ingest {pdf_path.name} (parse → chunk → embed)…")
        doc = DocumentService(db).ingest(
            content=pdf_path.read_bytes(),
            filename=pdf_path.name,
            content_type="application/pdf",
            course_id=course.id,
            chapter_id=None,
            uploaded_by=owner_id,
        )
        print(
            f"✓ Đã index tài liệu #{doc.id} '{doc.filename}' "
            f"với {doc.num_chunks} chunks. Trạng thái: {doc.status}."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
