# REQUIREMENTS.md — Đặc tả yêu cầu hệ thống (SRS)

**Dự án:** Maple — Course Document RAG Chatbot
**Phiên bản:** 2.2 (cập nhật 26/06/2026 — **bỏ gói dịch vụ/subscription**, Admin chỉ quản lý người dùng; trước đó 2.1: tách Role thành entity riêng (bảng `roles`), email báo Admin; 2.0: Phòng học, Yêu cầu tài khoản, chat chỉ Sinh viên)
**Tài liệu liên quan:** [README.md](../README.md) · [DESIGN.md](DESIGN.md) · [diagram.md](diagram.md) · [schema.sql](schema.sql) · [CLAUDE.md](../CLAUDE.md)

---

## 1. Giới thiệu

### 1.1. Mục đích
Web app chatbot hỏi đáp dựa trên tài liệu môn học (RAG — Retrieval Augmented Generation).
Giảng viên upload tài liệu bài giảng (PDF, DOCX, slide); hệ thống tự động chunk + embed;
sinh viên đặt câu hỏi và nhận câu trả lời **chỉ trong phạm vi tài liệu**, kèm trích dẫn nguồn.
Hệ thống bổ sung quiz trắc nghiệm theo môn và phòng học để giảng viên giao bài cho sinh viên.

### 1.2. Phạm vi
- **Trong phạm vi:** quản lý tài liệu + RAG pipeline, chat hỏi đáp có trích dẫn, quản lý
  môn học/chương, quiz + bảng điểm, phòng học, cấp tài khoản (Admin tạo / duyệt yêu cầu),
  phân quyền 3 actor, web + app Android (một codebase), bộ test 50 câu đánh giá.
- **Ngoài phạm vi:** chỉnh sửa tài liệu trực tuyến,
  thông báo real-time (websocket), làm quiz có giới hạn thời gian, LMS đầy đủ.

### 1.3. Thuật ngữ
| Thuật ngữ | Nghĩa |
|-----------|-------|
| RAG | Retrieval Augmented Generation — truy xuất ngữ cảnh từ vector store rồi sinh câu trả lời |
| Chunk | Đoạn văn bản (~800 token, overlap ~100) được embed thành vector |
| Citation | Trích dẫn nguồn (đoạn gốc, tên tài liệu, trang) kèm mỗi câu trả lời AI |
| Attempt | Một lượt làm quiz của sinh viên (điểm + đáp án đã chọn) |
| Room | Phòng học — không gian Lecturer mời sinh viên vào để giao quiz + tài liệu của một môn |

### 1.4. Yêu cầu gốc (đề bài tối thiểu)
Tài liệu môn học là các chapters trong textbook trên FLM: *Software Modeling and Design:
UML, Use Cases, Patterns, and Software Architectures*.

1. **Quản lý tài liệu:** upload PDF/DOCX/slide; tự động chunk & embed; quản lý theo môn
   học/chương (demo 1 môn); xem danh sách tài liệu đã index.
2. **Chat & Hỏi đáp:** chat tự nhiên theo ngữ cảnh hội thoại; trích dẫn nguồn tài liệu gốc;
   giới hạn trả lời trong phạm vi tài liệu; lịch sử hội thoại theo phiên.
3. **Deliverables:** web app chatbot; source code trên GitHub (có README); test set
   50 câu hỏi + ground truth.

Các mục từ §3 trở đi là yêu cầu **mở rộng** đã được chốt và hiện thực trong quá trình phát triển.

---

## 2. Mô tả tổng quan

### 2.1. Actors & phân quyền

| Actor | Vai trò | Quyền chính |
|-------|---------|-------------|
| **Guest** (chưa đăng nhập) | Khách | Đăng nhập; gửi **Yêu cầu tài khoản** |
| **User / Student** (Sinh viên) | Người dùng cuối | **Duy nhất actor cần AI chat**; xem tài liệu đã index; tham gia phòng học được mời; làm quiz & xem điểm ngay; quản lý phiên chat của mình |
| **Lecturer** (Giảng viên) | Phụ trách nội dung môn | Upload/xóa tài liệu môn mình; tạo & quản lý môn học/chương; tạo quiz + xem bảng điểm SV; tạo phòng học & mời SV. **Không dùng AI chat**, không quản lý người dùng |
| **Admin** | Quản trị | **Chỉ quản lý người dùng** (CRUD người dùng/role) + duyệt yêu cầu tài khoản. Giao diện không có chat/quiz/phòng/tài liệu (backend vẫn giữ quyền giám sát nhưng UI ẩn). Cấu hình hệ thống qua env |

Phân quyền thực thi server-side qua JWT + dependency `require_role(...)`.

### 2.2. Ràng buộc thiết kế & công nghệ
- Kiến trúc **Modular Monolith** — một process FastAPI, module ranh giới rõ (router → service → repository).
- Frontend **React** (Vite + TypeScript + Tailwind); cùng codebase build ra **app Android** qua Capacitor.
- LLM: **Google Gemini 2.5 Flash**; Embedding: **gemini-embedding-001**; hỗ trợ mode `local` không cần API key (demo offline).
- Vector store: **ChromaDB** (local) hoặc **pgvector** (production Neon); Metadata: **SQLite** (hoặc SQL Server / Postgres qua `DATABASE_URL`).
- Đơn giản, chỉ đáp ứng đủ yêu cầu; giao diện đẹp, bắt mắt; song ngữ VI/EN.

### 2.3. Giả định & phụ thuộc
- Không còn đăng ký công khai — tài khoản do Admin cấp hoặc duyệt từ form yêu cầu; Admin đầu tiên seed từ env.
- Gửi email cần Brevo API key (production) hoặc Gmail SMTP (local); thiếu cấu hình thì hệ thống vẫn chạy, mật khẩu tạm trả về cho Admin gửi tay.
- Đăng nhập Google yêu cầu `GOOGLE_OAUTH_CLIENT_ID`; email Google phải trùng tài khoản đã được cấp.

---

## 3. Yêu cầu chức năng (Functional Requirements)

> Quy ước: mỗi FR có mã, mô tả, quyền, và tiêu chí chấp nhận chính. Tất cả FR dưới đây
> **đã được hiện thực** và phủ bởi smoke test (`backend/tests/smoke_all.py`, 56 checks).

### 3.1. Xác thực — FR-AUTH

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-AUTH-01 | Đăng nhập bằng email + mật khẩu → JWT (hạn cấu hình qua `JWT_EXPIRE_MINUTES`). Sai thông tin → 401 | Public |
| FR-AUTH-02 | Đăng nhập bằng Google (idToken) — email phải trùng tài khoản đã tồn tại | Public |
| FR-AUTH-03 | Mọi endpoint (trừ Public) yêu cầu JWT hợp lệ; token sai/hết hạn → 401 | — |
| FR-AUTH-04 | Không có đăng ký công khai; tài khoản chỉ sinh ra từ FR-ADM-02 hoặc FR-REQ-03 | — |

### 3.2. Yêu cầu tài khoản — FR-REQ

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-REQ-01 | Form public ở trang đăng nhập: họ tên + email + vai trò mong muốn (USER/LECTURER) + lời nhắn → lưu `AccountRequest` trạng thái PENDING; gửi email báo Admin (`ADMIN_EMAIL`, best-effort). Không xin được role ADMIN (422) | Guest |
| FR-REQ-02 | Chống spam: tối đa **5 yêu cầu/giờ/IP** (429); chặn email đã có tài khoản (400); chặn email đã có yêu cầu PENDING (400) | — |
| FR-REQ-03 | Admin xem danh sách yêu cầu (lọc theo trạng thái); **Duyệt** → tạo tài khoản qua flow FR-ADM-02 (mật khẩu tự sinh + email) → APPROVED; **Từ chối** → REJECTED. Yêu cầu đã xử lý không xử lý lại (400) | Admin |
| FR-REQ-04 | Người được duyệt đăng nhập được ngay bằng mật khẩu trong email (hoặc Google cùng email) | — |

### 3.3. Quản lý người dùng — FR-ADM

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-ADM-01 | Xem danh sách người dùng | Admin |
| FR-ADM-02 | Tạo tài khoản Sinh viên/Giảng viên: mật khẩu tự sinh, gửi qua email (Brevo/SMTP); email lỗi → trả `temp_password` để gửi tay; không tạo được ADMIN qua API | Admin |
| FR-ADM-03 | Đổi role người dùng (ADMIN/LECTURER/USER) | Admin |
| FR-ADM-05 | Xóa người dùng: dọn dữ liệu cá nhân (phiên chat, messages, attempts, membership phòng); nội dung dùng chung (môn, tài liệu, quiz, phòng đã tạo) giữ lại và gỡ liên kết owner; không tự xóa chính mình (400) | Admin |
| FR-ADM-06 | Cấu hình hệ thống qua env (model, API key, DB, CORS, admin seed…) — không hardcode secret | Admin |

### 3.4. Môn học / Chương — FR-CRS

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-CRS-01 | Tạo môn học (tên + mô tả, owner = người tạo) | Lecturer, Admin |
| FR-CRS-02 | Xem danh sách môn, danh sách chương của môn | Mọi người đã đăng nhập |
| FR-CRS-03 | Xóa môn: cascade xóa tài liệu (kèm vector), quiz (kèm câu hỏi + attempts), phòng học (kèm thành viên); phiên chat gắn môn được gỡ liên kết. Lecturer chỉ xóa môn mình; Admin xóa mọi môn | Lecturer (của mình), Admin |

### 3.5. Quản lý tài liệu & RAG ingest — FR-DOC

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-DOC-01 | Upload tài liệu gắn môn (tùy chọn chương) → pipeline: parse → chunk (~800 token, overlap ~100) → embed → lưu ChromaDB kèm metadata `{document_id, course_id, chapter, chunk_index, source_text, page}` | Lecturer, Admin |
| FR-DOC-02 | Chỉ chấp nhận `.pdf` `.docx` `.pptx` — validate **cả MIME type lẫn extension** server-side; sai → 400 với thông báo rõ | — |
| FR-DOC-03 | Trạng thái index hiển thị được: PROCESSING → INDEXED / FAILED (kèm lý do lỗi) | Mọi người xem |
| FR-DOC-04 | Xem danh sách tài liệu đã index (lọc theo môn) | Mọi người đã đăng nhập |
| FR-DOC-05 | Xóa tài liệu: xóa **cả vector trong ChromaDB lẫn metadata SQLite** | Lecturer (của mình), Admin |

### 3.6. Chat & Hỏi đáp RAG — FR-CHAT

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-CHAT-01 | Chat hỏi đáp theo ngữ cảnh hội thoại: embed câu hỏi → similarity search top-k=4 (filter theo môn nếu chọn) → prompt (system + context + history + câu hỏi) → Gemini → câu trả lời | **USER, ADMIN** |
| FR-CHAT-02 | **Giảng viên không dùng AI chat** → `POST /api/chat` và `POST /api/sessions` trả 403; UI ẩn mục Hỏi đáp + lịch sử với Lecturer, trang chủ Lecturer chuyển về Phòng học | — |
| FR-CHAT-03 | **Citations bắt buộc** kèm mỗi câu trả lời: đoạn nguồn, tên tài liệu, trang, độ liên quan. Không trả lời ngoài phạm vi context — không có thì nói "không tìm thấy trong tài liệu" | — |
| FR-CHAT-04 | Phiên chat: tạo / xem danh sách của mình / xem lịch sử / đổi tên / ghim / xóa. Chủ phiên hoặc Admin mới xem được; người khác → 403 | Owner, Admin |
| FR-CHAT-05 | Admin giám sát: xem toàn bộ phiên chat của mọi người dùng | Admin |
| FR-CHAT-06 | Lịch sử chat lưu DB (messages kèm citations_json), hiển thị lại khi mở phiên | — |

### 3.7. Quiz trắc nghiệm — FR-QZ

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-QZ-01 | Tạo quiz gắn **từng môn học**: tiêu đề + 1–50 câu hỏi, mỗi câu 2–6 lựa chọn, đúng 1 đáp án; validate `correct_index` trong khoảng | Lecturer, Admin |
| FR-QZ-02 | Sinh viên mở đề: response **ẩn `correct_index`** (chống lộ đáp án) | Mọi người đã đăng nhập |
| FR-QZ-03 | Nộp bài → backend chấm: `score = đúng/tổng × 100`, trả điểm + đúng/sai + đáp án đúng từng câu **ngay lập tức** | Mọi người đã đăng nhập |
| FR-QZ-04 | **Chỉ lượt làm của Sinh viên được lưu** vào bảng điểm (QuizAttempt); Lecturer/Admin "xem thử" không ghi — bảng kết quả lớp không bị nhiễu | — |
| FR-QZ-05 | Bảng điểm (attempts) **kèm họ tên + email sinh viên** + thời gian — cơ chế "điểm tự gửi về giảng viên". Chỉ **người tạo quiz** hoặc Admin xem được; người khác → 403 | Người tạo, Admin |
| FR-QZ-06 | Xóa quiz (kèm câu hỏi + attempts) | Người tạo, Admin |

### 3.8. Phòng học — FR-ROOM

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-ROOM-01 | **Chỉ Admin/Lecturer** tạo phòng học, bắt buộc gắn một môn học tồn tại; Sinh viên tạo → 403 | Lecturer, Admin |
| FR-ROOM-02 | Danh sách phòng theo vai trò: Admin thấy **mọi** phòng; Lecturer thấy phòng **mình tạo**; Sinh viên chỉ thấy phòng **được mời** | Mọi người đã đăng nhập |
| FR-ROOM-03 | Chi tiết phòng tổng hợp: thành viên + **quiz của môn** + **tài liệu (slide/doc) của môn** — sinh viên học và làm quiz ngay trong phòng. Người ngoài phòng → 403 | Thành viên, người tạo, Admin |
| FR-ROOM-04 | Mời sinh viên qua **email**: chỉ tài khoản role USER (mời GV/Admin → 400), không mời trùng (400); có endpoint danh sách sinh viên để chọn nhanh | Người tạo, Admin |
| FR-ROOM-05 | Gỡ thành viên khỏi phòng; xóa phòng (thành viên xóa cascade) | Người tạo, Admin |

### 3.9. Giới hạn chat (Rate-limit) — FR-RL

| Mã | Yêu cầu | Quyền |
|----|---------|-------|
| FR-RL-01 | Rate-limit chat **mức cố định, chỉ áp dụng Sinh viên**: ~30 câu/phút mỗi SV (vượt → 429). Giảng viên & Admin không bị giới hạn (không dùng AI chat trong UI) | — |

### 3.10. Giao diện & đa nền tảng — FR-UI

| Mã | Yêu cầu |
|----|---------|
| FR-UI-01 | Giao diện đẹp, bắt mắt (yêu cầu rõ của đề); theme sáng/tối; responsive (sidebar drawer trên mobile) |
| FR-UI-02 | Song ngữ **VI/EN**, chuyển đổi ngay trong sidebar |
| FR-UI-03 | Điều hướng theo role: **Admin chỉ thấy mục Người dùng** (tab Người dùng + Yêu cầu chờ duyệt), không có chat/quiz/phòng/tài liệu; Lecturer không thấy Hỏi đáp; Sinh viên không thấy Tài liệu/Người dùng |
| FR-UI-04 | Cùng codebase build ra **website** (Vite) và **app Android** (Capacitor APK); API base cấu hình qua `VITE_API_BASE` |

---

## 4. Yêu cầu phi chức năng (Non-Functional Requirements)

| Mã | Nhóm | Yêu cầu |
|----|------|---------|
| NFR-01 | Bảo mật | Mật khẩu hash **bcrypt**; không lưu/log plaintext, API key, token. JWT hạn ngắn cấu hình được |
| NFR-02 | Bảo mật | Phân quyền **server-side** trên mọi endpoint (auth middleware + role guard + Pydantic validation + HTTP status phù hợp) — không tin client |
| NFR-03 | Bảo mật | Upload validate MIME + extension; không expose stack trace trong response production |
| NFR-04 | Chống lạm dụng | Rate-limit: chat mức cố định cho SV (FR-RL-01, ~30 câu/phút); form yêu cầu tài khoản 5/giờ/IP (FR-REQ-02) |
| NFR-05 | Độ tin cậy | Gọi Gemini có giới hạn retry — không retry vô hạn gây treo; lỗi ingest ghi vào `Document.error`, không crash app |
| NFR-06 | Toàn vẹn dữ liệu | Xóa user/course/quiz/room phải dọn đúng thứ tự FK (con trước cha), không để orphan/vỡ ràng buộc; xóa tài liệu phải xóa cả vector |
| NFR-07 | Tính đúng RAG | System prompt bắt buộc: chỉ trả lời từ context, không bịa, luôn dẫn nguồn |
| NFR-08 | Khả chuyển | Đổi DB chỉ bằng `DATABASE_URL` (SQLite / SQL Server / Postgres+pgvector); mode `local` chạy không cần API key |
| NFR-09 | Hiệu năng | Lịch sử chat trả theo phiên (không dump toàn bộ); top-k=4 chunk mỗi câu hỏi; phù hợp lớp học demo (~vài chục người dùng đồng thời trên free tier) |
| NFR-10 | Khả kiểm thử | Smoke test tự động toàn hệ thống không cần API key/email thật (DB tạm); script đánh giá RAG bằng LLM-as-judge |
| NFR-11 | Chuẩn code | Backend: black/isort/ruff, type hints, Pydantic v2, async IO. Frontend: TS strict, function components + hooks |

---

## 5. Yêu cầu dữ liệu

Mô hình đầy đủ (thuộc tính, quan hệ, quy tắc xóa) xem [diagram.md §2–3](diagram.md) và [schema.sql](schema.sql). Tóm tắt thực thể:

- **Role** (entity riêng — bảng `roles`: code ADMIN/LECTURER/USER + name + description; seed cố định id 1/2/3) — User & AccountRequest tham chiếu qua khóa ngoại `role_id` / `requested_role_id`
- **User** (role_id → Role) · **AccountRequest** (requested_role_id → Role, PENDING/APPROVED/REJECTED)
- **Course** → Chapter, Document, Quiz, Room
- **Document** (PROCESSING/INDEXED/FAILED) — vector + chunk text nằm ở ChromaDB/pgvector, không lặp trong SQL
- **ChatSession** → Message (citations_json)
- **Quiz** → Question (ẩn correct_index khi trả đề) → QuizAttempt (chỉ SV)
- **Room** → RoomMember (unique room_id + user_id)

---

## 6. Deliverables & tiêu chí nghiệm thu

| # | Sản phẩm | Tiêu chí nghiệm thu |
|---|----------|---------------------|
| 1 | Web app chatbot | Chạy được local (`uvicorn` + `npm run dev`) và production (Vercel + Render + Neon); đủ các FR §3 |
| 2 | App Android | `npm run cap:apk` build được APK debug, gọi API qua LAN/emulator |
| 3 | Source code GitHub | Repo có README hướng dẫn cài đặt/chạy/deploy đầy đủ; commit lịch sử rõ ràng |
| 4 | Test set 50 câu + ground truth | `backend/tests/test_set.json`; chạy `python -m tests.evaluate --course-id 1` ra accuracy (LLM-as-judge), lưu `eval_result.json` |
| 5 | Kiểm thử chức năng | `python -m tests.smoke_all` **51/51 PASS** (auth, yêu cầu tài khoản, users, môn, tài liệu, chat, quiz, phòng học, xóa an toàn); `python -m tests.smoke_rooms` 16/16 PASS; `pytest` 24/24 PASS |
| 6 | Tài liệu thiết kế | UML/Use Case/Patterns/Architecture: [DESIGN.md](DESIGN.md), [diagram.md](diagram.md), diagram Mermaid trong [README.md](../README.md) |

---

## 7. Ma trận truy vết (FR → Endpoint → Kiểm thử)

| FR | Endpoint chính | Phủ bởi |
|----|----------------|---------|
| FR-AUTH-01/02 | `POST /api/auth/login`, `/api/auth/google` | smoke_all [Health + Auth] |
| FR-REQ-01..04 | `POST/GET /api/account-requests`, `/{id}/approve`, `/{id}/reject` | smoke_all [Yêu cầu tài khoản] |
| FR-ADM-01..05 | `GET/POST /api/users`, `PATCH /{id}/role`, `DELETE /{id}` | smoke_all [Quản lý người dùng], [Xóa dữ liệu an toàn] |
| FR-CRS-01..03 | `GET/POST /api/courses`, `/{id}/chapters`, `DELETE /{id}` | smoke_all [Môn học], [Xóa dữ liệu an toàn] |
| FR-DOC-01..05 | `POST/GET /api/documents`, `DELETE /{id}` | smoke_all [Tài liệu]; evaluate.py (ingest thật) |
| FR-CHAT-01..06 | `POST /api/chat`, `POST/GET/PATCH/DELETE /api/sessions*` | smoke_all [Chat] |
| FR-QZ-01..06 | `POST/GET /api/quizzes*`, `/{id}/submit`, `/{id}/attempts` | smoke_all [Quiz] |
| FR-ROOM-01..05 | `POST/GET/DELETE /api/rooms*`, `/students`, `/{id}/members*` | smoke_all [Phòng học]; smoke_rooms |
| FR-RL-01 | `POST /api/chat` (giới hạn cố định cho SV) | rate_limit.py (STUDENT_CHAT_PER_MIN) |
| FR-UI-01..04 | — (frontend) | `npm run build` (TS strict) + kiểm tra tay theo role |
