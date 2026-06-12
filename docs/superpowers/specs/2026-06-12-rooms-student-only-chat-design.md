# Design — Phòng học (Rooms), chat chỉ cho Sinh viên, hoàn thiện flow Quiz

Ngày: 2026-06-12. Người dùng yêu cầu (đã chốt scope trong prompt, chạy tự động):

1. Lecturer tạo quiz theo môn → Student làm → nhận điểm ngay → điểm gửi về Lecturer.
2. Lecturer **không** dùng AI chat; chỉ Student cần (Admin giữ quyền giám sát).
3. Tính năng **Room**: chỉ Admin & Lecturer tạo; Lecturer mời Student vào để giao quiz,
   bài tập, slide/doc — tài liệu học tập của môn.
4. Chỉnh logic flow cho hợp lý, không va chạm với tính năng hiện có.
5. Cập nhật README + diagram, commit & push.

## Phương án chọn (so với các phương án khác)

- **A (chọn): Room gắn 1 môn học (course_id).** Quiz/tài liệu của môn tự xuất hiện
  trong room — không cần bảng nối room↔quiz/room↔document. Đơn giản, khớp yêu cầu
  "mỗi môn học sẽ có quiz riêng", không phá flow upload/quiz hiện có.
- B: Room độc lập, gắn từng quiz/tài liệu thủ công (bảng nối). Linh hoạt hơn nhưng
  thừa so với yêu cầu, thêm 2 bảng + UI gán — over-engineering.
- C: Biến Course thành Room. Phá vỡ data model + RAG filter theo course_id. Loại.

## Backend

### Module mới `modules/rooms/`
- `models.py`: `Room(id, name, description, course_id FK, created_by FK users nullable, created_at)`;
  `RoomMember(id, room_id FK, user_id FK, added_at)` unique (room_id, user_id).
- `repository.py`: CRUD room + members, list theo vai trò.
- `service.py`: nghiệp vụ — validate course tồn tại, chỉ mời tài khoản role USER,
  không mời trùng; quyền: Admin mọi room, Lecturer room mình tạo, Student room mình là thành viên.
  Room detail tổng hợp: members + quizzes (QuizService.list) + documents (DocumentService.list) theo course.
- `router.py`:
  - `POST /api/rooms` — Lecturer/Admin.
  - `GET /api/rooms` — Admin: tất cả; Lecturer: của mình; Student: room được mời.
  - `GET /api/rooms/{id}` — thành viên / người tạo / Admin.
  - `POST /api/rooms/{id}/members` (email) / `DELETE /api/rooms/{id}/members/{user_id}` — người tạo / Admin.
  - `DELETE /api/rooms/{id}` — người tạo / Admin.
  - `GET /api/rooms/students` — Lecturer/Admin: danh sách sinh viên để mời.
- Bảng mới do `create_all` tự tạo (SQLite & Postgres) — không cần migration tay.
- Dọn FK: `UserService.delete` xóa membership + gỡ `created_by`; `CourseService.delete`
  xóa room (kèm members) của môn.

### Chat chỉ cho Sinh viên
- `POST /api/chat`, `POST /api/sessions`: `require_role(USER, ADMIN)` (Admin toàn quyền
  theo FR-ADM; Lecturer 403). Các endpoint xem/sửa session giữ nguyên (owner/Admin).

### Quiz flow
- `AttemptOut` thêm `user_name`, `user_email` (join User) — Lecturer thấy điểm của từng SV.
- `GET /quizzes/{id}/attempts`: chỉ **người tạo quiz** hoặc Admin (trước đây mọi Lecturer xem được).
- `submit`: chỉ lưu `QuizAttempt` khi người nộp là Student (Lecturer/Admin xem thử không ghi điểm).

## Frontend
- `RoomsPage` (/rooms): danh sách room (card); Lecturer/Admin có nút tạo (tên, mô tả, môn) + xóa.
- `RoomDetailPage` (/rooms/:id): thông tin room, thành viên (mời/xóa cho người tạo/Admin),
  quiz của môn (Student làm trực tiếp; Lecturer xem kết quả), tài liệu của môn.
- Tách `TakeQuizModal` + thêm `AttemptsModal` vào `components/quiz/` dùng chung
  cho QuizzesPage và RoomDetailPage.
- Sidebar: thêm mục "Phòng học" (mọi role); **ẩn** Hỏi đáp + lịch sử chat với Lecturer;
  Lecturer vào index được điều hướng sang /rooms.
- i18n: thêm khóa rooms.* và quiz.results.* (VI + EN).

## Không thay đổi (tránh va chạm)
- Trang Quiz tổng vẫn liệt kê mọi quiz (demo/test set không phụ thuộc room).
- RAG pipeline, documents, subscriptions, rate-limit giữ nguyên.
- Admin giữ toàn quyền chat/sessions (giám sát).

## Kiểm thử
- Import app + smoke test bằng TestClient (tạo room, mời SV, SV làm quiz, Lecturer xem attempts, Lecturer chat bị 403).
- `npm run build` frontend (TypeScript strict).
