# Maple — Course Document RAG Chatbot

Web app chatbot hỏi đáp dựa trên tài liệu môn học (RAG — Retrieval Augmented Generation). Giảng viên upload tài liệu bài giảng (PDF/DOCX/PPTX), hệ thống tự động chunk + embed, và sinh viên đặt câu hỏi được trả lời **chỉ trong phạm vi tài liệu**, kèm **trích dẫn nguồn**. Cùng một codebase chạy được cả **website** lẫn **app Android** (Capacitor).

Môn học demo: _Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures_ (Gomaa).

---

## Tính năng chính

| Tính năng                 | Mô tả                                                                                                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Chat hỏi đáp RAG**      | Sinh viên chat theo ngữ cảnh hội thoại, câu trả lời bám sát tài liệu đã index và luôn kèm trích dẫn nguồn (tên tài liệu + trang). Render công thức toán LaTeX (KaTeX)       |
| **Quản lý tài liệu**      | Giảng viên upload PDF/DOCX/PPTX → tự động parse, chunk, embed vào vector store; theo dõi trạng thái PROCESSING / INDEXED / FAILED                                           |
| **Môn học & chương**      | Giảng viên tạo và quản lý môn học của mình; tài liệu, quiz, phòng học đều gắn theo môn                                                                                      |
| **Phòng học (Rooms)**     | Giảng viên tạo phòng gắn với môn học, mời sinh viên qua email; trong phòng có bảng tin thông báo, quiz để làm và tài liệu để học/tải về                                     |
| **Quiz trắc nghiệm**      | Giảng viên tạo quiz theo phòng học, tùy chọn mật khẩu + thời gian mở/đóng; sinh viên làm bài, chấm điểm tức thì; bảng điểm (kèm tên, email SV) tự gửi về giảng viên         |
| **AI soạn quiz (Gemini)** | Giảng viên nhờ AI soạn nháp đề từ tài liệu môn học, duyệt & chỉnh sửa trước khi lưu                                                                                         |
| **Bảng điểm & xem lại**   | Sinh viên xem mọi kết quả quiz theo môn, xem lại từng lượt làm (đáp án đã chọn vs đáp án đúng)                                                                              |
| **Yêu cầu tài khoản**     | Không có đăng ký công khai — người dùng gửi yêu cầu ở trang đăng nhập, Admin duyệt → tài khoản tạo tự động, mật khẩu gửi qua email (Brevo/SMTP). Chống spam theo IP         |
| **Phân quyền 3 vai trò**  | **Admin** (quản lý người dùng + duyệt yêu cầu), **Lecturer** (tài liệu, môn học, quiz, phòng học), **Student** (chat AI, làm quiz, tham gia phòng). JWT + role-based access |
| **Đăng nhập Google**      | Đăng nhập bằng Google OAuth với email đã được cấp tài khoản                                                                                                                 |
| **App Android**           | Build APK từ cùng codebase React qua Capacitor                                                                                                                              |

> Chat AI **chỉ dành cho Sinh viên** (giới hạn ~30 câu/phút mỗi SV). Giảng viên không dùng AI chat; giao diện Admin chỉ có mục Quản lý người dùng.

---

## Kiến trúc & Tech stack

**Modular Monolith** — một process FastAPI, chia module nghiệp vụ rõ ràng (router → service → repository), module `rag`/`llm` dùng chung qua Facade.

| Layer        | Công nghệ                                                        |
| ------------ | ---------------------------------------------------------------- |
| Frontend     | React 18 + Vite + TypeScript + Tailwind CSS                      |
| Mobile       | Capacitor 8 (Android APK từ cùng codebase web)                   |
| Backend      | Python 3.11+ / FastAPI                                           |
| LLM          | Google Gemini 2.5 Flash (có thể dùng `local` mode không cần key) |
| Embedding    | Google gemini-embedding-001 (hoặc local hash-based khi keyless)  |
| Vector store | ChromaDB (embedded/local)                                        |
| Metadata DB  | SQLite (SQLAlchemy)                                              |
| Auth         | JWT (role-based: ADMIN / LECTURER / USER)                        |

---

# Thiết kế hệ thống

> Sơ đồ vẽ bằng **Mermaid** — xem trực tiếp trên GitHub.

## 1. Use Case Diagram

```mermaid
graph LR
    Admin([👑 Admin])
    Lecturer([🎓 Lecturer])
    User([👤 Student])

    subgraph "Maple RAG Chatbot"
        UC1[Đăng nhập]
        UC2[Quản lý người dùng & role]
        UC3[Quản lý môn học / chương]
        UC4[Upload tài liệu PDF/DOCX/Slide]
        UC5[Xem danh sách tài liệu đã index]
        UC6[Xóa tài liệu]
        UC7[Chat hỏi đáp theo ngữ cảnh — chỉ Sinh viên]
        UC8[Xem trích dẫn nguồn]
        UC9[Quản lý phiên chat]
        UC10[Duyệt / từ chối yêu cầu tài khoản]
        UC11[Tạo & quản lý Quiz theo môn]
        UC12[Làm Quiz & xem điểm]
        UC14[Xem bảng điểm quiz của sinh viên]
        UC15[Tạo phòng học & mời sinh viên]
        UC16[Tham gia phòng học - quiz + tài liệu]
    end

    User --> UC1
    User --> UC5
    User --> UC7
    User --> UC8
    User --> UC9
    User --> UC12
    User --> UC16

    Lecturer --> UC1
    Lecturer --> UC3
    Lecturer --> UC4
    Lecturer --> UC5
    Lecturer --> UC6
    Lecturer --> UC11
    Lecturer --> UC14
    Lecturer --> UC15

    Admin --> UC1
    Admin --> UC2
    Admin --> UC10
```

> Admin **chỉ quản lý người dùng** + duyệt yêu cầu tài khoản (UI không có chat/quiz/phòng/tài liệu).
> Giảng viên **không** dùng AI chat (UC7) — hỏi đáp RAG là tính năng dành cho Sinh viên.

## 2. Class Diagram (Domain Model)

```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str password_hash
        +str full_name
        +int role_id
        +datetime created_at
    }
    class Role {
        +int id
        +str code
        +str name
        +str description
    }
    class Course {
        +int id
        +str name
        +str description
        +int owner_id
    }
    class Chapter {
        +int id
        +int course_id
        +str title
        +int order
    }
    class Document {
        +int id
        +int course_id
        +int chapter_id
        +int uploaded_by
        +str filename
        +FileType file_type
        +Status status
        +int num_chunks
        +datetime created_at
    }
    class ChatSession {
        +int id
        +int user_id
        +str title
        +datetime created_at
    }
    class Message {
        +int id
        +int session_id
        +MsgRole role
        +str content
        +json citations
        +datetime created_at
    }
    class Quiz {
        +int id
        +int course_id
        +int created_by
        +str title
        +datetime created_at
    }
    class Question {
        +int id
        +int quiz_id
        +str text
        +json options
        +int correct_index
    }
    class QuizAttempt {
        +int id
        +int quiz_id
        +int user_id
        +float score
        +json answers
        +datetime created_at
    }
    class Room {
        +int id
        +str name
        +str description
        +int course_id
        +int created_by
        +datetime created_at
    }
    class RoomMember {
        +int id
        +int room_id
        +int user_id
        +datetime added_at
    }

    Role "1" --> "0..*" User : assigned to
    User "1" --> "0..*" Course : owns
    User "1" --> "0..*" Document : uploads
    User "1" --> "0..*" ChatSession : has
    User "1" --> "0..*" Quiz : creates
    User "1" --> "0..*" QuizAttempt : attempts
    User "1" --> "0..*" Room : creates (Lecturer/Admin)
    User "1" --> "0..*" RoomMember : joins (Student)
    Course "1" --> "0..*" Chapter
    Course "1" --> "0..*" Document
    Course "1" --> "0..*" Quiz
    Course "1" --> "0..*" Room
    Room "1" --> "0..*" RoomMember
    ChatSession "1" --> "0..*" Message
    Quiz "1" --> "1..*" Question
    Quiz "1" --> "0..*" QuizAttempt
```

## 3. Sequence Diagram — Upload & Ingest tài liệu

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant FE as React UI
    participant R as DocumentRouter
    participant S as DocumentService
    participant P as Parser (Strategy)
    participant RAG as RagFacade
    participant E as Embedder
    participant C as ChromaDB
    participant DB as SQLite

    L->>FE: Chọn file + môn học
    FE->>R: POST /api/documents (file)
    R->>S: ingest(file, course_id)
    S->>DB: create Document (status=PROCESSING)
    S->>P: parse(file)
    P-->>S: text
    S->>S: chunk(text)
    S->>RAG: index_chunks(chunks)
    RAG->>E: embed(chunks)
    E-->>RAG: vectors
    RAG->>C: add(vectors, metadata)
    S->>DB: update status=INDEXED
    R-->>FE: 201 Created
    FE-->>L: "Đã index xong"
```

## 4. Sequence Diagram — Chat hỏi đáp (RAG Query)

```mermaid
sequenceDiagram
    actor U as Student
    participant FE as React UI
    participant R as ChatRouter
    participant S as ChatService
    participant RAG as RagFacade
    participant E as Embedder
    participant C as ChromaDB
    participant LLM as Gemini LLM
    participant DB as SQLite

    U->>FE: Nhập câu hỏi
    FE->>R: POST /api/chat {question, session_id}
    R->>S: answer(question, session_id)
    S->>DB: lấy lịch sử hội thoại
    S->>RAG: retrieve(question, k=4)
    RAG->>E: embed(question)
    RAG->>C: similarity search (filter course_id)
    C-->>RAG: top chunks + metadata
    S->>LLM: chat(system + context + history + question)
    LLM-->>S: answer
    S->>DB: lưu user + assistant message
    R-->>FE: {answer, citations}
    FE-->>U: Câu trả lời + trích dẫn nguồn
```

## 5. Sequence Diagram — Làm Quiz & Chấm điểm

```mermaid
sequenceDiagram
    actor S as Student
    participant FE as React UI
    participant R as QuizRouter
    participant SV as QuizService
    participant DB as SQLite

    S->>FE: Mở quiz
    FE->>R: GET /api/quizzes/{id}
    R->>SV: get_quiz(id)
    SV->>DB: lấy quiz + questions
    SV-->>R: đề bài (ẩn correct_index)
    R-->>FE: QuizDetail

    S->>FE: Chọn đáp án & Nộp bài
    FE->>R: POST /api/quizzes/{id}/submit {answers}
    R->>SV: submit(id, answers, user)
    SV->>DB: lấy questions (có correct_index)
    SV->>SV: chấm điểm từng câu
    SV->>DB: lưu QuizAttempt (chỉ khi người nộp là Sinh viên)
    SV-->>R: {score, correct, total, results[]}
    R-->>FE: AttemptResult
    FE-->>S: Kết quả + đáp án đúng

    actor L as Lecturer
    L->>FE: Mở "Kết quả" của quiz
    FE->>R: GET /api/quizzes/{id}/attempts
    R->>SV: list_attempts(id, lecturer)
    SV->>SV: chỉ người tạo quiz / Admin được xem
    SV->>DB: attempts JOIN users (tên + email SV)
    SV-->>R: [{user_name, user_email, score, ...}]
    R-->>FE: Bảng điểm sinh viên
    FE-->>L: Danh sách SV + điểm số
```

## 5b. Sequence Diagram — Phòng học (Rooms)

```mermaid
sequenceDiagram
    actor L as Lecturer
    actor S as Student
    participant FE as React UI
    participant R as RoomRouter
    participant SV as RoomService
    participant DB as SQLite

    L->>FE: Tạo phòng (tên + môn học)
    FE->>R: POST /api/rooms {name, course_id}
    R->>SV: create(payload, lecturer)
    SV->>DB: lưu Room (created_by=lecturer)
    R-->>FE: RoomOut

    L->>FE: Mời sinh viên (email)
    FE->>R: POST /api/rooms/{id}/members {email}
    R->>SV: invite(id, email, lecturer)
    SV->>SV: chỉ người tạo/Admin; chỉ mời role USER; không trùng
    SV->>DB: lưu RoomMember
    R-->>FE: MemberOut

    S->>FE: Mở "Phòng học"
    FE->>R: GET /api/rooms
    R->>SV: list_for(student)
    SV->>DB: rooms JOIN room_members (chỉ phòng được mời)
    R-->>FE: [RoomOut]
    S->>FE: Vào phòng
    FE->>R: GET /api/rooms/{id}
    R->>SV: detail(id, student)
    SV->>DB: members + quizzes + documents của môn
    R-->>FE: RoomDetail
    FE-->>S: Quiz để làm + tài liệu để học
```

## 6. Component / Architecture Diagram

```mermaid
graph TB
    subgraph Client["🖥️ Frontend — React (Vite + TS + Tailwind)"]
        CP[ChatPage]
        DP[DocumentsPage]
        RP[RoomsPage + RoomDetailPage]
        QP[QuizzesPage]
        AP[AdminPage]
    end

    subgraph Android["📱 Android App (Capacitor)"]
        APK[APK — webview bọc dist/]
    end

    subgraph Backend["⚙️ Backend — FastAPI (Modular Monolith)"]
        API[API Layer / Routers + CORS + JWT]

        subgraph Modules["Business Modules"]
            AUTH[auth]
            USERS[users]
            DOCS[documents]
            COURSES[courses]
            CHAT[chat]
            QUIZ[quizzes]
            ROOMS[rooms]
        end

        subgraph Shared["Shared Services"]
            RAG[rag: Embedder + Retriever + Facade]
            LLMW[llm: Gemini client]
            RL[rate_limit: giới hạn cố định cho SV]
        end
    end

    subgraph Data["💾 Data Stores"]
        SQLITE[(SQLite — metadata)]
        CHROMA[(ChromaDB — vectors)]
    end

    Client -->|REST /api| API
    Android -->|REST http://10.0.2.2:8000/api| API
    API --> AUTH & USERS & DOCS & COURSES & CHAT & QUIZ & ROOMS
    DOCS --> RAG
    CHAT --> RAG
    CHAT --> LLMW
    CHAT --> RL
    RL --> USERS
    AUTH --> USERS
    ROOMS --> QUIZ
    ROOMS --> DOCS
    DOCS & USERS & COURSES & CHAT & QUIZ & ROOMS --> SQLITE
    RAG --> CHROMA
```

## 7. ERD — Lược đồ quan hệ dữ liệu

```mermaid
erDiagram
    ROLE ||--o{ USER : "assigned to"
    ROLE ||--o{ ACCOUNT_REQUEST : "requested as"
    USER ||--o{ COURSE : "owns (Lecturer)"
    USER ||--o{ DOCUMENT : uploads
    USER ||--o{ CHATSESSION : has
    USER ||--o{ QUIZ : creates
    USER ||--o{ QUIZATTEMPT : attempts
    USER ||--o{ ROOM : "creates (Lecturer/Admin)"
    USER ||--o{ ROOM_MEMBER : "joins (Student)"
    COURSE ||--o{ CHAPTER : contains
    COURSE ||--o{ DOCUMENT : groups
    COURSE ||--o{ QUIZ : groups
    COURSE ||--o{ ROOM : groups
    ROOM ||--o{ ROOM_MEMBER : has
    CHAPTER ||--o{ DOCUMENT : "optional"
    CHATSESSION ||--o{ MESSAGE : contains
    QUIZ ||--|{ QUESTION : has
    QUIZ ||--o{ QUIZATTEMPT : records

    ROLE {
        int id PK
        string code UK "ADMIN|LECTURER|USER"
        string name
        string description
    }
    USER {
        int id PK
        string email UK
        string password_hash
        string full_name
        int role_id FK
        datetime created_at
    }
    ACCOUNT_REQUEST {
        int id PK
        string email
        string full_name
        int requested_role_id FK
        string message
        enum status "PENDING|APPROVED|REJECTED"
        datetime created_at
        datetime decided_at
    }
    QUIZ {
        int id PK
        int course_id FK
        int created_by FK
        string title
        datetime created_at
    }
    QUESTION {
        int id PK
        int quiz_id FK
        string text
        json options
        int correct_index
    }
    QUIZATTEMPT {
        int id PK
        int quiz_id FK
        int user_id FK
        float score
        json answers
        datetime created_at
    }
    ROOM {
        int id PK
        string name
        string description
        int course_id FK
        int created_by FK
        datetime created_at
    }
    ROOM_MEMBER {
        int id PK
        int room_id FK
        int user_id FK
        datetime added_at
    }
    CHATSESSION {
        int id PK
        int user_id FK
        string title
        datetime created_at
    }
    MESSAGE {
        int id PK
        int session_id FK
        enum role "user|assistant"
        string content
        json citations_json
        datetime created_at
    }
```

## 8. State Diagram — Vòng đời tài liệu

```mermaid
stateDiagram-v2
    [*] --> PROCESSING : upload
    PROCESSING --> INDEXED : parse + chunk + embed thành công
    PROCESSING --> FAILED : lỗi parse / embed
    FAILED --> PROCESSING : upload lại
    INDEXED --> [*] : xóa tài liệu
    FAILED --> [*] : xóa tài liệu
```

## 9. Design Patterns

| Pattern                  | Áp dụng                                                      |
| ------------------------ | ------------------------------------------------------------ |
| **Layered / Repository** | Mọi module: router → service → repository                    |
| **Strategy**             | `parsers.py` — chọn parser theo file type (PDF/DOCX/PPTX)    |
| **Facade**               | `rag/` module — che giấu embedder + vector_store + retriever |
| **Dependency Injection** | FastAPI `Depends` inject service/repo/session                |
| **DTO**                  | Pydantic schemas tách biệt model DB và API contract          |
| **Pipeline**             | RAG ingest & query — chuỗi bước rõ ràng                      |
| **RBAC**                 | `require_role()` dependency — phân quyền 3 actor             |

---

## Cài đặt & Chạy

### Yêu cầu

- Python 3.11+
- Node.js 18+
- (Tuỳ chọn) Google API Key để dùng Gemini — không cần nếu dùng mode `local`

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # xem cấu hình bên dưới

python seed.py         # tạo 3 user demo + môn học + quiz mẫu

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

**Cấu hình `.env`:**

```env
# Mode "local" (không cần key) — AI trả lời placeholder, RAG vẫn hoạt động
EMBED_PROVIDER=local
LLM_PROVIDER=local

# Hoặc dùng Gemini thật:
GOOGLE_API_KEY=AIza...
EMBED_PROVIDER=gemini
LLM_PROVIDER=gemini
GOOGLE_CHAT_MODEL=gemini-2.5-flash
GOOGLE_EMBED_MODEL=gemini-embedding-001

CHROMA_DIR=./data/chroma
DATABASE_URL=sqlite:///./data/app.db

# Bắt buộc đổi: chuỗi ngẫu nhiên dài
JWT_SECRET=<chuoi-ngau-nhien-dai-cua-ban>
JWT_EXPIRE_MINUTES=720

CORS_ORIGINS=http://localhost:5173,http://localhost,https://localhost,capacitor://localhost
```

> Muốn dùng **SQL Server** thay SQLite: chỉ cần đổi `DATABASE_URL` sang dạng
> `mssql+pyodbc://<user>:<password>@localhost/maple?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes`
> (cần ODBC Driver 17). App tự tạo bảng khi khởi động.

### 2. Frontend (Web)

```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:5173

### 3. Android APK (Capacitor)

> Yêu cầu: Android Studio (kèm JDK + SDK).

```bash
cd frontend
npm install

# Backend trên máy host, chạy trong emulator:
$env:VITE_API_BASE = "http://10.0.2.2:8000/api"   # PowerShell
# export VITE_API_BASE="http://10.0.2.2:8000/api"  # bash

npm run cap:apk
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

Điện thoại thật cùng Wi-Fi: thay `10.0.2.2` bằng IP LAN của máy chạy backend và chạy backend với `--host 0.0.0.0`.

### Tài khoản demo (chỉ local)

Chạy `python seed.py` — email + mật khẩu 3 tài khoản demo (Admin / Lecturer / Student) in ra console.

> ⚠️ Không chạy `seed.py` trên production (script tự từ chối khi `DATABASE_URL` không phải SQLite). Trên production, Admin đầu tiên tạo từ env `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

---

## Quy trình sử dụng

1. **Cấp tài khoản** — người dùng bấm _Yêu cầu tài khoản_ ở trang đăng nhập → Admin duyệt trong tab _Yêu cầu chờ duyệt_ → mật khẩu gửi qua email.
2. **Giảng viên** — tạo môn học, upload tài liệu (đợi trạng thái _Đã index_), tạo phòng học, mời sinh viên, giao quiz (tự soạn hoặc nhờ AI soạn nháp).
3. **Sinh viên** — vào _Hỏi đáp_ chọn môn và đặt câu hỏi (có trích dẫn nguồn); vào _Phòng học_ để làm quiz, xem thông báo và tải tài liệu; xem _Bảng điểm_ và xem lại bài làm.
4. **Admin** — quản lý người dùng (tạo, đổi vai trò, xóa) và duyệt yêu cầu tài khoản.

---

## Deploy free: Vercel + Render + Neon

| Thành phần | Dịch vụ                                                    | Ghi chú                                                                                                                                                                                          |
| ---------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Database   | [Neon](https://neon.tech) (Postgres + pgvector)            | Đổi prefix `postgresql://` → `postgresql+psycopg2://` trong `DATABASE_URL`                                                                                                                       |
| Backend    | [Render](https://render.com) (Blueprint đọc `render.yaml`) | Điền env: `DATABASE_URL`, `GOOGLE_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `BREVO_API_KEY`, `MAIL_FROM`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `CORS_ORIGINS`, `APP_LOGIN_URL`. Free tier ngủ sau ~15 phút |
| Frontend   | [Vercel](https://vercel.com) (Root Directory: `frontend`)  | Env: `VITE_API_BASE=https://<app>.onrender.com/api`, `VITE_GOOGLE_CLIENT_ID`                                                                                                                     |

- **Google OAuth**: tạo OAuth Client ID (Web) tại Google Cloud Console, thêm origins `http://localhost:5173` + domain Vercel.
- **Email cấp tài khoản**: Render free chặn SMTP → dùng [Brevo](https://www.brevo.com) API (free 300 mail/ngày): verify sender + lấy API key `xkeysib-...`. Chạy local vẫn dùng được Gmail SMTP (`SMTP_USER` + `SMTP_PASSWORD`).

---

## Kiểm thử & Đánh giá

```bash
cd backend

# Unit/API tests (pytest, DB tạm + FK enforcement)
python -m pytest tests/ -q

# Smoke test toàn bộ chức năng qua API (không cần API key)
python -m tests.smoke_all
python -m tests.smoke_rooms

# Đánh giá RAG: 50 câu hỏi + ground truth (tests/test_set.json), LLM-as-judge
python -m tests.evaluate --course-id 1
```

---

## Cấu trúc thư mục

```
swd/
├── readme.md
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, mount routers
│   │   ├── config.py            # Settings từ .env
│   │   ├── database.py          # SQLAlchemy engine + auto-migration nhẹ
│   │   ├── llm/                 # Gemini client wrapper
│   │   ├── shared/              # dependencies (JWT, require_role), mailer, rate-limit
│   │   └── modules/             # auth, account_requests, users, courses,
│   │                            # documents, chat, rag, quizzes, rooms
│   ├── seed.py                  # Seed user demo + môn học + quiz mẫu
│   ├── tests/                   # pytest + smoke test + test_set.json (50 câu)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/               # Chat, Documents, Rooms, Quizzes, Grade, Admin, Login
    │   ├── components/          # chat, quiz, profile, layout...
    │   ├── api/client.ts        # Axios + VITE_API_BASE (web & APK)
    │   └── auth/AuthContext.tsx
    ├── android/                 # Native Android project (Capacitor)
    ├── capacitor.config.ts
    └── vite.config.ts
```
