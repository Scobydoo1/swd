# Maple — Course Document RAG Chatbot

Web app chatbot hỏi đáp dựa trên tài liệu môn học (RAG). Người dùng upload tài liệu bài giảng (PDF/DOCX/Slide), hệ thống tự động chunk + embed, và trả lời câu hỏi **chỉ trong phạm vi tài liệu**, có trích dẫn nguồn. Cùng một codebase chạy được cả **website** lẫn **app Android cài đặt** (Capacitor).

Môn học demo: *Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures*.

> Tài liệu thiết kế đầy đủ: [CLAUDE.md](CLAUDE.md)

---

## Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **Chat & Hỏi đáp RAG** | Chat theo ngữ cảnh hội thoại, trích dẫn nguồn, giới hạn trong tài liệu đã index |
| **Quản lý tài liệu** | Upload PDF/DOCX/PPTX → tự động chunk & embed, xem trạng thái (PROCESSING / INDEXED / FAILED) |
| **Quiz trắc nghiệm** | Lecturer tạo quiz; student làm bài, nộp → chấm điểm tức thì, hiện đáp án đúng |
| **Gói dịch vụ** | 3 gói Free / Pro / Max cho **sinh viên** (rate-limit chat theo gói, nâng cấp tự phục vụ); giảng viên & admin được miễn |
| **Phân quyền 3 actor** | Admin (toàn quyền), Lecturer (tài liệu + quiz + môn học), User/Student (chat + làm quiz) |
| **App Android** | APK cài đặt từ cùng codebase React, build qua Capacitor |

---

## Kiến trúc

**Modular Monolith** — một process FastAPI, module nghiệp vụ rõ ràng.

| Layer | Công nghệ |
|-------|-----------|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| Mobile | Capacitor 8 (Android APK từ cùng codebase web) |
| Backend | Python 3.11+ / FastAPI |
| LLM | Google Gemini 2.5 Flash (có thể dùng `local` mode không cần key) |
| Embedding | Google gemini-embedding-001 (hoặc local hash-based khi keyless) |
| Vector store | ChromaDB (embedded/local) |
| Metadata DB | SQLite (SQLAlchemy) |
| Auth | JWT (role-based: ADMIN / LECTURER / USER) |

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
        UC1[Đăng nhập / Đăng ký]
        UC2[Quản lý người dùng & role & plan]
        UC3[Quản lý môn học / chương]
        UC4[Upload tài liệu PDF/DOCX/Slide]
        UC5[Xem danh sách tài liệu đã index]
        UC6[Xóa tài liệu]
        UC7[Chat hỏi đáp theo ngữ cảnh]
        UC8[Xem trích dẫn nguồn]
        UC9[Quản lý phiên chat]
        UC10[Xem thống kê / lịch sử toàn hệ thống]
        UC11[Tạo & quản lý Quiz]
        UC12[Làm Quiz & xem điểm]
        UC13[Xem & nâng cấp gói dịch vụ]
    end

    User --> UC1
    User --> UC5
    User --> UC7
    User --> UC8
    User --> UC9
    User --> UC12
    User --> UC13

    Lecturer --> UC1
    Lecturer --> UC3
    Lecturer --> UC4
    Lecturer --> UC5
    Lecturer --> UC6
    Lecturer --> UC7
    Lecturer --> UC8
    Lecturer --> UC9
    Lecturer --> UC11
    Lecturer --> UC12
    Lecturer --> UC13

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
```

## 2. Class Diagram (Domain Model)

```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str password_hash
        +str full_name
        +Role role
        +Plan plan
        +datetime created_at
    }
    class Role {
        <<enumeration>>
        ADMIN
        LECTURER
        USER
    }
    class Plan {
        <<enumeration>>
        FREE
        PRO
        MAX
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

    User --> Role
    User --> Plan
    User "1" --> "0..*" Course : owns
    User "1" --> "0..*" Document : uploads
    User "1" --> "0..*" ChatSession : has
    User "1" --> "0..*" Quiz : creates
    User "1" --> "0..*" QuizAttempt : attempts
    Course "1" --> "0..*" Chapter
    Course "1" --> "0..*" Document
    Course "1" --> "0..*" Quiz
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
    R->>SV: submit(id, answers, user_id)
    SV->>DB: lấy questions (có correct_index)
    SV->>SV: chấm điểm từng câu
    SV->>DB: lưu QuizAttempt
    SV-->>R: {score, correct, total, results[]}
    R-->>FE: AttemptResult
    FE-->>S: Kết quả + đáp án đúng
```

## 6. Component / Architecture Diagram

```mermaid
graph TB
    subgraph Client["🖥️ Frontend — React (Vite + TS + Tailwind)"]
        CP[ChatPage]
        DP[DocumentsPage]
        QP[QuizzesPage]
        PP[PricingPage]
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
            SUB[subscriptions]
        end

        subgraph Shared["Shared Services"]
            RAG[rag: Embedder + Retriever + Facade]
            LLMW[llm: Gemini client]
            RL[rate_limit: plan-aware]
        end
    end

    subgraph Data["💾 Data Stores"]
        SQLITE[(SQLite — metadata)]
        CHROMA[(ChromaDB — vectors)]
    end

    Client -->|REST /api| API
    Android -->|REST http://10.0.2.2:8000/api| API
    API --> AUTH & USERS & DOCS & COURSES & CHAT & QUIZ & SUB
    DOCS --> RAG
    CHAT --> RAG
    CHAT --> LLMW
    CHAT --> RL
    RL --> USERS
    AUTH --> USERS
    DOCS & USERS & COURSES & CHAT & QUIZ --> SQLITE
    RAG --> CHROMA
```

## 7. ERD — Lược đồ quan hệ dữ liệu

```mermaid
erDiagram
    USER ||--o{ COURSE : "owns (Lecturer)"
    USER ||--o{ DOCUMENT : uploads
    USER ||--o{ CHATSESSION : has
    USER ||--o{ QUIZ : creates
    USER ||--o{ QUIZATTEMPT : attempts
    COURSE ||--o{ CHAPTER : contains
    COURSE ||--o{ DOCUMENT : groups
    COURSE ||--o{ QUIZ : groups
    CHAPTER ||--o{ DOCUMENT : "optional"
    CHATSESSION ||--o{ MESSAGE : contains
    QUIZ ||--|{ QUESTION : has
    QUIZ ||--o{ QUIZATTEMPT : records

    USER {
        int id PK
        string email UK
        string password_hash
        string full_name
        enum role "ADMIN|LECTURER|USER"
        enum plan "FREE|PRO|MAX"
        datetime created_at
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

| Pattern | Áp dụng |
|---------|---------|
| **Layered / Repository** | Mọi module: router → service → repository |
| **Strategy** | `parsers.py` — chọn parser theo file type (PDF/DOCX/PPTX) |
| **Facade** | `rag/` module — che giấu embedder + vector_store + retriever |
| **Dependency Injection** | FastAPI `Depends` inject service/repo/session |
| **DTO** | Pydantic schemas tách biệt model DB và API contract |
| **Pipeline** | RAG ingest & query — chuỗi bước rõ ràng |
| **RBAC** | `require_role()` dependency — phân quyền 3 actor |

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

cp .env.example .env   # xem hướng dẫn env bên dưới

python seed.py         # tạo 3 user demo + môn học + quiz mẫu

uvicorn app.main:app --reload --port 8000
# Hoặc mở cho điện thoại/emulator truy cập:
uvicorn app.main:app --host 0.0.0.0 --reload --port 8000
```

API docs: http://localhost:8000/docs

**Cấu hình `.env`:**

```env
# Để mode "local" (không cần key) — AI trả lời bằng placeholder, RAG vẫn hoạt động
EMBED_PROVIDER=local
LLM_PROVIDER=local

# Hoặc dùng Gemini thật:
GOOGLE_API_KEY=AIza...
EMBED_PROVIDER=gemini
LLM_PROVIDER=gemini
GOOGLE_CHAT_MODEL=gemini-2.5-flash
GOOGLE_EMBED_MODEL=gemini-embedding-001

CHROMA_DIR=./data/chroma

# CSDL: mặc định SQLite (chạy ngay). Đổi sang SQL Server — xem mục bên dưới.
DATABASE_URL=sqlite:///./data/app.db

JWT_SECRET=change-me-in-production
JWT_EXPIRE_MINUTES=720

# CORS: thêm origin localhost cho app Capacitor (Android)
CORS_ORIGINS=http://localhost:5173,http://localhost,https://localhost,capacitor://localhost
```

### Kết nối SQL Server (tùy chọn)

Mặc định dự án dùng **SQLite** (file `data/app.db`, không cần cài gì). Có thể chuyển
sang **Microsoft SQL Server** chỉ bằng cách đổi `DATABASE_URL` — code đã tự nhận diện
dialect (chỉ SQLite mới chạy migration `PRAGMA`, các kiểu chuỗi đã có độ dài để index được trên SQL Server).

**Bước 1 — Cài driver** (ngoài `requirements.txt` đã có `pyodbc`, cần ODBC Driver trên máy):

- Windows: cài sẵn **ODBC Driver 17 for SQL Server** (thường có cùng SQL Server / SSMS).
- Bật **TCP/IP** và dịch vụ **SQL Server Browser** nếu dùng named instance.

**Bước 2 — Tạo database** (một lần) bằng SSMS hoặc `sqlcmd`:

```sql
CREATE DATABASE maple;
```

**Bước 3 — Đặt `DATABASE_URL` trong `.env`** (ví dụ user `sa` / mật khẩu `123`, instance tên `THANH`):

```env
DATABASE_URL=mssql+pyodbc://sa:123@localhost\THANH/maple?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes
```

- **Default instance** (không có tên): bỏ `\THANH` → `...@localhost/maple?driver=...`
- **Cổng cụ thể**: `...@localhost,1433/maple?driver=...`
- Mật khẩu có ký tự đặc biệt (`@ : / \`) phải URL-encode (vd `@` → `%40`).

**Bước 4 — Tạo bảng + seed** rồi chạy như bình thường:

```bash
python seed.py                     # init_db() tự CREATE tất cả bảng trong SQL Server
uvicorn app.main:app --reload --port 8000
```

> Lược đồ vật lý đầy đủ (DDL) ở [docs/schema.sql](docs/schema.sql).

### 2. Frontend (Web)

```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:5173

### 3. Android APK (Capacitor)

> Yêu cầu: Android Studio đã cài (mang theo JDK + SDK).

```bash
cd frontend
npm install

# Build APK debug cho emulator (backend trên máy host)
$env:VITE_API_BASE = "http://10.0.2.2:8000/api"   # PowerShell
# export VITE_API_BASE="http://10.0.2.2:8000/api"  # bash

npm run cap:apk
# APK output: android/app/build/outputs/apk/debug/app-debug.apk

# Hoặc mở Android Studio để build/run trực tiếp:
npm run cap:sync
npm run cap:open
```

**Điện thoại thật cùng Wi-Fi:** thay `10.0.2.2` bằng IP LAN của máy chạy backend (ví dụ `192.168.100.6`), và backend phải chạy với `--host 0.0.0.0`.

**Live-reload khi dev** (không cần rebuild APK): mở comment dòng `server.url` trong [frontend/capacitor.config.ts](frontend/capacitor.config.ts) trỏ về Vite dev server.

### Tài khoản demo

| Vai trò | Email | Mật khẩu | Gói |
|---------|-------|----------|-----|
| Admin | admin@demo.com | admin123 | — (không cần) |
| Lecturer | lecturer@demo.com | lecturer123 | — (không cần) |
| Student | student@demo.com | student123 | FREE |

> Gói dịch vụ **chỉ áp dụng cho Sinh viên**. Giảng viên & Admin dùng đầy đủ tính năng, không bị rate-limit theo gói.

> **Lưu ý:** Không còn đăng ký công khai. Tài khoản Sinh viên/Giảng viên do **Admin cấp** trong trang Quản lý người dùng — hệ thống tự sinh mật khẩu và gửi qua email; người dùng cũng có thể **đăng nhập bằng Google** với email đã được cấp. Admin đầu tiên seed từ env `ADMIN_EMAIL`/`ADMIN_PASSWORD` khi khởi động (hoặc chạy `python seed.py` để có dữ liệu demo).

---

## Deploy free: Vercel + Render + Neon

### 1. Neon (Postgres + pgvector — dữ liệu bền vững)
1. Tạo project free tại https://neon.tech → copy connection string.
2. Đổi prefix `postgresql://` thành `postgresql+psycopg2://` khi dùng làm `DATABASE_URL`.
   (pgvector được bật tự động bởi app: `CREATE EXTENSION IF NOT EXISTS vector`.)

### 2. Render (backend FastAPI)
1. https://render.com → New → Blueprint → trỏ repo này (đọc [render.yaml](render.yaml)).
2. Điền env: `DATABASE_URL` (Neon), `GOOGLE_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`,
   `BREVO_API_KEY`/`MAIL_FROM` (gửi email — xem mục 5), `ADMIN_EMAIL`/`ADMIN_PASSWORD`,
   `CORS_ORIGINS` (gồm domain Vercel), `APP_LOGIN_URL` (URL Vercel).
3. Lưu ý free tier: service ngủ sau ~15 phút không dùng — request đầu mất 30–60s đánh thức.

### 3. Vercel (frontend React)
1. https://vercel.com → Add New Project → import repo, **Root Directory: `frontend`**.
2. Env: `VITE_API_BASE=https://<app>.onrender.com/api`, `VITE_GOOGLE_CLIENT_ID=<client-id>`.
3. Deploy → lấy URL `https://<app>.vercel.app`, quay lại Render thêm vào `CORS_ORIGINS`.

### 4. Google OAuth Client ID (đăng nhập Google)
1. https://console.cloud.google.com → APIs & Services → Credentials →
   Create Credentials → OAuth client ID → Web application.
2. Authorized JavaScript origins: `http://localhost:5173` và `https://<app>.vercel.app`.
3. Copy Client ID → set `GOOGLE_OAUTH_CLIENT_ID` (Render) và `VITE_GOOGLE_CLIENT_ID` (Vercel) — cùng một giá trị.

### 5. Gửi email cấp tài khoản — Brevo API (bắt buộc trên Render)
> ⚠️ Render free **chặn kết nối SMTP ra ngoài** (OSError 101) nên Gmail SMTP không chạy
> trên Render — chỉ dùng được khi chạy local. Production dùng Brevo (free 300 mail/ngày).
1. Đăng ký free tại https://www.brevo.com (xác nhận email).
2. Verify sender: **Senders & IP → Senders → Add a sender** → nhập Gmail của bạn →
   bấm link xác nhận trong hộp thư.
3. Lấy API key: bấm tên tài khoản (góc phải) → **SMTP & API → API Keys →
   Generate a new API key** → copy chuỗi `xkeysib-...`.
4. Trên Render thêm env: `BREVO_API_KEY=xkeysib-...` và `MAIL_FROM=<gmail đã verify>`.

(Chạy local vẫn dùng được Gmail SMTP: `SMTP_USER` + `SMTP_PASSWORD` (App Password
tạo tại https://myaccount.google.com/apppasswords). Có `BREVO_API_KEY` thì Brevo
được ưu tiên.)

> Vì sao không deploy backend lên Vercel? Vercel serverless không giữ file giữa các request — SQLite/ChromaDB sẽ mất dữ liệu. Render chạy process thường, còn dữ liệu (metadata + vector) đặt ở Neon Postgres nên không mất khi service ngủ/restart.

---

## Ảnh chụp giao diện

**Web** (React + Vite + Tailwind)

| Hỏi đáp (RAG) | Tài liệu | Quiz |
|---|---|---|
| ![Chat](docs/screenshots/web/02-chat.png) | ![Tài liệu](docs/screenshots/web/03-documents.png) | ![Quiz](docs/screenshots/web/04-quizzes.png) |

| Gói dịch vụ (Sinh viên) | Tạo quiz (Lecturer) | Quản lý người dùng (Admin) |
|---|---|---|
| ![Pricing](docs/screenshots/web/05-pricing.png) | ![Tạo quiz](docs/screenshots/web/07-quiz-create-modal.png) | ![Admin](docs/screenshots/web/06-admin-users.png) |

**Android** (Capacitor — cùng codebase)

| Đăng nhập | Hỏi đáp | Quiz | Menu Giảng viên (không có gói) |
|---|---|---|---|
| ![Login](docs/screenshots/mobile/01-launch.png) | ![Chat](docs/screenshots/mobile/04-chat.png) | ![Quiz](docs/screenshots/mobile/05-quizzes.png) | ![Lecturer](docs/screenshots/mobile/06-lecturer-nav.png) |

---

## Quy trình sử dụng

**Hỏi đáp RAG:**
1. Đăng nhập Lecturer → vào **Tài liệu** → upload PDF/DOCX/PPTX. Đợi trạng thái *Đã index*.
2. Đăng nhập Student → vào **Hỏi đáp** → chọn môn → đặt câu hỏi → nhận câu trả lời kèm trích dẫn.

**Quiz:**
1. Lecturer → **Quiz** → **Tạo quiz** → điền câu hỏi + đáp án → lưu.
2. Student → **Quiz** → **Làm bài** → chọn đáp án → **Nộp bài** → xem điểm + đáp án đúng tức thì.

**Gói dịch vụ (chỉ Sinh viên):**
- Student → **Gói dịch vụ** → xem Free / Pro / Max → nâng cấp cho chính mình.
- Admin → trang **Người dùng** → đổi gói cho tài khoản **sinh viên** (giảng viên/admin hiển thị *Không áp dụng*).
- Giảng viên & Admin **không thấy** trang Gói dịch vụ và không bị giới hạn câu hỏi theo gói.

---

## Đánh giá (Test set 50 câu)

Sau khi đã index tài liệu textbook:

```bash
cd backend
python -m tests.evaluate --course-id 1
# Tuỳ chọn:
# --limit 10      chỉ chạy 10 câu đầu
# --delay 2       nghỉ 2s giữa mỗi câu (tránh rate-limit)
```

- Test set: [backend/tests/test_set.json](backend/tests/test_set.json) — 50 câu hỏi + ground truth.
- Dùng LLM-as-judge so với ground truth, in accuracy, lưu `tests/eval_result.json`.

---

## Cấu trúc thư mục

```
swd/
├── README.md
├── CLAUDE.md                    # Spec đầy đủ + hướng dẫn cho Claude Code
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, mount routers
│   │   ├── config.py            # Settings từ .env
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── shared/              # dependencies, exceptions
│   │   └── modules/
│   │       ├── auth/            # Đăng nhập, JWT
│   │       ├── users/           # Quản lý user, role, plan
│   │       ├── courses/         # Môn học, chương
│   │       ├── documents/       # Upload, ingest, parsers
│   │       ├── chat/            # Chat RAG, sessions
│   │       ├── rag/             # Embedder, VectorStore, Retriever, Facade
│   │       ├── quizzes/         # Quiz, Question, QuizAttempt
│   │       └── subscriptions/   # Gói Free/Pro/Max
│   ├── seed.py                  # Seed 3 user + môn học + quiz mẫu
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       ├── test_set.json        # 50 câu hỏi + ground truth
│       └── evaluate.py          # Script đánh giá
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── ChatPage.tsx
    │   │   ├── DocumentsPage.tsx
    │   │   ├── QuizzesPage.tsx  # Tạo quiz (Lecturer) + làm bài (Student)
    │   │   ├── PricingPage.tsx  # Gói dịch vụ
    │   │   └── AdminPage.tsx
    │   ├── api/client.ts        # Axios + VITE_API_BASE (web & APK)
    │   └── auth/AuthContext.tsx
    ├── capacitor.config.ts      # Cấu hình Capacitor / Android
    ├── android/                 # Native Android project (Capacitor)
    ├── package.json
    └── vite.config.ts
```
