# diagram.md — Thông tin đầy đủ để vẽ toàn bộ diagram

> File này **không chứa hình vẽ**. Nó là "nguồn sự thật" mô tả đầy đủ actor, use case,
> lớp, bảng, luồng tuần tự, component, trạng thái và triển khai — đủ để vẽ lại mọi
> diagram bằng bất kỳ công cụ nào (Mermaid, draw.io, PlantUML, Visio, Figma…).
> Bản Mermaid render sẵn của một số diagram nằm trong [README.md](../README.md).

Hệ thống: **Maple — Course Document RAG Chatbot** (Modular Monolith, FastAPI + React).

---

## 1. Use Case Diagram

### 1.1. Actors

| Actor | Mô tả |
|-------|-------|
| **Admin** | Quản trị hệ thống — toàn quyền |
| **Lecturer** (Giảng viên) | Phụ trách nội dung môn học; **không dùng AI chat** |
| **User / Student** (Sinh viên) | Người dùng cuối — actor duy nhất cần AI chat |
| **Guest** (khách chưa đăng nhập) | Chỉ dùng được form Yêu cầu tài khoản + đăng nhập |

### 1.2. Danh sách Use Case

| Mã | Use Case | Ghi chú |
|----|----------|---------|
| UC1 | Đăng nhập (email/mật khẩu hoặc Google) | Không còn đăng ký công khai |
| UC2 | Gửi yêu cầu tài khoản | Guest; form public, rate-limit theo IP |
| UC3 | Duyệt / từ chối yêu cầu tài khoản | Duyệt → tạo tài khoản + email mật khẩu |
| UC4 | Quản lý người dùng (tạo, đổi role, đổi plan, xóa) | |
| UC5 | Quản lý môn học / chương (tạo, xóa) | |
| UC6 | Upload tài liệu PDF/DOCX/PPTX → ingest RAG | |
| UC7 | Xem danh sách tài liệu + trạng thái index | |
| UC8 | Xóa tài liệu (kèm vector ChromaDB) | |
| UC9 | Chat hỏi đáp RAG theo ngữ cảnh | **Chỉ Sinh viên** (Admin giám sát) |
| UC10 | Xem trích dẫn nguồn của câu trả lời | đi kèm UC9 («include») |
| UC11 | Quản lý phiên chat (tạo/ghim/đổi tên/xóa) của mình | |
| UC12 | Xem toàn bộ phiên chat mọi người dùng | Admin |
| UC13 | Tạo & quản lý Quiz theo môn học | |
| UC14 | Làm Quiz → nhận điểm + đáp án ngay | Chỉ lượt làm của SV được lưu |
| UC15 | Xem bảng điểm quiz (tên + email + điểm SV) | Người tạo quiz hoặc Admin |
| UC16 | Tạo phòng học (gắn môn) | Chỉ Admin/Lecturer |
| UC17 | Mời / gỡ sinh viên trong phòng (qua email) | Người tạo phòng hoặc Admin |
| UC18 | Tham gia phòng học — làm quiz + xem tài liệu | Sinh viên được mời |
| UC19 | Xem / nâng cấp gói dịch vụ Free–Pro–Max | Chỉ Sinh viên |
| UC20 | Cấu hình hệ thống qua env | Admin (ngoài UI) |

### 1.3. Ma trận Actor × Use Case (để nối mũi tên)

| UC | Guest | Student | Lecturer | Admin |
|----|:-----:|:-------:|:--------:|:-----:|
| UC1 | ✔ (thực hiện) | ✔ | ✔ | ✔ |
| UC2 | ✔ | — | — | — |
| UC3, UC4, UC12, UC20 | — | — | — | ✔ |
| UC5, UC6, UC8, UC13, UC15, UC16, UC17 | — | — | ✔ | ✔ |
| UC7 | — | ✔ | ✔ | ✔ |
| UC9, UC10, UC11 | — | ✔ | — | ✔ (giám sát) |
| UC14, UC18, UC19 | — | ✔ | — | — |

Quan hệ giữa các use case: UC9 «include» UC10 (mỗi câu trả lời bắt buộc kèm trích dẫn);
UC3 «include» UC4-tạo-tài-khoản (duyệt gọi lại flow tạo tài khoản); UC18 «extend» UC14
(làm quiz từ trong phòng); UC16 «include» UC5 (phòng phải gắn một môn có sẵn).

---

## 2. Class Diagram (Domain Model)

### 2.1. Enum

- `Plan` = FREE | PRO | MAX
- `FileType` = PDF | DOCX | PPTX
- `DocStatus` = PROCESSING | INDEXED | FAILED
- `MsgRole` = user | assistant
- `RequestStatus` = PENDING | APPROVED | REJECTED

> `Role` **không** còn là enum trong DB mà là **entity riêng** (bảng `roles`,
> code ∈ ADMIN | LECTURER | USER). User & AccountRequest tham chiếu qua khóa ngoại.
> Trong code vẫn có enum `Role` (mã vai trò) dùng cho `require_role(...)`, ánh xạ
> id cố định ADMIN=1, LECTURER=2, USER=3.

### 2.2. Lớp và thuộc tính

| Lớp | Thuộc tính |
|-----|-----------|
| **Role** | id: int, code: str (unique — ADMIN/LECTURER/USER), name: str, description: str |
| **User** | id: int, email: str (unique), password_hash: str, full_name: str, role_id: int → Role, plan: Plan, created_at: datetime |
| **AccountRequest** | id: int, email: str, full_name: str, requested_role_id: int → Role (≠ADMIN), message: str, status: RequestStatus, created_at: datetime, decided_at: datetime? |
| **Course** | id: int, name: str, description: str, owner_id: int? → User |
| **Chapter** | id: int, course_id: int → Course, title: str, order: int |
| **Document** | id: int, course_id → Course, chapter_id? → Chapter, uploaded_by? → User, filename: str, file_type: FileType, status: DocStatus, num_chunks: int, error: str?, created_at |
| **ChatSession** | id: int, user_id → User, title: str, course_id?: int, pinned: bool, created_at |
| **Message** | id: int, session_id → ChatSession, role: MsgRole, content: str, citations_json: json, created_at |
| **Quiz** | id: int, course_id → Course, created_by? → User, title: str, created_at |
| **Question** | id: int, quiz_id → Quiz, text: str, options_json: json (list[str]), correct_index: int, order: int |
| **QuizAttempt** | id: int, quiz_id → Quiz, user_id? → User, score: float (0–100), answers_json: json (list[int]), created_at |
| **Room** | id: int, name: str, description: str, course_id → Course, created_by? → User, created_at |
| **RoomMember** | id: int, room_id → Room, user_id → User, added_at — unique(room_id, user_id) |

### 2.3. Quan hệ (multiplicity)

- Role 1 — 0..* User (mỗi user đúng 1 role); Role 1 — 0..* AccountRequest (vai trò mong muốn)
- User 1 — 0..* Course (owns, vai Lecturer)
- User 1 — 0..* Document (uploads)
- User 1 — 0..* ChatSession; ChatSession 1 — 0..* Message (composition)
- User 1 — 0..* Quiz (creates); Quiz 1 — 1..* Question (composition); Quiz 1 — 0..* QuizAttempt; User 1 — 0..* QuizAttempt
- User 1 — 0..* Room (creates, vai Lecturer/Admin); Room 1 — 0..* RoomMember (composition); User 1 — 0..* RoomMember (vai Student)
- Course 1 — 0..* Chapter (composition); Course 1 — 0..* Document; Course 1 — 0..* Quiz; Course 1 — 0..* Room
- AccountRequest đứng độc lập (liên kết logic với User qua email sau khi duyệt)

### 2.4. Lớp service (nếu vẽ class diagram tầng ứng dụng)

Mỗi module: `Router → Service → Repository → DB`. Các service chính: AuthService,
AccountRequestService, UserService, CourseService, DocumentService (dùng Parser
strategy + Chunker + RagFacade), ChatService (dùng RagFacade + GeminiClient +
RateLimiter), QuizService, RoomService (gọi QuizService + DocumentService +
CourseRepository + UserRepository), SubscriptionService.

---

## 3. ERD (lược đồ vật lý)

Bảng (PK in đậm, FK →):

0. **roles**: **id**, code UNIQUE INDEX (ADMIN/LECTURER/USER), name, description — seed cố định id 1/2/3
1. **users**: **id**, email UNIQUE INDEX, password_hash, full_name, role_id → roles.id, plan ENUM, created_at
2. **account_requests**: **id**, email INDEX, full_name, requested_role_id → roles.id, message, status ENUM, created_at, decided_at NULL
3. **courses**: **id**, name, description, owner_id → users.id NULL
4. **chapters**: **id**, course_id → courses.id, title, `order`
5. **documents**: **id**, course_id → courses.id, chapter_id → chapters.id NULL, uploaded_by → users.id NULL, filename, file_type ENUM, status ENUM, num_chunks, error NULL, created_at
6. **chat_sessions**: **id**, user_id → users.id, title, course_id NULL, pinned BOOL, created_at
7. **messages**: **id**, session_id → chat_sessions.id, role ENUM, content TEXT, citations_json TEXT, created_at
8. **quizzes**: **id**, course_id → courses.id, created_by → users.id NULL, title, created_at
9. **quiz_questions**: **id**, quiz_id → quizzes.id, text, options_json TEXT, correct_index, `order`
10. **quiz_attempts**: **id**, quiz_id → quizzes.id, user_id → users.id NULL, score FLOAT, answers_json TEXT, created_at
11. **rooms**: **id**, name, description, course_id → courses.id, created_by → users.id NULL, created_at
12. **room_members**: **id**, room_id → rooms.id, user_id → users.id, added_at, UNIQUE(room_id, user_id)

Ngoài SQL: **ChromaDB** lưu vector chunk với metadata `{document_id, course_id, chapter,
chunk_index, source_text, page}` — không phải bảng quan hệ.

Quy tắc xóa (vẽ chú thích cạnh FK):
- Xóa User → xóa messages + chat_sessions + quiz_attempts + room_members của user; SET NULL trên courses.owner_id, documents.uploaded_by, quizzes.created_by, rooms.created_by.
- Xóa Course → xóa documents (kèm vector Chroma), quizzes (kèm questions + attempts), rooms (kèm members), chapters; SET NULL chat_sessions.course_id.
- Xóa Quiz → xóa questions + attempts. Xóa Room → xóa room_members.

---

## 4. Sequence Diagrams (các luồng chính)

### 4.1. Đăng nhập
Participants: Người dùng → React UI → AuthRouter → AuthService → UserRepository → SQLite.
1. Nhập email/mật khẩu → `POST /api/auth/login` (form-urlencoded).
2. AuthService: tìm user theo email, verify bcrypt; sai → 401.
3. Đúng → encode JWT (sub=user_id, hạn `JWT_EXPIRE_MINUTES`) → trả `{access_token, user}`.
4. (Nhánh Google) `POST /api/auth/google` với idToken → verify bằng `GOOGLE_OAUTH_CLIENT_ID` → tìm user theo email (phải tồn tại sẵn) → JWT.

### 4.2. Yêu cầu tài khoản → Admin duyệt (FR-REQ)
Participants: Guest → React (LoginPage modal) → AccountRequestRouter → IPRateLimiter → AccountRequestService → UserService → Mailer (Brevo/SMTP) → SQLite; Admin → React (AdminPage tab).
1. Guest bấm "Yêu cầu tài khoản" → điền họ tên, email, vai trò (USER/LECTURER), lời nhắn → `POST /api/account-requests`.
2. IPRateLimiter: >5 yêu cầu/giờ/IP → 429.
3. Service: email đã có user → 400; email đã có yêu cầu PENDING → 400; role=ADMIN → 422.
4. Lưu AccountRequest(status=PENDING) → 201. Đồng thời gửi email báo Admin (`send_admin_new_request_email` tới `ADMIN_EMAIL`, best-effort — không chặn nếu mail chưa cấu hình/lỗi).
5. Admin mở tab "Yêu cầu chờ duyệt" → `GET /api/account-requests?status=PENDING` (chuông thông báo + danh sách).
6. **Duyệt**: `POST /api/account-requests/{id}/approve` → AccountRequestService gọi `UserService.create_account` (sinh mật khẩu ngẫu nhiên, hash bcrypt, lưu User, gửi email qua Brevo API/Gmail SMTP) → status=APPROVED, decided_at=now → trả `{request, email_sent, temp_password?}` (temp_password chỉ khi email gửi thất bại, để Admin gửi tay).
7. **Từ chối**: `POST /api/account-requests/{id}/reject` → status=REJECTED.
8. Yêu cầu đã xử lý mà duyệt/từ chối lại → 400.

### 4.3. Upload & Ingest tài liệu (RAG ingest)
Participants: Lecturer → React UI → DocumentRouter → DocumentService → Parser(Strategy) → Chunker → RagFacade → Embedder → ChromaDB → SQLite.
1. Chọn file + môn → `POST /api/documents` (multipart). Role guard: Lecturer/Admin.
2. Validate extension + MIME (chỉ .pdf/.docx/.pptx) → sai trả 400.
3. Tạo Document(status=PROCESSING) trong SQLite.
4. Parser theo loại file → text; Chunker (~800 token, overlap 100) → chunks.
5. Embedder (gemini-embedding-001 hoặc local) → vectors; ChromaDB.add(vectors + metadata).
6. Update status=INDEXED (lỗi → FAILED + error message). Trả DocumentOut.

### 4.4. Chat hỏi đáp RAG (chỉ Sinh viên)
Participants: Student → React UI → ChatRouter → RateLimiter(plan) + require_role(USER, ADMIN) → ChatService → RagFacade(Embedder + ChromaDB) → GeminiClient → SQLite.
1. `POST /api/chat {question, session_id?, course_id?}`.
2. Guard: Lecturer → 403. RateLimiter theo gói (Free 20/Pro 60/Max 120 mỗi phút, chỉ áp cho role USER) → quá → 429.
3. Lấy lịch sử hội thoại của session (tạo session mới nếu chưa có).
4. Embed câu hỏi → similarity search ChromaDB top-k=4 (filter course_id nếu có).
5. Build prompt: system ("chỉ trả lời từ context, không bịa, luôn dẫn nguồn") + chunks + history + câu hỏi → Gemini → answer.
6. Lưu message user + assistant (kèm citations_json) → trả `{session_id, answer, citations[]}`.

### 4.5. Quiz: làm bài + bảng điểm về Lecturer (FR-QZ)
Participants: Student, Lecturer → React UI → QuizRouter → QuizService → QuizRepository → SQLite.
1. Lecturer tạo quiz: `POST /api/quizzes {course_id, title, questions[]}` (mỗi câu ≥2 lựa chọn, 1 đáp án đúng).
2. Student mở đề: `GET /api/quizzes/{id}` → QuestionOut **không chứa correct_index**.
3. Student nộp: `POST /api/quizzes/{id}/submit {answers[]}` → service so từng câu với correct_index → score = đúng/tổng × 100.
4. **Chỉ khi role=USER** mới lưu QuizAttempt (Lecturer/Admin xem thử không ghi).
5. Trả AttemptResult {score, correct, total, results[] kèm đáp án đúng} → SV thấy điểm ngay.
6. Lecturer xem bảng điểm: `GET /api/quizzes/{id}/attempts` → guard: chỉ **người tạo quiz** hoặc Admin → repo JOIN users → [{user_name, user_email, score, created_at}] — đây là cơ chế "điểm tự gửi về giảng viên".

### 4.6. Phòng học (FR-ROOM)
Participants: Lecturer, Student → React UI → RoomRouter → RoomService → (QuizService, DocumentService, CourseRepository, UserRepository) → SQLite.
1. Lecturer tạo: `POST /api/rooms {name, description, course_id}` — guard Lecturer/Admin; course phải tồn tại → Room(created_by=lecturer).
2. Mời SV: `POST /api/rooms/{id}/members {email}` — guard người tạo/Admin; email phải là user role USER; không trùng (unique room_id+user_id) → RoomMember.
3. Danh sách: `GET /api/rooms` — Admin: tất cả; Lecturer: phòng mình tạo; Student: JOIN room_members phòng được mời.
4. Chi tiết: `GET /api/rooms/{id}` — guard: thành viên/người tạo/Admin → trả {room, members[] (JOIN users), quizzes[] của course, documents[] của course}.
5. Student làm quiz ngay trong phòng (gọi lại luồng 4.5); Lecturer xem bảng điểm trong phòng.
6. Gỡ SV: `DELETE /api/rooms/{id}/members/{user_id}`; Xóa phòng: `DELETE /api/rooms/{id}` (members xóa cascade).

### 4.7. Gói dịch vụ (FR-SUB)
1. `GET /api/plans` → 3 gói tĩnh (plans.py) + đánh dấu `current` theo user.plan.
2. Student `POST /api/subscriptions {plan_id}` → cập nhật user.plan (demo, không thanh toán thật).
3. RateLimiter đọc user.plan mỗi lần chat (xem 4.4).

---

## 5. Component / Architecture Diagram

### 5.1. Khối

- **Client Web**: React 18 + Vite + TS + Tailwind. Pages: LoginPage (+ modal Yêu cầu tài khoản), ChatPage, DocumentsPage, RoomsPage, RoomDetailPage, QuizzesPage, PricingPage, AdminPage (tab Users + tab Requests). Shared: api/client.ts (Axios + JWT interceptor), AuthContext, ChatSessionContext, i18n (VI/EN), ThemeContext, components/quiz/QuizModals (TakeQuizModal, AttemptsModal, Overlay).
- **Client Android**: Capacitor 8 webview bọc `dist/` — cùng codebase, gọi API qua `VITE_API_BASE`.
- **Backend FastAPI (Modular Monolith)**:
  - API layer: routers + CORS + OAuth2PasswordBearer JWT.
  - Business modules: `auth`, `account_requests`, `users`, `courses`, `documents`, `chat`, `quizzes`, `rooms`, `subscriptions`.
  - Shared services: `rag` (Embedder, VectorStore, Retriever — Facade), `llm` (GeminiClient), `shared/rate_limit` (RateLimiter theo plan + IPRateLimiter), `shared/mailer` (Brevo API / Gmail SMTP — gửi email duyệt tài khoản cho người dùng + email báo Admin khi có yêu cầu mới), `shared/dependencies` (get_current_user, require_role).
- **Data stores**: SQLite (hoặc SQL Server / Neon Postgres) — metadata; ChromaDB (hoặc pgvector) — vectors.
- **External**: Google Gemini API (chat + embedding), Google OAuth, Brevo email API.

### 5.2. Mũi tên phụ thuộc

- Web/Android → API (REST `/api/*`).
- API → mọi business module.
- documents → rag (ingest); chat → rag + llm + rate_limit; rooms → quizzes + documents + courses + users; account_requests → users (create_account) + mailer; auth → users; subscriptions → users.
- Mọi module nghiệp vụ → SQLite. rag → ChromaDB. llm → Gemini API. mailer → Brevo/Gmail.
- **Cấm**: module nghiệp vụ import thẳng `google.generativeai` (chỉ qua `llm/`); embedding chỉ qua `rag/embedder.py`.

---

## 6. State Diagrams

### 6.1. Document.status
- `[*] → PROCESSING` (upload)
- `PROCESSING → INDEXED` (parse + chunk + embed thành công)
- `PROCESSING → FAILED` (lỗi parse/embed, lưu error)
- `FAILED → PROCESSING` (upload lại file)
- `INDEXED / FAILED → [*]` (xóa tài liệu — xóa cả vector)

### 6.2. AccountRequest.status
- `[*] → PENDING` (guest gửi form)
- `PENDING → APPROVED` (Admin duyệt → tạo User + gửi email mật khẩu, set decided_at)
- `PENDING → REJECTED` (Admin từ chối, set decided_at)
- `APPROVED / REJECTED` là trạng thái cuối — gọi approve/reject lần nữa trả 400. Email đã APPROVED có thể gửi yêu cầu mới? Không cần — email lúc đó đã có tài khoản nên form chặn từ đầu.

---

## 7. Deployment Diagram

### 7.1. Local dev
- Node 18+ chạy Vite dev server :5173 (proxy `/api` → :8000).
- Python 3.11 venv chạy uvicorn :8000 (`--host 0.0.0.0` nếu cần điện thoại truy cập).
- SQLite file `backend/data/app.db`; ChromaDB dir `backend/data/chroma`.
- Android emulator gọi `http://10.0.2.2:8000/api`; điện thoại thật dùng IP LAN.

### 7.2. Production (free tier)
- **Vercel**: hosting frontend React (root `frontend/`, env `VITE_API_BASE`, `VITE_GOOGLE_CLIENT_ID`).
- **Render**: backend FastAPI (blueprint `render.yaml`; ngủ sau ~15 phút idle).
- **Neon**: Postgres + pgvector (DATABASE_URL `postgresql+psycopg2://`; vector backend `pgvector`).
- **Brevo**: gửi email cấp tài khoản qua HTTPS API (Render free chặn SMTP outbound).
- **Google Cloud**: OAuth Client ID (đăng nhập Google) + Gemini API key.
- Luồng: Browser → Vercel (static) → fetch → Render (FastAPI) → Neon (SQL + vector) / Gemini / Brevo.

---

## 8. Bảng API đầy đủ (để vẽ API map / swagger overview)

| Method | Path | Quyền | Ghi chú |
|--------|------|-------|---------|
| GET | /api/health | Public | |
| POST | /api/auth/login | Public | form-urlencoded → JWT |
| POST | /api/auth/google | Public | Google idToken → JWT |
| POST | /api/account-requests | Public | rate-limit 5/giờ/IP |
| GET | /api/account-requests?status= | Admin | |
| POST | /api/account-requests/{id}/approve | Admin | tạo tài khoản + email |
| POST | /api/account-requests/{id}/reject | Admin | |
| GET | /api/users | Admin | |
| POST | /api/users | Admin | mật khẩu tự sinh + email |
| PATCH | /api/users/{id}/role | Admin | |
| PATCH | /api/users/{id}/plan | Admin | chỉ với role USER |
| DELETE | /api/users/{id} | Admin | không tự xóa mình |
| GET | /api/courses | All (đã đăng nhập) | |
| POST | /api/courses | Lecturer, Admin | |
| GET | /api/courses/{id}/chapters | All | |
| DELETE | /api/courses/{id} | Lecturer (môn mình), Admin | cascade docs/quiz/rooms |
| POST | /api/documents | Lecturer, Admin | multipart; validate MIME+ext |
| GET | /api/documents?course_id= | All | |
| DELETE | /api/documents/{id} | Lecturer, Admin | xóa cả vector |
| POST | /api/chat | **USER, ADMIN** | Lecturer → 403; rate-limit theo gói |
| POST | /api/sessions | **USER, ADMIN** | |
| GET | /api/sessions | All | của mình; Admin: tất cả |
| GET | /api/sessions/{id} | Owner, Admin | |
| PATCH | /api/sessions/{id} | Owner, Admin | title/pinned |
| DELETE | /api/sessions/{id} | Owner, Admin | |
| GET | /api/quizzes?course_id= | All | |
| POST | /api/quizzes | Lecturer, Admin | |
| GET | /api/quizzes/{id} | All | ẩn correct_index |
| POST | /api/quizzes/{id}/submit | All | chỉ SV được ghi attempt |
| GET | /api/quizzes/{id}/attempts | Người tạo quiz, Admin | kèm tên + email SV |
| DELETE | /api/quizzes/{id} | Người tạo, Admin | |
| POST | /api/rooms | Lecturer, Admin | |
| GET | /api/rooms | All | theo vai trò |
| GET | /api/rooms/students | Lecturer, Admin | danh sách SV để mời |
| GET | /api/rooms/{id} | Thành viên, người tạo, Admin | members+quizzes+documents |
| POST | /api/rooms/{id}/members | Người tạo, Admin | mời qua email, chỉ role USER |
| DELETE | /api/rooms/{id}/members/{user_id} | Người tạo, Admin | |
| DELETE | /api/rooms/{id} | Người tạo, Admin | |
| GET | /api/plans | All | 3 gói + current |
| POST | /api/subscriptions | USER | Lecturer/Admin → 403 |
| GET | /api/subscriptions/me | All | |

---

## 9. Design Patterns (chú thích trên diagram kiến trúc)

| Pattern | Vị trí |
|---------|--------|
| Layered / Repository | mọi module: router → service → repository |
| Strategy | `documents/parsers.py` — chọn parser theo file type |
| Facade | `rag/` che giấu embedder + vector_store + retriever |
| Dependency Injection | FastAPI `Depends` (db session, current user, role guard, rate limiter) |
| DTO | Pydantic schemas tách model DB ↔ API contract |
| Pipeline | RAG ingest (parse→chunk→embed→store) & query (embed→search→prompt→LLM→cite) |
| RBAC | `require_role(...)` — 3 actor |
| Template reuse | Duyệt yêu cầu tài khoản tái dùng flow `create_account` (không lặp logic) |

## 10. Ràng buộc bảo mật / phi chức năng (chú thích)

- JWT Bearer cho mọi endpoint trừ Public; bcrypt hash mật khẩu.
- Rate-limit: chat theo gói (USER only — Free 20 / Pro 60 / Max 120 mỗi phút); form yêu cầu tài khoản 5/giờ/IP.
- Upload chỉ .pdf/.docx/.pptx — validate cả MIME lẫn extension server-side.
- Không log mật khẩu/API key/token; temp_password chỉ trả trong response khi email thất bại.
- Xóa tài liệu phải xóa cả vector ChromaDB lẫn metadata SQLite.
- Citations bắt buộc trong mọi câu trả lời AI.
