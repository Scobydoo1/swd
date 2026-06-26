# Hướng dẫn Prompt vẽ Diagram — Course Document RAG Chatbot (Maple 🍁)

Tài liệu này chứa **prompt sẵn dùng** để sinh từng loại sơ đồ cho dự án.
Mỗi mục gồm: **(1) Mục đích**, **(2) Prompt dán thẳng**, **(3) Công cụ gợi ý**.

> ⚠️ **Quy ước dữ liệu quan trọng:** `Role` được **tách thành một entity / bảng riêng**
> (`roles`), KHÔNG nhúng vào `users` dưới dạng cột enum. `User` tham chiếu Role qua
> khóa ngoại `role_id`. Tương tự `AccountRequest.requested_role_id → roles`.

---

## 0. Bối cảnh chung (luôn dán kèm mọi prompt)

```
BỐI CẢNH HỆ THỐNG — dùng làm nền cho mọi diagram:

Tên: Course Document RAG Chatbot "Maple" — web app hỏi đáp tài liệu môn học
bằng RAG (Retrieval Augmented Generation), trả lời CHỈ trong phạm vi tài liệu
đã upload, kèm trích dẫn nguồn.

Kiến trúc: Modular Monolith. Backend FastAPI (Python 3.11). Frontend React +
Vite + TypeScript + Tailwind, đóng gói Android qua Capacitor.

LLM: Google Gemini (gemini-2.5-flash) cho chat, gemini-embedding-001 cho
embedding — có chế độ "local/offline" làm mặc định khi chưa cấu hình API key.
Vector store: ChromaDB (cục bộ). Metadata DB: SQLite qua SQLAlchemy.
RAG framework: LangChain. Auth: JWT, RBAC.

3 ACTOR (phân quyền qua bảng Role riêng):
- ADMIN: toàn quyền — quản lý người dùng, duyệt yêu cầu tài khoản, quản lý mọi
  tài liệu/môn học/phòng, giám sát mọi phiên chat.
- LECTURER (Giảng viên): upload/xóa tài liệu môn mình, tạo môn học/chương,
  tạo quiz + xem bảng điểm, tạo phòng học + mời sinh viên. KHÔNG dùng AI chat.
- USER (Sinh viên): chat RAG, xem tài liệu, làm quiz, tham gia phòng được mời,
  quản lý phiên chat của mình, tự nâng gói. KHÔNG upload/quản trị.

9 MODULE backend: auth, account_requests, users, courses, documents, chat,
rag (core dùng chung: embedder + vector_store + retriever), quizzes, rooms,
subscriptions.
```

---

## 1. Architecture Diagram (Sơ đồ kiến trúc)

**Mục đích:** Thể hiện các tầng (frontend, API, module nghiệp vụ, hạ tầng AI/DB)
và luồng phụ thuộc của Modular Monolith.

**Prompt:**
```
Vẽ Architecture Diagram (sơ đồ kiến trúc phân tầng) cho hệ thống ở [BỐI CẢNH CHUNG].

Bố cục 5 tầng từ trên xuống:

1) CLIENT LAYER:
   - Web App (React + Vite + TS + Tailwind)
   - Android App (Capacitor bọc cùng build)
   Cả hai gọi backend qua Axios client (base URL cấu hình qua VITE_API_BASE),
   có cơ chế cold-start retry (10 lần) cho backend ngủ trên Render free tier.

2) API GATEWAY LAYER (FastAPI):
   - CORS middleware
   - JWT Auth middleware
   - Role Guard: require_role(...) đọc từ bảng Role
   - Mount 9 router

3) MODULE LAYER (mỗi module: Router -> Service -> Repository):
   auth | account_requests | users | courses | documents | chat |
   quizzes | rooms | subscriptions
   Vẽ kèm 2 shared component dùng chung:
   - rag (Facade): embedder + vector_store + retriever
   - llm: Google Gemini client wrapper (chat + embedding), có chế độ local fallback

4) DATA LAYER:
   - SQLite (SQLAlchemy ORM) — metadata: users, roles, courses, documents,
     chat, quizzes, rooms, account_requests
   - ChromaDB — vector embeddings + chunk text

5) EXTERNAL SERVICES:
   - Google Gemini API (chat + embedding)
   - Brevo API / Gmail SMTP (gửi email duyệt tài khoản)

Yêu cầu: mũi tên chỉ chiều phụ thuộc. Module chỉ giao tiếp qua service interface,
KHÔNG gọi thẳng repository của module khác. Module documents/chat/quizzes/rooms
dùng chung rag + llm qua Dependency Injection. Tô màu phân tầng rõ ràng.
```

**Công cụ:** Mermaid (`flowchart TB` với `subgraph` mỗi tầng), draw.io, Excalidraw.

---

## 2. Use Case Diagram (Sơ đồ ca sử dụng)

**Mục đích:** Liệt kê use case theo từng actor và quyền truy cập.

**Prompt:**
```
Vẽ Use Case Diagram cho hệ thống ở [BỐI CẢNH CHUNG], 3 actor: Admin, Lecturer,
User (Sinh viên), cộng thêm actor "Khách (Guest)" cho phần công khai.

GUEST (chưa đăng nhập):
- Đăng nhập (email/mật khẩu hoặc Google)
- Gửi Yêu cầu tài khoản (form công khai, rate-limit 5/giờ/IP)

USER (Sinh viên):
- Chat hỏi đáp RAG (xem trích dẫn nguồn)
- Quản lý phiên chat của mình (tạo, đổi tên, ghim, xóa)
- Xem danh sách tài liệu đã index
- Làm quiz, xem điểm
- Tham gia phòng học được mời
- Xem & nâng cấp gói dịch vụ (Free/Pro/Max)

LECTURER (Giảng viên):
- Upload / xóa tài liệu (PDF, DOCX, PPTX) -> ingest RAG
- Tạo & quản lý môn học / chương
- Xem trạng thái index tài liệu (PROCESSING/INDEXED/FAILED)
- Tạo & xóa quiz, xem bảng điểm sinh viên (tên + email)
- Tạo phòng học, mời/gỡ sinh viên, xóa phòng
- (KHÔNG dùng AI chat -> không có use case Chat)

ADMIN (bao toàn quyền của Lecturer +):
- CRUD người dùng, đổi role, đổi gói
- Duyệt / từ chối Yêu cầu tài khoản
- Quản lý MỌI tài liệu/môn học/phòng (không giới hạn ownership)
- Giám sát mọi phiên chat của mọi người dùng
- Cấu hình hệ thống (qua env)

Quan hệ:
- Admin generalize (kế thừa) các use case của Lecturer nơi phù hợp.
- "Chat hỏi đáp RAG" <<include>> "Xem trích dẫn nguồn".
- "Duyệt yêu cầu tài khoản" <<include>> "Tạo tài khoản + gửi email".
- "Upload tài liệu" <<include>> "Ingest RAG (chunk + embed)".
Ghi chú rate-limit chat theo gói chỉ áp cho Sinh viên.
```

**Công cụ:** PlantUML (`@startuml ... actor ... usecase`), draw.io.

---

## 3. MAIN FLOWS (Các luồng nghiệp vụ chính)

**Mục đích:** Sequence/Activity diagram cho các luồng cốt lõi. Vẽ **mỗi luồng một sơ đồ**.

### 3.1 RAG Query Flow (Chat hỏi đáp)
```
Vẽ Sequence Diagram "Chat hỏi đáp RAG" cho [BỐI CẢNH CHUNG].
Participant: Sinh viên -> Frontend -> chat/router -> RateLimiter (theo gói) ->
chat/service -> rag.retriever -> rag.embedder -> ChromaDB -> llm (Gemini) ->
chat/repository (SQLite).

Các bước:
1. Sinh viên gửi câu hỏi + session_id.
2. Router kiểm JWT + require_role(USER, ADMIN). Lecturer -> 403.
3. RateLimiter chặn nếu vượt hạn mức gói (Free 20/Pro 60/Max 120 câu/phút).
4. Service (tùy chọn) condense câu hỏi với lịch sử -> standalone question.
5. embedder tạo vector câu hỏi.
6. retriever similarity search ChromaDB (top-k=4, filter theo course_id).
7. Service build prompt: system prompt (CHỈ trả lời từ context, không bịa) +
   chunks + lịch sử + câu hỏi.
8. llm (Gemini hoặc local) sinh câu trả lời.
9. Service đính kèm citations (source_text, document, page).
10. repository lưu message user + assistant vào session.
11. Trả answer + citations về Frontend.
Thêm alt fragment: nếu retriever không có chunk phù hợp -> trả "không tìm thấy
trong tài liệu", vẫn lưu lịch sử.
```

### 3.2 Document Ingest Flow (Upload tài liệu)
```
Vẽ Activity Diagram "Ingest tài liệu" cho [BỐI CẢNH CHUNG].
Actor Lecturer/Admin upload file. Các bước:
1. Validate extension + MIME (chỉ .pdf/.docx/.pptx) -> sai thì trả lỗi rõ ràng.
2. Lưu metadata Document (status=PROCESSING).
3. Parse file -> text (Strategy theo loại: pypdf/python-docx/python-pptx).
4. Chunk text (RecursiveCharacterTextSplitter ~800 token, overlap ~100).
5. Embed từng chunk (gemini-embedding-001 hoặc local).
6. Lưu vector vào ChromaDB kèm metadata {document_id, course_id, chapter,
   chunk_index, source_text, page}.
7. Update Document.status = INDEXED (hoặc FAILED nếu lỗi, ghi error).
Dùng nhánh quyết định (decision node) cho validate và cho thành công/thất bại.
```

### 3.3 Account Request → Approval Flow (Yêu cầu & duyệt tài khoản)
```
Vẽ Sequence Diagram "Yêu cầu tài khoản và Admin duyệt" cho [BỐI CẢNH CHUNG].
Phần 1 (công khai): Guest -> Frontend -> account_requests/router ->
IPRateLimiter (5/giờ/IP) -> service. Service chặn nếu email đã có tài khoản
hoặc đã có yêu cầu PENDING -> tạo AccountRequest(PENDING) -> gửi email báo Admin
(best-effort, không chặn luồng).
Phần 2 (Admin): Admin -> router /{id}/approve -> service tái dùng
UserService.create_account (sinh mật khẩu ngẫu nhiên + hash bcrypt + lưu User
với role_id tương ứng) -> gửi email mật khẩu tạm (Brevo/SMTP) -> set status
APPROVED. Nhánh /{id}/reject -> set REJECTED. Yêu cầu đã xử lý không duyệt lại.
```

### 3.4 Auth / Login Flow
```
Vẽ Sequence Diagram "Đăng nhập" cho [BỐI CẢNH CHUNG], 2 nhánh:
(a) Email + mật khẩu: auth/router -> auth/service verify bcrypt -> security
encode JWT (hết hạn theo env) -> trả token + thông tin user (kèm role từ bảng Role).
(b) Google: nhận Google ID token -> verify -> tìm/khớp user theo email -> JWT.
Frontend lưu token, gắn vào header Authorization mọi request; 401 -> xóa token,
chuyển về /login.
```

### 3.5 Admin Governance Flow (Quản trị)
```
Vẽ Activity Diagram "Admin quản trị người dùng" cho [BỐI CẢNH CHUNG]:
Admin chọn user -> đổi role_id / đổi plan / xóa user -> Service kiểm quyền
require_role(ADMIN) -> cập nhật DB (xóa user phải xóa FK-safe: messages,
sessions trước) -> trả kết quả cập nhật. (Tùy chọn mở rộng: ghi Audit Log —
hiện CHƯA implement, đánh dấu là "future".)
```

**Công cụ:** Mermaid (`sequenceDiagram`, `flowchart` cho activity), PlantUML.

---

## 4. Conceptual ERD (Sơ đồ thực thể quan niệm)

**Mục đích:** Thực thể + quan hệ ở mức ý niệm, **Role là thực thể độc lập**.

**Prompt:**
```
Vẽ Conceptual ERD (mức quan niệm, chỉ thực thể + quan hệ, KHÔNG cần kiểu dữ liệu)
cho [BỐI CẢNH CHUNG]. QUAN TRỌNG: ROLE là thực thể RIÊNG, không gộp vào USER.

Thực thể:
ROLE, USER, COURSE, CHAPTER, DOCUMENT, CHAT_SESSION, MESSAGE, QUIZ, QUESTION,
QUIZ_ATTEMPT, ROOM, ROOM_MEMBER, ACCOUNT_REQUEST.

Quan hệ (kèm bội số):
- ROLE 1 --- N USER            (mỗi user có đúng 1 role; 1 role gán nhiều user)
- ROLE 1 --- N ACCOUNT_REQUEST (vai trò mong muốn)
- USER 1 --- N COURSE          (owner — giảng viên phụ trách)
- COURSE 1 --- N CHAPTER
- COURSE 1 --- N DOCUMENT
- CHAPTER 1 --- N DOCUMENT     (tùy chọn, document có thể chưa gắn chương)
- USER 1 --- N DOCUMENT        (người upload)
- USER 1 --- N CHAT_SESSION
- COURSE 1 --- N CHAT_SESSION  (phiên gắn ngữ cảnh môn, tùy chọn)
- CHAT_SESSION 1 --- N MESSAGE
- COURSE 1 --- N QUIZ
- USER 1 --- N QUIZ            (người tạo)
- QUIZ 1 --- N QUESTION
- QUIZ 1 --- N QUIZ_ATTEMPT
- USER 1 --- N QUIZ_ATTEMPT    (chỉ lưu lượt của Sinh viên)
- COURSE 1 --- N ROOM
- USER 1 --- N ROOM            (người tạo)
- ROOM 1 --- N ROOM_MEMBER
- USER 1 --- N ROOM_MEMBER     (ROOM_MEMBER là bảng nối N-N giữa ROOM và USER,
                                ràng buộc duy nhất (room_id, user_id))
Ghi chú: vector + chunk text KHÔNG nằm trong ERD này (lưu ở ChromaDB ngoài).
```

**Công cụ:** Mermaid `erDiagram`, draw.io (Chen/Crow's foot).

---

## 5. Class Diagram (Sơ đồ lớp)

**Mục đích:** Lớp domain/ORM với thuộc tính, kiểu, và quan hệ. **Role tách riêng.**

**Prompt:**
```
Vẽ Class Diagram (UML) cho tầng domain/ORM của [BỐI CẢNH CHUNG].
ROLE là class riêng; User tham chiếu Role qua role_id.

Class + thuộc tính:

Role:
  + id: int
  + code: str        // ADMIN | LECTURER | USER  (unique)
  + name: str
  + description: str

User:
  + id: int
  + email: str (unique)
  + password_hash: str
  + full_name: str
  + role_id: int -> Role
  + plan: Plan       // FREE | PRO | MAX (gói định nghĩa tĩnh, không bảng riêng)
  + created_at: datetime

Course: id, name, description, owner_id -> User
Chapter: id, course_id -> Course, title, order
Document: id, course_id -> Course, chapter_id? -> Chapter, uploaded_by? -> User,
          filename, file_type: FileType{PDF,DOCX,PPTX},
          status: Status{PROCESSING,INDEXED,FAILED}, num_chunks, error?, created_at
ChatSession: id, user_id? -> User, course_id? -> Course, title, pinned: bool, created_at
Message: id, session_id -> ChatSession, role: MsgRole{user,assistant}, content,
         citations_json?, created_at
Quiz: id, course_id -> Course, title, created_by? -> User, created_at
Question: id, quiz_id -> Quiz, text, options_json, correct_index: int, order: int
QuizAttempt: id, quiz_id -> Quiz, user_id? -> User, score: float, answers_json, created_at
Room: id, name, description, course_id -> Course, created_by? -> User, created_at
RoomMember: id, room_id -> Room, user_id -> User, added_at  // unique(room_id,user_id)
AccountRequest: id, email, full_name, requested_role_id -> Role, message,
                status: RequestStatus{PENDING,APPROVED,REJECTED}, created_at, decided_at?

Quan hệ:
- Composition: Course *-- Chapter; ChatSession *-- Message; Quiz *-- Question;
  Room *-- RoomMember (cascade delete).
- Association: User "1" -- "N" Role(role_id); các FK còn lại là association
  thường (nullable -> 0..1).
Hiển thị enum Role bị thay bằng class Role (bảng roles). Kèm các Enum:
Plan, FileType, Status, MsgRole, RequestStatus.

(Tùy chọn) Thêm các lớp tầng service theo pattern Layered:
<Module>Router -> <Module>Service -> <Module>Repository, và Facade RagService
(embedder + vector_store + retriever), LlmClient.
```

**Công cụ:** Mermaid `classDiagram`, PlantUML, draw.io.

---

## 6. DATABASE DESIGN (Lược đồ vật lý / Physical schema)

**Mục đích:** Bảng vật lý SQLite với PK, FK, kiểu cột, ràng buộc. **Bảng `roles` riêng.**

**Prompt:**
```
Vẽ DATABASE DESIGN (physical schema, crow's foot) cho [BỐI CẢNH CHUNG] trên SQLite.
TÁCH bảng roles RIÊNG; users tham chiếu roles qua role_id (FK).

Bảng:

roles
  id            INTEGER PK
  code          VARCHAR(20) UNIQUE NOT NULL   -- ADMIN | LECTURER | USER
  name          VARCHAR(100) NOT NULL
  description   VARCHAR(255)
  (seed sẵn 3 dòng: ADMIN, LECTURER, USER)

users
  id            INTEGER PK
  email         VARCHAR(255) UNIQUE NOT NULL, INDEX
  password_hash VARCHAR(255) NOT NULL
  full_name     VARCHAR(255) NOT NULL
  role_id       INTEGER FK -> roles(id) NOT NULL
  plan          VARCHAR(10) NOT NULL DEFAULT 'FREE'   -- FREE|PRO|MAX (tĩnh)
  created_at    DATETIME

courses
  id INTEGER PK, name VARCHAR(255), description VARCHAR(1000),
  owner_id INTEGER FK -> users(id) NULL

chapters
  id INTEGER PK, course_id INTEGER FK -> courses(id) NOT NULL,
  title VARCHAR(255), "order" INTEGER DEFAULT 0

documents
  id INTEGER PK, course_id INTEGER FK -> courses(id) NOT NULL,
  chapter_id INTEGER FK -> chapters(id) NULL,
  uploaded_by INTEGER FK -> users(id) NULL,
  filename VARCHAR(512), file_type VARCHAR(10) [PDF|DOCX|PPTX],
  status VARCHAR(12) [PROCESSING|INDEXED|FAILED] DEFAULT 'PROCESSING',
  num_chunks INTEGER DEFAULT 0, error VARCHAR(1000) NULL, created_at DATETIME

chat_sessions
  id INTEGER PK, user_id INTEGER FK -> users(id) NULL,
  course_id INTEGER FK -> courses(id) NULL,
  title VARCHAR(255) DEFAULT 'Cuộc trò chuyện mới',
  pinned BOOLEAN NOT NULL DEFAULT 0, created_at DATETIME

messages
  id INTEGER PK, session_id INTEGER FK -> chat_sessions(id) NOT NULL,
  role VARCHAR(10) [user|assistant], content TEXT,
  citations_json TEXT NULL, created_at DATETIME

quizzes
  id INTEGER PK, course_id INTEGER FK -> courses(id) NOT NULL,
  title VARCHAR(255), created_by INTEGER FK -> users(id) NULL, created_at DATETIME

quiz_questions
  id INTEGER PK, quiz_id INTEGER FK -> quizzes(id) NOT NULL,
  text TEXT, options_json TEXT, correct_index INTEGER, "order" INTEGER DEFAULT 0

quiz_attempts
  id INTEGER PK, quiz_id INTEGER FK -> quizzes(id) NOT NULL,
  user_id INTEGER FK -> users(id) NULL, score FLOAT,
  answers_json TEXT, created_at DATETIME

rooms
  id INTEGER PK, name VARCHAR(255), description VARCHAR(1000),
  course_id INTEGER FK -> courses(id) NOT NULL,
  created_by INTEGER FK -> users(id) NULL, created_at DATETIME

room_members
  id INTEGER PK, room_id INTEGER FK -> rooms(id) NOT NULL,
  user_id INTEGER FK -> users(id) NOT NULL, added_at DATETIME,
  UNIQUE(room_id, user_id)

account_requests
  id INTEGER PK, email VARCHAR(255) INDEX, full_name VARCHAR(255),
  requested_role_id INTEGER FK -> roles(id) NOT NULL,
  message VARCHAR(1000), status VARCHAR(10) [PENDING|APPROVED|REJECTED] DEFAULT 'PENDING',
  created_at DATETIME, decided_at DATETIME NULL

Ghi chú: ChromaDB (ngoài SQLite) lưu vector + chunk text với metadata
{document_id, course_id, chapter, chunk_index, source_text, page} — vẽ như store
ngoài, nối tới documents bằng đường nét đứt (logical link, không FK).
```

**Công cụ:** Mermaid `erDiagram` (có kiểu cột), dbdiagram.io (cú pháp DBML), draw.io.

> 💡 Lưu ý đồng bộ code: hiện tại code để `role` là **enum cột trong `users`**.
> Sơ đồ này mô tả thiết kế **chuẩn hóa Role thành bảng riêng** theo yêu cầu.
> Nếu muốn code khớp sơ đồ, cần thêm model `Role` + migration `role_id`.

---

## 7. DYNAMIC MODELING (Mô hình động)

**Mục đích:** State Machine + Sequence/Communication cho hành vi thay đổi trạng thái.

### 7.1 State Machine — Document
```
Vẽ State Machine Diagram cho vòng đời Document trong [BỐI CẢNH CHUNG]:
[*] -> PROCESSING (khi tạo metadata)
PROCESSING -> INDEXED (chunk + embed + lưu ChromaDB thành công)
PROCESSING -> FAILED (lỗi parse/embed, ghi error)
INDEXED -> [*] (xóa tài liệu: xóa vector ChromaDB + metadata SQLite)
FAILED -> [*] (xóa)
```

### 7.2 State Machine — AccountRequest
```
Vẽ State Machine cho AccountRequest:
[*] -> PENDING (gửi yêu cầu công khai)
PENDING -> APPROVED (Admin duyệt -> tạo user + email)
PENDING -> REJECTED (Admin từ chối)
APPROVED -> [*]; REJECTED -> [*]
(không cho phép chuyển trạng thái sau khi đã xử lý)
```

### 7.3 State Machine — ChatSession (tùy chọn)
```
Vẽ State Machine ChatSession: Active <-> Pinned (ghim/bỏ ghim), Active -> Deleted.
```

### 7.4 Communication/Sequence động cho Quiz
```
Vẽ Sequence Diagram "Làm & chấm Quiz" cho [BỐI CẢNH CHUNG]:
Sinh viên -> GET /quizzes/{id} (đề ẩn correct_index) -> làm bài ->
POST /quizzes/{id}/submit -> service chấm điểm (so answers_json vs correct_index)
-> trả score/correct/total + đáp án đúng. CHỈ lưu QuizAttempt nếu actor là Sinh viên;
Lecturer/Admin làm thử KHÔNG ghi attempt. Sau đó Lecturer -> GET
/quizzes/{id}/attempts -> bảng điểm kèm tên + email sinh viên.
```

**Công cụ:** Mermaid `stateDiagram-v2`, `sequenceDiagram`; PlantUML.

---

## 8. Các diagram khác (bổ sung)

### 8.1 Component Diagram
```
Vẽ Component Diagram cho [BỐI CẢNH CHUNG]: mỗi module backend là một component
với interface cung cấp (provided) và yêu cầu (required). Ví dụ DocumentsModule
provided: IDocumentService; required: IRagService (từ rag), ILlmClient (từ llm),
DB session. ChatModule required: IRagService, ILlmClient, IRateLimiter.
Thể hiện rag là Facade gói embedder + vector_store + retriever.
```

### 8.2 Deployment Diagram
```
Vẽ Deployment Diagram cho [BỐI CẢNH CHUNG]:
- Node "Client": trình duyệt (Web) + thiết bị Android (Capacitor WebView).
- Node "Backend Host" (vd Render): process Uvicorn/FastAPI, file SQLite, thư mục
  ChromaDB persistent.
- Node ngoài: Google Gemini API, Brevo/SMTP.
Giao thức: HTTPS REST giữa client và backend; HTTPS tới Gemini & Brevo.
Ghi chú CORS cho phép origin web localhost:5173, capacitor://localhost,
và domain GitHub Pages.
```

### 8.3 Package Diagram
```
Vẽ Package Diagram phản chiếu cây thư mục backend/app: main, config, database,
shared (exceptions, dependencies, rate_limit, mailer), modules/* (9 module),
llm. Mũi tên phụ thuộc: modules -> shared, modules -> llm, modules -> rag.
```

### 8.4 Data Flow Diagram (DFD) — RAG
```
Vẽ DFD cấp 1 cho pipeline RAG: External entity (User, Lecturer) -> Process
(Upload/Ingest, Query/Answer) -> Data store (SQLite metadata, ChromaDB vectors)
-> External (Gemini). Thể hiện luồng tài liệu đi vào và câu hỏi/câu trả lời đi ra.
```

---

## 9. Mẹo dùng nhanh

- **Mermaid trực tiếp:** dán prompt vào LLM kèm câu "xuất ra **Mermaid syntax**".
  Xem trước tại <https://mermaid.live>.
- **PlantUML:** thích hợp Use Case + Class chuẩn UML; xem tại <https://www.plantuml.com/plantuml>.
- **dbdiagram.io (DBML):** tốt nhất cho mục 6 DATABASE DESIGN.
- **Nhất quán Role:** luôn nhắc "Role là entity/bảng riêng, User dùng role_id"
  để mọi diagram đồng bộ.
- Mỗi prompt **đã nhúng dữ liệu thật của dự án** — chỉ cần ghép với [BỐI CẢNH CHUNG] ở §0.
```
