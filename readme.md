# EduRAG — Course Document RAG Chatbot

Web app chatbot hỏi đáp dựa trên tài liệu môn học (RAG). Người dùng upload tài liệu bài giảng (PDF/DOCX/Slide), hệ thống tự động chunk + embed, và trả lời câu hỏi **chỉ trong phạm vi tài liệu**, có trích dẫn nguồn.

Môn học demo: *Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures*.

> Yêu cầu gốc của dự án: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)

## Tính năng

- **Quản lý tài liệu:** upload PDF/DOCX/PPTX, tự động chunk & embed, quản lý theo môn học, xem danh sách đã index.
- **Chat & Hỏi đáp:** chat theo ngữ cảnh, trích dẫn nguồn, giới hạn trả lời trong tài liệu, lịch sử theo phiên.
- **Phân quyền 3 actor:** Admin (toàn quyền + quản lý người dùng), Lecturer (quản lý tài liệu/môn học), User (chat + xem).

## Kiến trúc

**Modular Monolith** — chi tiết trong [CLAUDE.md](CLAUDE.md), sơ đồ UML/Use Case/Architecture trong [docs/DESIGN.md](docs/DESIGN.md).

| Layer | Công nghệ |
|-------|-----------|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Backend | Python + FastAPI |
| LLM / Embedding | OpenAI (gpt-4o-mini / text-embedding-3-small) |
| Vector store | ChromaDB |
| Metadata DB | SQLite |

## Cài đặt & chạy

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # rồi điền OPENAI_API_KEY
python seed.py              # tạo 3 user demo + môn học demo
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:5173

### Tài khoản demo

| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| Admin | admin@demo.com | admin123 |
| Lecturer | lecturer@demo.com | lecturer123 |
| User | student@demo.com | student123 |

## Quy trình sử dụng

1. Đăng nhập bằng tài khoản **Lecturer** hoặc **Admin**.
2. Vào **Tài liệu** → upload file PDF/DOCX/PPTX (ví dụ textbook môn học). Đợi trạng thái chuyển sang *Đã index*.
3. Vào **Hỏi đáp** → chọn môn học → đặt câu hỏi. Câu trả lời kèm trích dẫn nguồn.
4. Tài khoản **Admin** có thêm trang **Người dùng** để phân quyền.

## Đánh giá (Test set 50 câu)

Sau khi đã index tài liệu textbook vào môn học (id=1):

```bash
cd backend
python -m tests.evaluate --course-id 1
```

- Test set: [backend/tests/test_set.json](backend/tests/test_set.json) — 50 câu hỏi + ground truth.
- Script chạy 50 câu qua chatbot, dùng LLM-as-judge so với ground truth, in accuracy và lưu `tests/eval_result.json`.

## Cấu trúc thư mục

```
project/
├── readme.md            # File này
├── CLAUDE.md            # Tài liệu thiết kế & hướng dẫn chi tiết
├── docs/
│   ├── DESIGN.md        # Sơ đồ UML, Use Case, Architecture, Patterns
│   └── REQUIREMENTS.md  # Yêu cầu gốc
├── backend/             # FastAPI (Modular Monolith)
│   ├── app/modules/     # auth, users, courses, documents, chat, rag
│   ├── seed.py
│   └── tests/           # test_set.json + evaluate.py
└── frontend/            # React + Vite + Tailwind
    └── src/pages/       # ChatPage, DocumentsPage, AdminPage, LoginPage
```
