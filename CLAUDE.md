# CLAUDE.md

Tài liệu hướng dẫn cho Claude Code khi làm việc trong repository này.

---

## 1. Tổng quan dự án

**Tên dự án:** Course Document RAG Chatbot
**Mục tiêu:** Web app chatbot hỏi đáp dựa trên tài liệu môn học (RAG - Retrieval Augmented Generation). Người dùng upload tài liệu bài giảng (PDF, DOCX, slide), hệ thống tự động chunk + embed, và trả lời câu hỏi **chỉ trong phạm vi tài liệu**, có trích dẫn nguồn.

**Môn học demo:** *Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures* (textbook trong `gomaa-softwaremodellinganddesign (1).pdf`).

**Kiến trúc:** Modular Monolith — một codebase backend duy nhất, chia thành các module nghiệp vụ rõ ràng, tách biệt qua interface nhưng deploy chung một process.

**Tinh thần:** Đơn giản, chỉ đáp ứng đủ yêu cầu. Giao diện đẹp, bắt mắt.

---

## 1.1. Actors & Phân quyền

Hệ thống có **3 actor** với quyền khác nhau (role-based access, JWT):

| Actor | Vai trò | Quyền |
|-------|---------|-------|
| **Admin** | Quản trị hệ thống | Toàn quyền: quản lý người dùng, quản lý môn học/chương, quản lý **mọi** tài liệu, xem toàn bộ phiên chat, cấu hình hệ thống |
| **Lecturer** (Giảng viên) | Người phụ trách nội dung môn học | Upload / xem / xóa tài liệu của môn mình phụ trách, tạo & quản lý môn học/chương, xem thống kê hỏi đáp; **không** quản lý người dùng |
| **User** (Sinh viên) | Người dùng cuối | Chat hỏi đáp, xem tài liệu đã index, xem & quản lý phiên chat **của chính mình**; **không** upload/xóa tài liệu, không quản trị |

**Phân quyền theo endpoint** thực thi qua dependency `require_role(...)` trong `shared/dependencies.py`. Mỗi `User` model có trường `role ∈ {ADMIN, LECTURER, USER}`.

---

## 2. Yêu cầu chức năng (từ readme)

### A. Tính năng hệ thống

**1. Quản lý tài liệu**
- Upload PDF, DOCX, slide bài giảng.
- Tự động chunk & embed tài liệu.
- Quản lý theo môn học / chương (chỉ cần demo 1 môn).
- Xem danh sách tài liệu đã index.

**2. Chat & Hỏi đáp**
- Chat tự nhiên theo ngữ cảnh hội thoại.
- Trích dẫn nguồn tài liệu gốc.
- Giới hạn trả lời trong phạm vi tài liệu (không bịa — nếu không có trong tài liệu thì nói rõ).
- Lịch sử hội thoại theo phiên (session).

### B. Deliverables
- Web app chatbot.
- Source code trên GitHub (có README).
- Test set 50 câu hỏi + ground truth (file đánh giá độ chính xác của chatbot).

---

## 3. Tech Stack

| Layer | Công nghệ | Ghi chú |
|-------|-----------|---------|
| Frontend | **React** (Vite + TypeScript) | UI đẹp, bắt mắt. Tailwind CSS + component library |
| Backend | **Python 3.11+ / FastAPI** | Modular Monolith |
| LLM | **Google Gemini** (gemini-2.5-flash) | Chat completion |
| Embedding | **Google gemini-embedding-001** | Tạo vector |
| Vector Store | **ChromaDB** (embedded/local) | Lưu & search vector |
| Metadata DB | **SQLite** (qua SQLAlchemy) | Tài liệu, phiên chat, lịch sử |
| RAG framework | **LangChain** (loaders, splitters, chains) | Chunk, retrieve, orchestrate |
| Doc parsing | `pypdf`, `python-docx`, `python-pptx` | Đọc PDF/DOCX/slide |
| Auth | JWT cơ bản (role-based) | 3 actor: Admin / Lecturer / User |

---

## 4. Kiến trúc Modular Monolith

Backend gồm các **module** độc lập, mỗi module có ranh giới rõ ràng (router → service → repository). Các module giao tiếp qua **service interface**, không gọi thẳng vào internals của nhau.

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, mount routers, CORS
│   ├── config.py                # Settings (API keys, paths) qua env
│   ├── database.py              # SQLAlchemy engine/session (SQLite)
│   │
│   ├── shared/                  # Cross-cutting: schemas chung, exceptions, deps
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   │
│   ├── modules/
│   │   ├── auth/                # MODULE: Đăng nhập, JWT, đăng ký
│   │   │   ├── router.py        # POST /auth/login, /auth/register
│   │   │   ├── service.py       # Verify password, issue JWT
│   │   │   ├── security.py      # Hash password, encode/decode JWT
│   │   │   └── schemas.py
│   │   │
│   │   ├── users/               # MODULE: Quản lý người dùng (Admin)
│   │   │   ├── router.py        # GET /users, PATCH /users/{id}/role
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py        # User (role: ADMIN|LECTURER|USER)
│   │   │   └── schemas.py
│   │   │
│   │   ├── documents/           # MODULE: Quản lý tài liệu
│   │   │   ├── router.py        # POST /documents, GET /documents
│   │   │   ├── service.py       # Upload, parse, chunk, embed orchestration
│   │   │   ├── repository.py    # CRUD metadata tài liệu (SQLite)
│   │   │   ├── models.py        # SQLAlchemy: Document, Chunk
│   │   │   ├── schemas.py       # Pydantic DTO
│   │   │   ├── parsers.py       # PDF/DOCX/PPTX → text
│   │   │   └── chunker.py       # Text → chunks
│   │   │
│   │   ├── chat/                # MODULE: Chat & Hỏi đáp
│   │   │   ├── router.py        # POST /chat, GET /sessions, GET /sessions/{id}
│   │   │   ├── service.py       # RAG pipeline: retrieve → prompt → LLM → cite
│   │   │   ├── repository.py    # CRUD session + message
│   │   │   ├── models.py        # ChatSession, Message
│   │   │   └── schemas.py
│   │   │
│   │   ├── rag/                 # MODULE: RAG core (dùng chung)
│   │   │   ├── embedder.py      # Google embedding wrapper
│   │   │   ├── vector_store.py  # ChromaDB wrapper (add/query)
│   │   │   └── retriever.py     # Similarity search + filter theo môn/chương
│   │   │
│   │   └── courses/             # MODULE: Môn học / Chương
│   │       ├── router.py        # GET /courses, /courses/{id}/chapters
│   │       ├── service.py
│   │       ├── repository.py
│   │       └── models.py        # Course, Chapter
│   │
│   └── llm/                     # Google Gemini client wrapper (chat + embedding)
│
├── data/
│   ├── app.db                   # SQLite
│   └── chroma/                  # ChromaDB persistent dir
├── tests/
│   └── test_set.json            # 50 câu hỏi + ground truth
├── requirements.txt
└── .env.example
```

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/                     # Axios client gọi backend
│   ├── components/
│   │   ├── chat/                # ChatWindow, MessageBubble, CitationCard, SourceList
│   │   ├── documents/           # UploadZone, DocumentList, DocumentCard
│   │   └── layout/              # Sidebar, Header
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   └── DocumentsPage.tsx
│   ├── hooks/                   # useChat, useDocuments, useSessions
│   └── types/
├── index.html
├── package.json
└── vite.config.ts
```

**Nguyên tắc module:**
- Router chỉ điều phối HTTP ↔ Service. Không chứa logic nghiệp vụ.
- Service chứa logic, gọi Repository và RAG module.
- Repository là lớp duy nhất chạm DB.
- Module `rag` và `llm` là shared service — module khác inject vào dùng, không tự dựng Gemini client riêng.

---

## 5. RAG Pipeline

**Ingest (upload tài liệu):**
1. Nhận file → lưu metadata `Document` (SQLite, status=PROCESSING).
2. Parse file → text (parsers.py).
3. Chunk text (RecursiveCharacterTextSplitter, ~800 token, overlap ~100).
4. Embed từng chunk (Google text-embedding-004).
5. Lưu vector vào ChromaDB kèm metadata: `{document_id, course_id, chapter, chunk_index, source_text, page}`.
6. Update `Document.status = INDEXED`.

**Query (hỏi đáp):**
1. Nhận câu hỏi + session_id.
2. (Tùy chọn) condense câu hỏi với lịch sử hội thoại → standalone question.
3. Embed câu hỏi → similarity search ChromaDB (top-k=4, filter theo course_id).
4. Build prompt: system prompt (chỉ trả lời từ context, nếu không có thì nói "không tìm thấy trong tài liệu") + retrieved chunks + lịch sử + câu hỏi.
5. Gọi LLM → câu trả lời.
6. Trả về answer + danh sách citations (source_text, document name, page).
7. Lưu message vào session.

**System prompt nguyên tắc:** Bắt buộc trả lời **chỉ dựa trên context cung cấp**. Không bịa. Luôn dẫn nguồn.

---

## 6. API Endpoints (dự kiến)

| Method | Path | Mô tả | Quyền |
|--------|------|-------|-------|
| POST | `/api/auth/register` | Đăng ký tài khoản | Public |
| POST | `/api/auth/login` | Đăng nhập → JWT | Public |
| GET | `/api/users` | Danh sách người dùng | Admin |
| PATCH | `/api/users/{id}/role` | Đổi role người dùng | Admin |
| POST | `/api/documents` | Upload file → ingest | Lecturer, Admin |
| GET | `/api/documents` | Danh sách tài liệu đã index (kèm status) | All |
| DELETE | `/api/documents/{id}` | Xóa tài liệu + vector | Lecturer (của mình), Admin |
| GET | `/api/courses` | Danh sách môn học | All |
| POST | `/api/courses` | Tạo môn học | Lecturer, Admin |
| GET | `/api/courses/{id}/chapters` | Chương của môn | All |
| POST | `/api/chat` | Gửi câu hỏi → answer + citations | All |
| GET | `/api/sessions` | Danh sách phiên chat (của mình) | All |
| GET | `/api/sessions/{id}` | Lịch sử messages của phiên | Owner, Admin |
| POST | `/api/sessions` | Tạo phiên mới | All |

---

## 7. Data Model (SQLite)

- **User** (id, email, password_hash, full_name, role[ADMIN|LECTURER|USER], created_at)
- **Course** (id, name, description, owner_id → User[Lecturer])
- **Chapter** (id, course_id, title, order)
- **Document** (id, course_id, chapter_id?, uploaded_by → User, filename, file_type, status, num_chunks, created_at)
- **ChatSession** (id, user_id → User, title, created_at)
- **Message** (id, session_id, role[user|assistant], content, citations_json, created_at)

Vector + chunk text lưu trong ChromaDB (không lặp lại trong SQLite để gọn).

---

## 8. Test Set & Đánh giá

- `backend/tests/test_set.json`: 50 câu hỏi về nội dung textbook + `ground_truth` (đáp án đúng do người chuẩn bị).
- Script đánh giá: chạy 50 câu qua chatbot, so sánh với ground truth.
- Metrics gợi ý: **Faithfulness** (trả lời có bám context không), **Answer relevance**, **Retrieval hit rate** (chunk đúng có được retrieve không). Có thể dùng RAGAS hoặc LLM-as-judge.

---

## 9. Quy ước phát triển

**Backend (Python):**
- Format: `black` + `isort`. Lint: `ruff`.
- Pydantic v2 cho schema. Type hints bắt buộc.
- Async cho IO (FastAPI endpoints, Gemini API calls).
- Không hardcode secret — đọc từ `.env` qua `config.py`.

**Frontend (React):**
- TypeScript strict. Function components + hooks.
- Tailwind CSS. State đơn giản (React Query cho server state, không cần Redux).
- Component nhỏ, tái sử dụng. Tránh prop drilling sâu.

**Lệnh thường dùng:**
```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Test set evaluation
cd backend && python tests/evaluate.py
```

**Env (`.env`):**
```
GOOGLE_API_KEY=AIza...
GOOGLE_CHAT_MODEL=gemini-2.5-flash
GOOGLE_EMBED_MODEL=gemini-embedding-001
CHROMA_DIR=./data/chroma
DATABASE_URL=sqlite:///./data/app.db
```

---

## 10. Design Patterns áp dụng

| Pattern | Áp dụng ở đâu |
|---------|---------------|
| **Layered / Repository** | Mỗi module: router → service → repository |
| **Strategy** | `parsers.py`: chọn parser theo file type (PDF/DOCX/PPTX) |
| **Facade** | `rag` module che giấu embedder + vector_store + retriever |
| **Dependency Injection** | FastAPI `Depends` inject service/repo/session |
| **DTO** | Pydantic schemas tách biệt model DB và API contract |
| **Pipeline** | RAG ingest & query là chuỗi bước rõ ràng |

Chi tiết sơ đồ xem `docs/DESIGN.md`.

---

## 11. Lưu ý cho Claude Code

- Giữ project **đơn giản**, chỉ làm đủ yêu cầu — không over-engineer.
- Ưu tiên giao diện đẹp, bắt mắt cho frontend (đây là yêu cầu rõ của người dùng).
- Khi thêm tính năng, tôn trọng ranh giới module — không để module này gọi thẳng repository của module khác.
- Tài liệu thiết kế (UML, Use Case, Architecture) nằm ở `docs/DESIGN.md`.
- Người dùng giao tiếp bằng tiếng Việt.
