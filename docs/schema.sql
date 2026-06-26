-- =====================================================================
-- Maple — Course Document RAG Chatbot
-- Physical Database Schema (DDL) — chạy trực tiếp được
-- =====================================================================
-- DBMS gốc của app: SQLite (qua SQLAlchemy). Script này được viết
-- tương thích SQLite, đồng thời di động sang Postgres/MySQL với chỉnh
-- sửa nhỏ (xem ghi chú cuối file).
--
-- Cách chạy (SQLite):
--   sqlite3 maple.db < docs/schema.sql
-- hoặc trong sqlite3:  .read docs/schema.sql
--
-- Thứ tự tạo bảng theo phụ thuộc khóa ngoại (FK):
--   roles → users → courses → chapters → documents
--                 → chat_sessions → messages
--                 → quizzes → quiz_questions → quiz_attempts
--                 → rooms → room_members
--   roles → account_requests
--
-- Lưu ý: vector + chunk text KHÔNG nằm ở đây — chúng ở ChromaDB.
-- SQLite chỉ giữ metadata. Bật ràng buộc FK mỗi phiên:
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- ROLES — vai trò (RBAC) tách thành entity riêng, không nhúng vào users
-- ---------------------------------------------------------------------
CREATE TABLE roles (
    id           INTEGER NOT NULL PRIMARY KEY,
    code         VARCHAR(20) NOT NULL,            -- ADMIN | LECTURER | USER
    name         VARCHAR(100) NOT NULL,
    description  VARCHAR(255) NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX ix_roles_code ON roles (code);

-- Seed cố định 3 vai trò (id khớp thứ tự enum trong code):
INSERT INTO roles (id, code, name, description) VALUES
    (1, 'ADMIN',    'Quản trị viên', 'Toàn quyền: người dùng, tài liệu, môn học, phòng học, giám sát'),
    (2, 'LECTURER', 'Giảng viên',    'Tài liệu, môn học/chương, quiz, phòng học của mình'),
    (3, 'USER',     'Sinh viên',     'Chat hỏi đáp RAG, làm quiz, tham gia phòng học');

-- ---------------------------------------------------------------------
-- USERS — tài khoản; role tham chiếu roles qua role_id (FK)
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              INTEGER  NOT NULL PRIMARY KEY,
    email           VARCHAR  NOT NULL,
    password_hash   VARCHAR  NOT NULL,            -- bcrypt, không lưu plaintext
    full_name       VARCHAR  NOT NULL,
    role_id         INTEGER  NOT NULL DEFAULT 3,  -- → roles.id (mặc định USER)
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles (id)
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

-- ---------------------------------------------------------------------
-- COURSES — môn học, owner là Lecturer
-- ---------------------------------------------------------------------
CREATE TABLE courses (
    id           INTEGER NOT NULL PRIMARY KEY,
    name         VARCHAR NOT NULL,
    description  VARCHAR NOT NULL DEFAULT '',
    owner_id     INTEGER,                          -- → users.id (Lecturer)
    FOREIGN KEY (owner_id) REFERENCES users (id)
);

-- ---------------------------------------------------------------------
-- CHAPTERS — chương thuộc môn học
-- ---------------------------------------------------------------------
CREATE TABLE chapters (
    id          INTEGER NOT NULL PRIMARY KEY,
    course_id   INTEGER NOT NULL,
    title       VARCHAR NOT NULL,
    "order"     INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

-- ---------------------------------------------------------------------
-- DOCUMENTS — tài liệu đã upload + trạng thái index
-- ---------------------------------------------------------------------
CREATE TABLE documents (
    id           INTEGER NOT NULL PRIMARY KEY,
    course_id    INTEGER NOT NULL,
    chapter_id   INTEGER,                          -- nullable
    uploaded_by  INTEGER,                          -- → users.id
    filename     VARCHAR NOT NULL,
    file_type    VARCHAR(4) NOT NULL
                 CHECK (file_type IN ('PDF', 'DOCX', 'PPTX')),
    status       VARCHAR(10) NOT NULL DEFAULT 'PROCESSING'
                 CHECK (status IN ('PROCESSING', 'INDEXED', 'FAILED')),
    num_chunks   INTEGER NOT NULL DEFAULT 0,
    error        VARCHAR,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id)  REFERENCES courses (id),
    FOREIGN KEY (chapter_id) REFERENCES chapters (id),
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

-- ---------------------------------------------------------------------
-- CHAT_SESSIONS — phiên chat của người dùng
-- ---------------------------------------------------------------------
CREATE TABLE chat_sessions (
    id          INTEGER NOT NULL PRIMARY KEY,
    user_id     INTEGER,                           -- → users.id
    course_id   INTEGER,                           -- môn đang hỏi (nullable)
    title       VARCHAR NOT NULL DEFAULT 'Cuộc trò chuyện mới',
    pinned      BOOLEAN NOT NULL DEFAULT 0,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

-- ---------------------------------------------------------------------
-- MESSAGES — tin nhắn trong phiên; citations lưu dạng JSON
-- ---------------------------------------------------------------------
CREATE TABLE messages (
    id              INTEGER NOT NULL PRIMARY KEY,
    session_id      INTEGER NOT NULL,
    role            VARCHAR(9) NOT NULL
                    CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    citations_json  TEXT,                          -- JSON: list[Citation]
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
);

-- ---------------------------------------------------------------------
-- QUIZZES — quiz trắc nghiệm gắn với môn học
-- ---------------------------------------------------------------------
CREATE TABLE quizzes (
    id          INTEGER NOT NULL PRIMARY KEY,
    course_id   INTEGER NOT NULL,
    title       VARCHAR NOT NULL,
    created_by  INTEGER,                           -- → users.id (Lecturer/Admin)
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id)  REFERENCES courses (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- ---------------------------------------------------------------------
-- QUIZ_QUESTIONS — câu hỏi; options_json = list[str], correct_index = đáp án đúng
-- ---------------------------------------------------------------------
CREATE TABLE quiz_questions (
    id             INTEGER NOT NULL PRIMARY KEY,
    quiz_id        INTEGER NOT NULL,
    text           TEXT NOT NULL,
    options_json   TEXT NOT NULL,                  -- JSON: list[str] (>= 2 lựa chọn)
    correct_index  INTEGER NOT NULL,               -- chỉ lộ sau khi nộp bài
    "order"        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);

-- ---------------------------------------------------------------------
-- QUIZ_ATTEMPTS — lượt làm bài + điểm
-- ---------------------------------------------------------------------
CREATE TABLE quiz_attempts (
    id            INTEGER NOT NULL PRIMARY KEY,
    quiz_id       INTEGER NOT NULL,
    user_id       INTEGER,                         -- → users.id (Student)
    score         FLOAT NOT NULL,                  -- % đúng (0..100)
    answers_json  TEXT NOT NULL,                   -- JSON: list[int] đáp án đã chọn
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- ---------------------------------------------------------------------
-- ROOMS — phòng học (Lecturer/Admin tạo, gắn một môn học)
-- ---------------------------------------------------------------------
CREATE TABLE rooms (
    id           INTEGER NOT NULL PRIMARY KEY,
    name         VARCHAR NOT NULL,
    description  VARCHAR NOT NULL DEFAULT '',
    course_id    INTEGER NOT NULL,
    created_by   INTEGER,                          -- → users.id (Lecturer/Admin)
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id)  REFERENCES courses (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- ---------------------------------------------------------------------
-- ROOM_MEMBERS — sinh viên được mời vào phòng (unique room_id + user_id)
-- ---------------------------------------------------------------------
CREATE TABLE room_members (
    id        INTEGER NOT NULL PRIMARY KEY,
    room_id   INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,                    -- → users.id (Student)
    added_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (room_id, user_id)
);

-- ---------------------------------------------------------------------
-- ACCOUNT_REQUESTS — yêu cầu cấp tài khoản công khai; Admin duyệt/từ chối
-- ---------------------------------------------------------------------
CREATE TABLE account_requests (
    id                 INTEGER NOT NULL PRIMARY KEY,
    email              VARCHAR NOT NULL,
    full_name          VARCHAR NOT NULL,
    requested_role_id  INTEGER NOT NULL DEFAULT 3, -- → roles.id (LECTURER/USER)
    message            VARCHAR NOT NULL DEFAULT '',
    status             VARCHAR(8) NOT NULL DEFAULT 'PENDING'
                       CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at         DATETIME,                   -- nullable: thời điểm duyệt/từ chối
    FOREIGN KEY (requested_role_id) REFERENCES roles (id)
);
CREATE INDEX ix_account_requests_email ON account_requests (email);

-- =====================================================================
-- Ghi chú di động (Postgres / MySQL):
--   • INTEGER PRIMARY KEY  → SERIAL/IDENTITY (PG) hoặc INT AUTO_INCREMENT (MySQL)
--   • DATETIME             → TIMESTAMP (PG) / DATETIME (MySQL)
--   • BOOLEAN DEFAULT 0    → DEFAULT FALSE
--   • "order" (từ khóa)    → giữ trong ngoặc kép (PG) hoặc backtick `order` (MySQL)
--   • Có thể đổi CHECK(...) enum sang kiểu ENUM/native nếu muốn.
-- =====================================================================
