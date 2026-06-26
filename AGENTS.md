# AGENTS.md

Tài liệu hướng dẫn cho Codex khi làm việc trong repository này.

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
| **Admin** | Quản trị hệ thống | **Chỉ quản lý người dùng** (CRUD người dùng + đổi role) và **duyệt yêu cầu tài khoản**; cấu hình hệ thống qua env. Giao diện Admin **không** có chat/quiz/phòng/tài liệu (backend vẫn giữ quyền giám sát nhưng UI ẩn) |
| **Lecturer** (Giảng viên) | Người phụ trách nội dung môn học | Upload / xem / xóa tài liệu của môn mình phụ trách, tạo & quản lý môn học/chương, tạo quiz + xem bảng điểm SV, tạo **phòng học** & mời sinh viên; **không** quản lý người dùng, **không dùng AI chat** |
| **User** (Sinh viên) | Người dùng cuối | Chat hỏi đáp (chỉ role này cần AI chat), xem tài liệu đã index, tham gia phòng học được mời, làm quiz & xem điểm, xem & quản lý phiên chat **của chính mình**; **không** upload/xóa tài liệu, không quản trị |

**Phân quyền theo endpoint** thực thi qua dependency `require_role(...)` trong `shared/dependencies.py`. Role là **entity riêng** (bảng `roles`); `User` tham chiếu qua `role_id` và enum `Role ∈ {ADMIN, LECTURER, USER}` (mã vai trò) dùng cho `require_role`.

---

## 2. Yêu cầu chức năng

### A. Functional Requirements theo actor

#### User / Sinh viên (FR-USR)
- `FR-USR-01` — Đăng nhập bằng email + mật khẩu (hoặc Google), nhận JWT. Không còn đăng ký công khai — tài khoản do Admin cấp hoặc duyệt từ form **Yêu cầu tài khoản** (FR-REQ)
- `FR-USR-02` — Chat hỏi đáp tự nhiên theo ngữ cảnh hội thoại (RAG). **Chỉ Sinh viên** (Admin giữ quyền giám sát); Giảng viên không dùng AI chat → `403`
- `FR-USR-03` — Xem trích dẫn nguồn tài liệu gốc kèm mỗi câu trả lời
- `FR-USR-04` — Xem danh sách & lịch sử phiên chat của chính mình

#### Lecturer / Giảng viên (FR-LEC)
- `FR-LEC-01` — Upload tài liệu (PDF, DOCX, PPTX) → tự động ingest vào RAG pipeline
- `FR-LEC-02` — Tạo & quản lý môn học / chương
- `FR-LEC-03` — Xem trạng thái index tài liệu (PROCESSING / INDEXED / FAILED)

#### Admin (FR-ADM)
- `FR-ADM-01` — CRUD người dùng, đổi role (ADMIN / LECTURER / USER)
- `FR-ADM-02` — Quản lý mọi tài liệu và môn học (không giới hạn ownership)
- `FR-ADM-03` — Xem toàn bộ phiên chat của mọi người dùng (backend hỗ trợ; UI hiện không hiển thị)
- `FR-ADM-04` — Cấu hình hệ thống qua env (model name, API key, paths)

> **Lưu ý phạm vi Admin:** giao diện Admin **chỉ có mục Quản lý người dùng** (CRUD user + đổi role + duyệt yêu cầu tài khoản). Không có chat/quiz/phòng/tài liệu trong UI.

#### Yêu cầu tài khoản (FR-REQ)
- `FR-REQ-01` — Form **public** ở trang đăng nhập: họ tên + email + vai trò mong muốn (USER/LECTURER, không xin được ADMIN) + lời nhắn → lưu `AccountRequest` (PENDING). Chống spam: rate-limit 5 yêu cầu/giờ/IP; chặn email đã có tài khoản hoặc đã có yêu cầu PENDING
- `FR-REQ-02` — Admin xem danh sách yêu cầu (lọc theo trạng thái) trong tab "Yêu cầu chờ duyệt"
- `FR-REQ-03` — Admin **Duyệt** → tái dùng flow `create_account` (mật khẩu tự sinh + email thông báo qua Brevo/SMTP) → status APPROVED; hoặc **Từ chối** → REJECTED. Yêu cầu đã xử lý không duyệt lại được

#### Quiz (FR-QZ)
- `FR-QZ-01` — Lecturer/Admin tạo quiz trắc nghiệm gắn với **từng môn học** (nhiều câu, mỗi câu ≥2 lựa chọn, 1 đáp án đúng)
- `FR-QZ-02` — Student làm quiz; endpoint trả đề **ẩn đáp án đúng** (chống lộ đáp án)
- `FR-QZ-03` — Nộp bài → backend chấm điểm, trả `score / correct / total` + đáp án đúng từng câu. Chỉ lượt làm của **Sinh viên** được lưu vào bảng điểm (Lecturer/Admin xem thử không ghi)
- `FR-QZ-04` — Lecturer (người tạo quiz) / Admin xóa quiz; xem bảng điểm (attempts) **kèm tên + email sinh viên** — điểm của SV tự động gửi về giảng viên qua bảng này

#### Phòng học / Rooms (FR-ROOM)
- `FR-ROOM-01` — **Chỉ Admin/Lecturer** tạo phòng học, gắn với một môn học (`course_id`)
- `FR-ROOM-02` — Danh sách phòng theo vai trò: Admin thấy mọi phòng; Lecturer thấy phòng mình tạo; Student chỉ thấy phòng được mời
- `FR-ROOM-03` — Chi tiết phòng tổng hợp: thành viên + quiz + tài liệu (slide/doc) của môn — sinh viên trong phòng làm quiz và xem tài liệu học tập tại đây
- `FR-ROOM-04` — Người tạo phòng / Admin mời sinh viên qua email (chỉ tài khoản role USER), gỡ thành viên, xóa phòng

#### Giới hạn chat (FR-RL)
- `FR-RL-01` — Rate-limit chat **mức cố định, chỉ áp dụng cho Sinh viên** (`STUDENT_CHAT_PER_MIN` ≈ 30 câu/phút). Giảng viên & Admin không bị giới hạn (không dùng AI chat trong UI). *(Đã bỏ subscription/gói dịch vụ Free/Pro/Max.)*

### B. Deliverables
- Web app chatbot.
- Source code trên GitHub (có README).
- Test set 50 câu hỏi + ground truth (file đánh giá độ chính xác của chatbot).

---

## 3. Tech Stack

| Layer | Công nghệ | Ghi chú |
|-------|-----------|---------|
| Frontend | **React** (Vite + TypeScript) | UI đẹp, bắt mắt. Tailwind CSS + component library |
| Mobile | **Capacitor** (Android) | Bọc cùng codebase web thành app cài đặt (xem §9.1) |
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
│   │   ├── account_requests/    # MODULE: Yêu cầu tài khoản (public + Admin duyệt)
│   │   │   ├── router.py        # POST /account-requests, /{id}/approve|reject
│   │   │   ├── service.py       # Chặn trùng; duyệt -> create_account + email
│   │   │   ├── repository.py
│   │   │   ├── models.py        # AccountRequest (PENDING|APPROVED|REJECTED)
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
│   │   ├── courses/             # MODULE: Môn học / Chương
│   │   │   ├── router.py        # GET /courses, /courses/{id}/chapters
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── models.py        # Course, Chapter
│   │   │
│   │   ├── quizzes/             # MODULE: Quiz trắc nghiệm
│   │   │   ├── router.py        # POST/GET /quizzes, /{id}/submit, /{id}/attempts
│   │   │   ├── service.py       # Tạo quiz, chấm điểm (ẩn đáp án khi trả đề)
│   │   │   ├── repository.py
│   │   │   ├── models.py        # Quiz, Question, QuizAttempt
│   │   │   └── schemas.py
│   │   │
│   │   └── rooms/               # MODULE: Phòng học (Lecturer/Admin tạo, mời SV)
│   │       ├── router.py        # POST/GET /rooms, /{id}/members, /students
│   │       ├── service.py       # Quyền theo vai trò; tổng hợp quiz + tài liệu của môn
│   │       ├── repository.py
│   │       ├── models.py        # Room, RoomMember
│   │       └── schemas.py
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
4. Embed từng chunk (Google gemini-embedding-001).
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
| POST | `/api/account-requests` | Gửi yêu cầu tài khoản (rate-limit theo IP) | Public |
| GET | `/api/account-requests` | Danh sách yêu cầu (lọc `?status=`) | Admin |
| POST | `/api/account-requests/{id}/approve` | Duyệt → tạo tài khoản + gửi email | Admin |
| POST | `/api/account-requests/{id}/reject` | Từ chối yêu cầu | Admin |
| GET | `/api/users` | Danh sách người dùng | Admin |
| PATCH | `/api/users/{id}/role` | Đổi role người dùng | Admin |
| POST | `/api/documents` | Upload file → ingest | Lecturer, Admin |
| GET | `/api/documents` | Danh sách tài liệu đã index (kèm status) | All |
| DELETE | `/api/documents/{id}` | Xóa tài liệu + vector | Lecturer (của mình), Admin |
| GET | `/api/courses` | Danh sách môn học | All |
| POST | `/api/courses` | Tạo môn học | Lecturer, Admin |
| GET | `/api/courses/{id}/chapters` | Chương của môn | All |
| POST | `/api/chat` | Gửi câu hỏi → answer + citations | Student, Admin |
| GET | `/api/sessions` | Danh sách phiên chat (của mình) | All |
| GET | `/api/sessions/{id}` | Lịch sử messages của phiên | Owner, Admin |
| POST | `/api/sessions` | Tạo phiên mới | Student, Admin |
| GET | `/api/quizzes` | Danh sách quiz | All |
| POST | `/api/quizzes` | Tạo quiz | Lecturer, Admin |
| GET | `/api/quizzes/{id}` | Lấy đề (ẩn đáp án đúng) | All |
| POST | `/api/quizzes/{id}/submit` | Nộp bài → chấm điểm + đáp án (chỉ SV ghi attempt) | All |
| GET | `/api/quizzes/{id}/attempts` | Bảng điểm kèm tên/email SV | Lecturer (người tạo), Admin |
| DELETE | `/api/quizzes/{id}` | Xóa quiz | Lecturer (của mình), Admin |
| POST | `/api/rooms` | Tạo phòng học (gắn môn) | Lecturer, Admin |
| GET | `/api/rooms` | Danh sách phòng theo vai trò | All |
| GET | `/api/rooms/students` | Danh sách SV để mời | Lecturer, Admin |
| GET | `/api/rooms/{id}` | Chi tiết phòng (members + quiz + tài liệu) | Thành viên, người tạo, Admin |
| POST | `/api/rooms/{id}/members` | Mời SV vào phòng (email) | Người tạo, Admin |
| DELETE | `/api/rooms/{id}/members/{user_id}` | Gỡ SV khỏi phòng | Người tạo, Admin |
| DELETE | `/api/rooms/{id}` | Xóa phòng | Người tạo, Admin |

---

## 7. Data Model (SQLite)

- **Role** (id, code[ADMIN|LECTURER|USER] unique, name, description) — entity riêng (bảng `roles`), seed cố định id 1/2/3; enum `Role` trong code chỉ là mã vai trò cho `require_role`
- **User** (id, email, password_hash, full_name, role_id → Role, created_at)
- **Course** (id, name, description, owner_id → User[Lecturer])
- **Chapter** (id, course_id, title, order)
- **Document** (id, course_id, chapter_id?, uploaded_by → User, filename, file_type, status, num_chunks, created_at)
- **ChatSession** (id, user_id → User, title, created_at)
- **Message** (id, session_id, role[user|assistant], content, citations_json, created_at)
- **Quiz** (id, course_id → Course, created_by → User, title, created_at)
- **Question** (id, quiz_id → Quiz, text, options_json, correct_index)
- **QuizAttempt** (id, quiz_id → Quiz, user_id → User, score, answers_json, created_at)
- **Room** (id, name, description, course_id → Course, created_by → User[Lecturer/Admin], created_at)
- **RoomMember** (id, room_id → Room, user_id → User[Student], added_at) — unique (room_id, user_id)
- **AccountRequest** (id, email, full_name, requested_role_id → Role[LECTURER|USER], message, status[PENDING|APPROVED|REJECTED], created_at, decided_at?)

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
- Mật khẩu hash bằng `bcrypt` — không lưu plaintext.

**Frontend (React):**
- TypeScript strict. Function components + hooks.
- Tailwind CSS. State đơn giản (React Query cho server state, không cần Redux).
- Component nhỏ, tái sử dụng. Tránh prop drilling sâu.

**Lệnh thường dùng:**
```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend (web)
cd frontend && npm run dev

# Test set evaluation
cd backend && python tests/evaluate.py

# Android (Capacitor): build dist → sync → mở Android Studio
cd frontend && npm run cap:sync && npm run cap:open
# hoặc build thẳng APK debug (cần JDK + Android SDK):
cd frontend && npm run cap:apk   # -> android/app/build/outputs/apk/debug/app-debug.apk
```

**Env (`.env`):**
```
GOOGLE_API_KEY=AIza...
GOOGLE_CHAT_MODEL=gemini-2.5-flash
GOOGLE_EMBED_MODEL=gemini-embedding-001
CHROMA_DIR=./data/chroma
DATABASE_URL=sqlite:///./data/app.db
# Web dev dùng http://localhost:5173. App Capacitor (webview) thêm các origin localhost:
CORS_ORIGINS=http://localhost:5173,http://localhost,https://localhost,capacitor://localhost
```

---

## 9.1. Đa nền tảng: Web + Android (một codebase)

Cùng một frontend React build ra **2 sản phẩm**: website (Vite) và **app Android cài đặt** (Capacitor bọc `dist/`).

- **API base linh hoạt** — `src/api/client.ts` đọc `VITE_API_BASE` (mặc định `/api` tương đối,
  proxy qua Vite cho web). APK đứng một mình **không có proxy** nên phải build với URL backend tuyệt đối:
  - Emulator → host: `VITE_API_BASE=http://10.0.2.2:8000/api`
  - Điện thoại cùng Wi-Fi: `VITE_API_BASE=http://<IP-LAN-máy>:8000/api` (mở firewall cổng 8000)
- **Cleartext HTTP** — backend demo chạy HTTP nên `capacitor.config.ts` đặt `androidScheme: "http"` +
  `cleartext: true`, và `AndroidManifest.xml` có `android:usesCleartextTraffic="true"`. Production HTTPS thì bỏ.
- **CORS** — webview origin là `http://localhost`, đã thêm vào `CORS_ORIGINS` (xem trên).
- **Live-reload khi dev** (tuỳ chọn) — mở comment `server.url` trong `capacitor.config.ts` trỏ về Vite dev
  server LAN; khi đó `/api` proxy qua Vite, không cần build lại APK mỗi lần sửa.
- Backend phải lắng nghe `0.0.0.0` để emulator/điện thoại truy cập: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

> Thư mục native `frontend/android/` do `npx cap add android` sinh ra. Sau khi sửa code web phải
> `npm run build && npx cap sync android` để copy `dist/` mới vào app.

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

## 11. Quy tắc sinh code (Code Generation Rules)

Khi implement bất kỳ tính năng nào, tuân theo các quy tắc sau:

1. **Tham chiếu FR code** trong comment khi implement một yêu cầu.
   Ví dụ: `# FR-USR-02: RAG chat query handler`

2. **Không trộn lẫn logic của các role** — giữ logic User / Lecturer / Admin trong các service layer riêng biệt. Khi cần check quyền, dùng `require_role(...)` trong `shared/dependencies.py`, không viết if/else role inline trong service.

3. **Upload tài liệu** chỉ chấp nhận `.pdf`, `.docx`, `.pptx` — validate cả MIME type lẫn extension ở server side, trả lỗi rõ ràng nếu sai định dạng.

4. **Lịch sử chat** phải được lưu và có thể phân trang — không trả toàn bộ history trong một response.

5. **Citations là bắt buộc** trong mọi câu trả lời AI — không trả bare answer không có source attribution.

6. **Mọi API route mới** phải có đủ 4 thứ:
   - Auth middleware (kiểm tra JWT hợp lệ)
   - Role guard (`require_role(...)`)
   - Input validation (Pydantic schema)
   - Error handling với HTTP status code phù hợp

7. **Gemini API** chỉ được gọi qua `llm/` wrapper — không import `google.generativeai` trực tiếp trong các module nghiệp vụ. Tương tự, embedding chỉ qua `rag/embedder.py`.

8. **Không log dữ liệu nhạy cảm** — không log password, API key, hay token. Log phải có: timestamp, user_id, action, outcome.

---

## 12. Non-Functional Reminders

- **File upload:** Validate MIME type + file extension ở server side trước khi xử lý.
- **Rate limiting:** Áp dụng cho AI chat endpoints (`/api/chat`) để tránh lạm dụng.
- **Auth:** JWT access token nên có thời hạn ngắn (ví dụ 30 phút), cấu hình qua env.
- **Security:** Passwords hash bằng bcrypt. Không expose stack trace trong response production.
- **Gemini retry:** Có giới hạn retry khi gọi Gemini API — không để vòng lặp retry không giới hạn gây treo app.
- **ChromaDB:** Khi xóa tài liệu, phải xóa cả vector trong ChromaDB lẫn metadata trong SQLite.

---

## 13. Lưu ý cho Codex

- Giữ project **đơn giản**, chỉ làm đủ yêu cầu — không over-engineer.
- Ưu tiên giao diện đẹp, bắt mắt cho frontend (đây là yêu cầu rõ của người dùng).
- Khi thêm tính năng, tôn trọng ranh giới module — không để module này gọi thẳng repository của module khác.
- Tài liệu thiết kế (UML, Use Case, Architecture) nằm ở `docs/DESIGN.md`.
- Người dùng giao tiếp bằng tiếng Việt.
- Khi implement một requirement, luôn hỏi: **actor nào sở hữu tính năng này?** và gate đúng quyền.
