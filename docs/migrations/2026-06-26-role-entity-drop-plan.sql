-- =====================================================================
-- Migration một lần cho Postgres/Neon (production)
-- Ngày: 2026-06-26
-- Mục đích: đồng bộ DB production với code mới:
--   1) Tách Role thành bảng `roles`; users.role (enum) -> users.role_id (FK)
--      và account_requests.requested_role -> requested_role_id
--   2) Bỏ subscription: xóa cột users.plan
--
-- VÌ SAO CẦN CHẠY TAY: auto-migration trong app (_run_lightweight_migrations)
-- chỉ áp dụng cho SQLite (cú pháp PRAGMA). Với Neon Postgres ĐÃ CÓ DỮ LIỆU cũ,
-- create_all chỉ tạo bảng còn thiếu (roles) chứ KHÔNG ALTER bảng users hiện có.
--
-- KHÔNG cần chạy nếu Neon DB là MỚI TINH (chưa có bảng users) — khi đó
-- create_all + seed_roles của app tự dựng đúng lược đồ.
--
-- Cách chạy: dán toàn bộ vào Neon SQL Editor (hoặc psql) rồi Execute.
-- Script idempotent: chạy lại nhiều lần vẫn an toàn.
-- =====================================================================
BEGIN;

-- 1) Bảng roles + seed 3 vai trò cố định (id khớp ROLE_IDS trong code)
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT ''
);
INSERT INTO roles (id, code, name, description) VALUES
    (1, 'ADMIN',    'Quản trị viên', 'Toàn quyền quản lý người dùng + duyệt yêu cầu'),
    (2, 'LECTURER', 'Giảng viên',    'Tài liệu, môn học/chương, quiz, phòng học'),
    (3, 'USER',     'Sinh viên',     'Chat hỏi đáp RAG, làm quiz, tham gia phòng học')
ON CONFLICT (id) DO NOTHING;

-- 2) users: thêm role_id, backfill từ cột role cũ (nếu còn), bỏ role + plan
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INTEGER;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'role'
    ) THEN
        UPDATE users SET role_id = CASE role
            WHEN 'ADMIN' THEN 1 WHEN 'LECTURER' THEN 2 ELSE 3 END
        WHERE role_id IS NULL;
    END IF;
END $$;
UPDATE users SET role_id = 3 WHERE role_id IS NULL;
ALTER TABLE users ALTER COLUMN role_id SET NOT NULL;
ALTER TABLE users DROP COLUMN IF EXISTS role;
ALTER TABLE users DROP COLUMN IF EXISTS plan;

-- 3) account_requests: thêm requested_role_id, backfill, bỏ requested_role
ALTER TABLE account_requests ADD COLUMN IF NOT EXISTS requested_role_id INTEGER;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'account_requests' AND column_name = 'requested_role'
    ) THEN
        UPDATE account_requests SET requested_role_id = CASE requested_role
            WHEN 'ADMIN' THEN 1 WHEN 'LECTURER' THEN 2 ELSE 3 END
        WHERE requested_role_id IS NULL;
    END IF;
END $$;
UPDATE account_requests SET requested_role_id = 3 WHERE requested_role_id IS NULL;
ALTER TABLE account_requests ALTER COLUMN requested_role_id SET NOT NULL;
ALTER TABLE account_requests DROP COLUMN IF EXISTS requested_role;

-- 4) (tùy chọn) ràng buộc khóa ngoại — bỏ comment nếu muốn enforce
-- ALTER TABLE users ADD CONSTRAINT fk_users_role
--     FOREIGN KEY (role_id) REFERENCES roles (id);
-- ALTER TABLE account_requests ADD CONSTRAINT fk_req_role
--     FOREIGN KEY (requested_role_id) REFERENCES roles (id);

COMMIT;
