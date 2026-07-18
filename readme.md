# Maple — Course Document RAG Chatbot

Web app chatbot hỏi đáp dựa trên tài liệu môn học (RAG). Người dùng upload tài liệu bài giảng (PDF/DOCX/Slide), hệ thống tự động chunk + embed, và trả lời câu hỏi **chỉ trong phạm vi tài liệu**, có trích dẫn nguồn. Cùng một codebase chạy được cả **website** lẫn **app Android cài đặt** (Capacitor).

Môn học demo: *Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures*.

> Tài liệu thiết kế đầy đủ: [CLAUDE.md](CLAUDE.md)

---

## Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **Chat & Hỏi đáp RAG** | **Chỉ Sinh viên** chat theo ngữ cảnh hội thoại, trích dẫn nguồn, giới hạn trong tài liệu đã index (Admin giữ quyền giám sát; Giảng viên không dùng AI chat) |
| **Quản lý tài liệu** | Upload PDF/DOCX/PPTX → tự động chunk & embed, xem trạng thái (PROCESSING / INDEXED / FAILED) |
| **Quiz trắc nghiệm** | Lecturer tạo quiz **gắn theo từng phòng học (lớp)**, có thể đặt **mật khẩu** + **hạn nộp**; student làm bài, nộp → chấm điểm tức thì, hiện đáp án đúng; **điểm tự gửi về Lecturer** (bảng kết quả kèm tên sinh viên) |
| **AI soạn quiz (Gemini)** | Lecturer nhờ **AI soạn nháp đề** từ tài liệu môn học (chọn số câu + chủ đề) → đề hiện ngay trong form để **duyệt & chỉnh sửa** trước khi lưu (không tự lưu) |
| **Bảng điểm & xem lại (Grade)** | Sinh viên có trang **Bảng điểm** gom mọi kết quả quiz **theo môn học**; bấm **Xem lại** từng lượt làm để soi đáp án đã chọn vs đáp án đúng |
| **Định dạng toán (LaTeX)** | Chat và đề/đáp án quiz render công thức toán bằng KaTeX (`$...$` inline, `$$...$$` block) |
| **Phòng học (Rooms)** | Chỉ Admin/Lecturer tạo phòng gắn với môn học, **mời sinh viên** vào; trong phòng có quiz + slide/tài liệu của môn để sinh viên học và làm bài |
| **Yêu cầu tài khoản** | Form public ở trang đăng nhập (họ tên, email, vai trò, lời nhắn) → Admin **duyệt** trong tab riêng → tài khoản tạo tự động + mật khẩu gửi qua email; chống spam theo IP; Admin nhận email báo khi có yêu cầu mới |
| **Phân quyền 3 actor** | Admin (**chỉ quản lý người dùng** + duyệt yêu cầu tài khoản), Lecturer (tài liệu + quiz + môn học + phòng học), User/Student (chat + phòng học + làm quiz) |
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

# (tuỳ chọn) nạp giáo trình chính (Gomaa) vào RAG để hỏi đáp chạy sẵn:
python -m scripts.seed_textbook   # idempotent, chạy offline (embed local)

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

# Bắt buộc đổi: chuỗi ngẫu nhiên dài (vd: python -c "import secrets; print(secrets.token_urlsafe(48))")
JWT_SECRET=<chuoi-ngau-nhien-dai-cua-ban>
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

**Bước 3 — Đặt `DATABASE_URL` trong `.env`** (thay `<user>`, `<password>`, `<INSTANCE>` bằng thông tin SQL Server của bạn — nên tạo login riêng thay vì dùng `sa`):

```env
DATABASE_URL=mssql+pyodbc://<user>:<password>@localhost\<INSTANCE>/maple?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes
```

- **Default instance** (không có tên): bỏ `\<INSTANCE>` → `...@localhost/maple?driver=...`
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

**Điện thoại thật cùng Wi-Fi:** thay `10.0.2.2` bằng IP LAN của máy chạy backend (xem bằng `ipconfig`, dạng `192.168.x.x`), và backend phải chạy với `--host 0.0.0.0`.

**Live-reload khi dev** (không cần rebuild APK): mở comment dòng `server.url` trong [frontend/capacitor.config.ts](frontend/capacitor.config.ts) trỏ về Vite dev server.

### Tài khoản demo (chỉ local)

Chạy `python seed.py` để tạo 3 tài khoản demo (Admin / Lecturer / Student) — **email và mật khẩu in ra console khi seed xong**. Bộ tài khoản này chỉ dành cho chạy thử trên máy local.

> ⚠️ **Không chạy `seed.py` trên production.** Script sẽ từ chối seed tài khoản demo khi `DATABASE_URL` không phải SQLite (cần cờ `--demo-users` để ép). Trên production, Admin đầu tiên tạo từ env `ADMIN_EMAIL` / `ADMIN_PASSWORD` (đặt mật khẩu mạnh, đổi sau lần đăng nhập đầu).

> Chat AI **chỉ dành cho Sinh viên** (giới hạn cố định ~30 câu/phút mỗi SV để tránh lạm dụng). Giảng viên không dùng AI chat; Admin chỉ quản lý người dùng.

> **Lưu ý:** Không còn đăng ký công khai. Tài khoản Sinh viên/Giảng viên có 2 đường cấp: (1) **Admin tạo trực tiếp** trong trang Quản lý người dùng, hoặc (2) người dùng tự bấm **"Yêu cầu tài khoản"** ở trang đăng nhập → Admin **duyệt** trong tab "Yêu cầu chờ duyệt". Cả hai đường đều tự sinh mật khẩu và gửi qua email; người dùng cũng có thể **đăng nhập bằng Google** với email đã được cấp.

---

## Deploy free: Vercel + Render + Neon

### 1. Neon (Postgres + pgvector — dữ liệu bền vững)
1. Tạo project free tại https://neon.tech → copy connection string.
2. Đổi prefix `postgresql://` thành `postgresql+psycopg2://` khi dùng làm `DATABASE_URL`.
   (pgvector được bật tự động bởi app: `CREATE EXTENSION IF NOT EXISTS vector`.)

> ⚠️ **Neon DB đã có dữ liệu cũ?** Auto-migration của app chỉ chạy cho SQLite. Với
> Postgres đã tồn tại bảng `users` từ trước (còn cột `role`/`plan`), chạy một lần
> script [docs/migrations/2026-06-26-role-entity-drop-plan.sql](docs/migrations/2026-06-26-role-entity-drop-plan.sql)
> trong Neon SQL Editor để tách bảng `roles` + bỏ cột `plan`. **DB Neon mới tinh thì
> không cần** — app tự dựng đúng lược đồ khi khởi động.

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

| Tạo quiz (Lecturer) | Quản lý người dùng (Admin) |
|---|---|
| ![Tạo quiz](docs/screenshots/web/07-quiz-create-modal.png) | ![Admin](docs/screenshots/web/06-admin-users.png) |

**Android** (Capacitor — cùng codebase)

| Đăng nhập | Hỏi đáp | Quiz | Menu Giảng viên |
|---|---|---|---|
| ![Login](docs/screenshots/mobile/01-launch.png) | ![Chat](docs/screenshots/mobile/04-chat.png) | ![Quiz](docs/screenshots/mobile/05-quizzes.png) | ![Lecturer](docs/screenshots/mobile/06-lecturer-nav.png) |

---

## Quy trình sử dụng

**Xin cấp tài khoản (người chưa có tài khoản):**
1. Trang đăng nhập → bấm **Yêu cầu tài khoản** → điền họ tên, email, vai trò (SV/GV), lời nhắn → gửi.
2. Admin → trang **Người dùng** → tab **Yêu cầu chờ duyệt** → bấm **Duyệt** (tài khoản tạo tự động, mật khẩu gửi về email người xin) hoặc **Từ chối**.
3. Người xin nhận email mật khẩu → đăng nhập (hoặc dùng "Đăng nhập bằng Google" với chính email đó).

**Hỏi đáp RAG (chỉ Sinh viên):**
1. Đăng nhập Lecturer → vào **Tài liệu** → upload PDF/DOCX/PPTX. Đợi trạng thái *Đã index*.
2. Đăng nhập Student → vào **Hỏi đáp** → chọn môn → đặt câu hỏi → nhận câu trả lời kèm trích dẫn.

> Giảng viên **không có** mục Hỏi đáp — AI chat là tính năng dành cho sinh viên
> (backend trả 403 nếu Lecturer gọi `/api/chat`). Admin chỉ quản lý người dùng nên cũng không có mục Hỏi đáp.

**Phòng học (Rooms):**
1. Lecturer → **Phòng học** → **Tạo phòng** → đặt tên + chọn môn học.
2. Mở phòng → **Mời sinh viên** (nhập email hoặc chọn nhanh từ danh sách).
3. Student → **Phòng học** → thấy phòng mình được mời → vào phòng là có **quiz của môn để làm** và **slide/tài liệu để học**.

**Quiz (gắn theo môn học):**
1. Lecturer → **Quiz** → **Tạo quiz** → chọn môn + điền câu hỏi + đáp án → lưu.
2. Student → **Quiz** (hoặc trong **Phòng học**) → **Làm bài** → chọn đáp án → **Nộp bài** → xem điểm + đáp án đúng tức thì.
3. Lecturer → nút **Kết quả** trên quiz → xem bảng điểm từng sinh viên (tên, email, điểm, thời gian) — chỉ người tạo quiz hoặc Admin xem được; lượt "xem thử" của giảng viên không bị ghi vào bảng điểm.

**Quản trị người dùng (Admin):**
- Admin đăng nhập → vào thẳng trang **Người dùng** (menu chỉ có mục này) → tạo tài khoản, đổi role, xóa người dùng, và duyệt **Yêu cầu chờ duyệt**.
- Admin không có chat/quiz/phòng học/tài liệu trong giao diện.

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

**Smoke test chức năng** (không cần API key — dùng DB tạm, mode local):

```bash
cd backend
python -m tests.smoke_all     # toàn bộ chức năng: auth, yêu cầu tài khoản,
                              # users, môn học, tài liệu, chat, quiz, rooms
python -m tests.smoke_rooms   # riêng flow phòng học + quiz + chat student-only
```

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
│   │       ├── account_requests/ # Yêu cầu tài khoản (public) + Admin duyệt
│   │       ├── users/           # Quản lý user + bảng roles (role tách entity)
│   │       ├── courses/         # Môn học, chương
│   │       ├── documents/       # Upload, ingest, parsers
│   │       ├── chat/            # Chat RAG, sessions (chỉ Sinh viên)
│   │       ├── rag/             # Embedder, VectorStore, Retriever, Facade
│   │       ├── quizzes/         # Quiz, Question, QuizAttempt (bảng điểm cho Lecturer)
│   │       └── rooms/           # Phòng học: Room, RoomMember (Lecturer mời SV)
│   ├── seed.py                  # Seed 3 user + môn học + quiz mẫu
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       ├── test_set.json        # 50 câu hỏi + ground truth
│       ├── evaluate.py          # Script đánh giá RAG
│       ├── smoke_all.py         # Smoke test TOÀN BỘ chức năng qua API
│       └── smoke_rooms.py       # Smoke test riêng phòng học + quiz + chat
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── ChatPage.tsx     # Hỏi đáp RAG (Sinh viên; Lecturer bị ẩn)
    │   │   ├── DocumentsPage.tsx
    │   │   ├── RoomsPage.tsx    # Danh sách phòng học + tạo phòng
    │   │   ├── RoomDetailPage.tsx # Thành viên + quiz + tài liệu trong phòng
    │   │   ├── QuizzesPage.tsx  # Tạo quiz (Lecturer) + làm bài (Student) + bảng điểm
    │   │   └── AdminPage.tsx    # Quản lý người dùng + duyệt yêu cầu (chỉ Admin)
    │   ├── api/client.ts        # Axios + VITE_API_BASE (web & APK)
    │   └── auth/AuthContext.tsx
    ├── capacitor.config.ts      # Cấu hình Capacitor / Android
    ├── android/                 # Native Android project (Capacitor)
    ├── package.json
    └── vite.config.ts
```
