# Design — Yêu cầu tài khoản (FR-REQ): form public + Admin duyệt

Ngày: 2026-06-12. Người dùng chọn phương án "Form Yêu cầu tài khoản + Admin duyệt
trong app" (phương án 2 trong các gợi ý kênh liên hệ Admin).

## Lý do chọn

Hệ thống đã có sẵn flow `UserService.create_account` (mật khẩu tự sinh + email
"tài khoản được duyệt" qua Brevo/SMTP) — chỉ thiếu đầu vào tự phục vụ. Phương án
này khép kín vòng: **xin → duyệt → nhận mật khẩu qua email**, có lịch sử, không
phải gõ lại thông tin. Các phương án khác (mailto, form gửi mail trực tiếp,
Google Form) đều xử lý tay và không có trạng thái.

## Backend — module `modules/account_requests/`

- `models.py`: `AccountRequest(id, email idx, full_name, requested_role[LECTURER|USER],
  message, status[PENDING|APPROVED|REJECTED], created_at, decided_at?)`.
- Endpoints:
  - `POST /api/account-requests` — **public**, rate-limit 5/giờ/IP
    (`IPRateLimiter` mới trong `shared/rate_limit.py`). Chặn: email đã có tài
    khoản (400), email đã có yêu cầu PENDING (400), role ADMIN (422).
  - `GET /api/account-requests?status=` — Admin.
  - `POST /api/account-requests/{id}/approve` — Admin; tái dùng
    `UserService.create_account` → APPROVED; trả `{request, email_sent,
    temp_password?}` (temp_password chỉ khi email thất bại, để Admin gửi tay).
  - `POST /api/account-requests/{id}/reject` — Admin → REJECTED.
  - Yêu cầu đã xử lý → approve/reject lại trả 400.
- Bảng mới tự tạo qua `create_all` (SQLite & Postgres), không cần migration tay.

## Frontend

- **LoginPage**: dòng "Chưa có tài khoản?" + nút **Yêu cầu tài khoản** → modal
  (họ tên, email, vai trò SV/GV, lời nhắn) → thông báo thành công nêu rõ
  "mật khẩu sẽ gửi tới email khi được duyệt".
- **AdminPage**: 2 tab — **Người dùng** (như cũ) và **Yêu cầu chờ duyệt (n)**:
  mỗi yêu cầu hiện tên, email, vai trò xin, lời nhắn + nút **Duyệt** / **Từ chối**;
  notice tái dùng kiểu thông báo created/createdNoEmail.
- i18n VI/EN: nhóm khóa `req.*` và `admin.tab*/approve/reject/...`.

## Kiểm thử

`backend/tests/smoke_all.py` — smoke test TOÀN BỘ chức năng hệ thống (56 checks),
trong đó FR-REQ: gửi yêu cầu, chặn trùng/đã có tài khoản/role ADMIN, cần quyền
Admin để xem, duyệt → đăng nhập được bằng mật khẩu tạm, không duyệt lại được,
từ chối. Chạy: `python -m tests.smoke_all` (DB tạm, tắt email).
