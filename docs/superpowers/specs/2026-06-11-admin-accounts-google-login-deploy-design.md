# Design: Tài khoản do Admin cấp + Google Sign-In + Email + Deploy Vercel/Render/Neon

**Ngày:** 2026-06-11
**Trạng thái:** Đã duyệt

## Mục tiêu

1. Bỏ đăng ký công khai — **chỉ Admin tạo tài khoản** Sinh viên (USER) và Giảng viên (LECTURER).
2. Hệ thống **gửi email** thông tin đăng nhập (email + mật khẩu tự sinh) cho người được cấp tài khoản.
3. Thêm **đăng nhập bằng Google** — chỉ email đã được Admin cấp tài khoản mới đăng nhập được.
4. **Deploy free hoàn toàn**: frontend lên Vercel, backend lên Render free, dữ liệu (metadata + vector) lên Neon Postgres free (pgvector) để không mất dữ liệu khi Render spin-down.

## Quyết định đã chốt

| Câu hỏi | Quyết định |
|---|---|
| Email lạ đăng nhập Google | **Từ chối (403)** — "Tài khoản chưa được cấp, liên hệ Admin" |
| Nội dung email cấp tài khoản | Email + **mật khẩu tự sinh**; người dùng login bằng mật khẩu hoặc Google |
| Hosting backend | **Render free** (frontend Vercel) |
| Dịch vụ gửi mail | **Gmail SMTP** (App Password) |
| Persistence trên Render free | **Neon Postgres free**: metadata qua `DATABASE_URL`, vector qua **pgvector** |

## Phần 1 — Chỉ Admin tạo tài khoản

### Backend
- **Xóa** `POST /api/auth/register` (router + `AuthService.register` + `RegisterRequest`).
- **Thêm** `POST /api/users` — guard `require_role(Role.ADMIN)`:
  - Body (Pydantic): `{ email: EmailStr, full_name: str, role: LECTURER | USER }` (không cho tạo ADMIN qua API).
  - Service (`users/service.py`): kiểm tra email trùng (400), sinh mật khẩu `secrets.token_urlsafe` ~12 ký tự, hash bcrypt, tạo user, gửi mail đồng bộ (xem Phần 3 — cần biết kết quả gửi để quyết định trả `temp_password`).
  - Response: `UserOut` + `email_sent: bool` + `temp_password: str | None` (chỉ trả khi gửi mail thất bại/SMTP chưa cấu hình, để Admin gửi tay).
- **Seed Admin** khi startup (`main.py` lifespan): nếu DB chưa có user role ADMIN, tạo từ env `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_FULL_NAME` (mặc định hợp lý). Bắt buộc vì không còn đường tự đăng ký.
- Không log mật khẩu (quy tắc 8, CLAUDE.md).

### Frontend
- `LoginPage.tsx`: bỏ mode `register`, bỏ field họ tên/role; thêm nút Google (Phần 2).
- `AuthContext.tsx`: bỏ hàm `register`, thêm `loginWithGoogle(idToken)`.
- `AdminPage.tsx`: thêm form "Tạo tài khoản" (email, họ tên, role LECTURER/USER); hiển thị thông báo "đã gửi email" hoặc mật khẩu tạm nếu gửi lỗi.
- `i18n/translations.ts`: thêm key mới (vi + en), dọn key đăng ký không dùng.

## Phần 2 — Đăng nhập Google

- **Frontend**: Google Identity Services (`https://accounts.google.com/gsi/client`), render nút chuẩn của Google trên LoginPage. Callback nhận `credential` (ID token JWT) → gọi `POST /api/auth/google`. Client ID đọc từ `VITE_GOOGLE_CLIENT_ID`; nếu thiếu env thì ẩn nút.
- **Backend**: `POST /api/auth/google` body `{ id_token: str }`:
  1. Verify bằng `google-auth` (`id_token.verify_oauth2_token`, audience = `GOOGLE_OAUTH_CLIENT_ID`). Token sai/hết hạn → 401.
  2. Lấy `email` từ payload → tìm user. Không có → **403** "Tài khoản chưa được cấp. Vui lòng liên hệ Admin."
  3. Có → cấp JWT app (`_token_for`) như login thường.
- Env mới: `GOOGLE_OAUTH_CLIENT_ID` (backend), `VITE_GOOGLE_CLIENT_ID` (frontend) — cùng một giá trị.
- README ghi hướng dẫn tạo OAuth Client ID trên Google Cloud Console (Authorized JavaScript origins: `http://localhost:5173` + domain Vercel).

## Phần 3 — Gửi email (Gmail SMTP)

- Module mới `app/shared/mailer.py`:
  - `send_account_email(to, full_name, password, login_url) -> bool` — `smtplib.SMTP_SSL("smtp.gmail.com", 465)`.
  - Env: `SMTP_USER`, `SMTP_PASSWORD` (Gmail App Password), `MAIL_FROM` (mặc định = SMTP_USER), `APP_LOGIN_URL`.
  - SMTP chưa cấu hình → return False ngay (không crash); lỗi gửi → log warning (không log mật khẩu), return False.
- Gọi từ `users/service.py`. Vì cần biết kết quả để trả `temp_password`, gửi **đồng bộ trong threadpool** (endpoint sync chạy threadpool sẵn của FastAPI) — chấp nhận ~1-2s cho thao tác Admin ít dùng.
- Template tiếng Việt: chào theo tên, email đăng nhập, mật khẩu tạm, link app, ghi chú "có thể đăng nhập bằng Google với email này".

## Phần 4 — Persistence: Neon Postgres + pgvector

- **Metadata**: Neon free → `DATABASE_URL=postgresql+psycopg2://...`. `database.py` đã hỗ trợ URL ngoài SQLite (nhánh `pool_pre_ping`). Thêm `psycopg2-binary` vào requirements. Lightweight migrations chỉ chạy cho SQLite (giữ nguyên); Postgres tạo mới đủ cột qua `create_all`.
- **Vector**: implementation mới `PgVectorStore` cùng interface 3 method (`add`, `query`, `delete_document`) trong `rag/vector_store.py`:
  - Bảng `rag_chunks(id text pk, document_id int, course_id int, chapter text, chunk_index int, page int, text text, embedding vector(N))` — tạo qua `CREATE EXTENSION IF NOT EXISTS vector` + DDL khi khởi tạo.
  - `query`: cosine distance (`embedding <=> :vec`) + filter `course_id`, ORDER BY LIMIT k. Tách theo `embed_provider` (số chiều khác nhau) như Chroma hiện tại — tên bảng theo provider.
  - Chọn implementation qua env `VECTOR_BACKEND=chroma|pgvector` (mặc định `chroma` để dev local không đổi gì). Factory trả đúng class — caller (`embedder`/`retriever`/`documents`) không đổi.
- Local dev giữ nguyên SQLite + Chroma; production dùng Neon cho cả hai.

## Phần 5 — Deploy

- **Vercel (frontend)**: root directory `frontend/`, build `npm run build`, output `dist/`; `vercel.json` rewrite SPA về `index.html`. Env: `VITE_API_BASE=https://<app>.onrender.com/api`, `VITE_GOOGLE_CLIENT_ID`.
- **Render (backend)**: `render.yaml` — web service Python free, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, rootDir `backend/`. Env: `DATABASE_URL` (Neon), `VECTOR_BACKEND=pgvector`, `GOOGLE_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `SMTP_*`, `ADMIN_*`, `JWT_SECRET`, `CORS_ORIGINS` (+domain Vercel).
- README: mục "Deploy" từng bước (tạo Neon, Render, Vercel, Google OAuth Client, Gmail App Password).

## Ngoài phạm vi (YAGNI)

- Đổi/reset mật khẩu tự phục vụ, buộc đổi mật khẩu lần đầu, refresh token.
- Xác thực email, link kích hoạt.
- Hàng đợi email; retry gửi mail.
- Di trú dữ liệu SQLite cũ sang Neon.

## Kiểm thử

- Backend: pytest cho `POST /api/users` (admin ok / non-admin 403 / email trùng 400 / temp_password khi SMTP tắt), `POST /api/auth/google` (token hợp lệ + user tồn tại → JWT; user lạ → 403; token sai → 401 — mock verify), seed admin idempotent, register cũ trả 404/405.
- Mailer test bằng mock SMTP. PgVectorStore test khi có Postgres (skip nếu không có).
- Manual: build frontend, login Google end-to-end sau khi cấu hình Client ID.
