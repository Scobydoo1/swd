# Cập nhật tính năng (Updates)

Tài liệu mô tả 5 nhóm tính năng bổ sung gần đây và thiết kế của chúng.
Xem thêm: [DESIGN.md](DESIGN.md) · [REQUIREMENTS.md](REQUIREMENTS.md) · [../CLAUDE.md](../CLAUDE.md)

---

## 1. Múi giờ Việt Nam (Asia/Ho_Chi_Minh)

**Vấn đề:** Backend lưu `created_at` theo UTC nhưng serialize dạng *naive* ISO
(`2026-06-27T10:30:00`, không có hậu tố `Z`). Trình duyệt hiểu nhầm chuỗi naive là
giờ **local** → lệch giờ khi hiển thị.

**Thiết kế:** Giữ nguyên backend (đã lưu UTC). Frontend có tiện ích
[`src/lib/datetime.ts`](../frontend/src/lib/datetime.ts):
- `parseServerDate()` — coi mốc không có timezone là UTC (thêm `Z`).
- `formatDateTimeVN` / `formatDateVN` / `fromNowVN` — format qua
  `Intl.DateTimeFormat("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })`.

Dùng ở: bảng điểm, màn xem lại, bảng kết quả của Lecturer, nhóm thời gian sidebar.

## 2. Định dạng toán học (KaTeX)

Render công thức toán trong chat và đề/đáp án quiz.
- Thư viện: `katex` (+ CSS import ở [`main.tsx`](../frontend/src/main.tsx)).
- [`src/lib/math.tsx`](../frontend/src/lib/math.tsx): `MathInline`, `MathBlock`,
  `splitInlineMath`, và `MathText` (text thường có inline math).
- [`Markdown.tsx`](../frontend/src/components/Markdown.tsx) hỗ trợ `$...$` (inline)
  và `$$...$$` (block). Đề/đáp án quiz bọc qua `<MathText>`.
- System prompt chat được nhắc dùng LaTeX cho công thức.

## 3. Xem lại kết quả & Bảng điểm (Grade)

**Yêu cầu:** Sinh viên làm xong xem lại được kết quả; có mục lục **Grade** gom
mọi kết quả theo **môn học**.

**Backend** (module `quizzes`):
- `GET /api/quizzes/grades/me?course_id=` → danh sách `GradeItem` (mọi lượt làm của
  chính mình, kèm tên quiz + điểm + số đúng/tổng).
- `GET /api/quizzes/attempts/{attempt_id}` → `AttemptReview` (đề + đáp án đã chọn vs
  đáp án đúng từng câu). Sinh viên chỉ xem bài của mình; Lecturer/Admin xem mọi bài.
- Chấm điểm tách thành `QuizService._grade()` dùng chung cho `submit`, `grades`,
  `review`. (Lưu ý: chỉ lưu attempt cho role `USER`.)
- Hai route đặt **trước** `/{quiz_id}` để không bị nuốt path.

**Frontend:** trang [`GradePage.tsx`](../frontend/src/pages/GradePage.tsx) (route
`/grades`, nav chỉ hiện cho Sinh viên) — nhóm theo môn, lọc theo môn, modal **Xem lại**.

## 4. Nạp giáo trình chính vào RAG (seed)

Script [`backend/scripts/seed_textbook.py`](../backend/scripts/seed_textbook.py)
ingest cuốn *Software Modeling and Design* (Gomaa) qua đúng pipeline upload
(parse → chunk → embed → index ChromaDB) để hỏi đáp chạy sẵn.
- Chạy: `cd backend && python -m scripts.seed_textbook`
- Idempotent (bỏ qua nếu môn đã có tài liệu); chạy offline với `embed_provider=local`.

## 5. AI soạn quiz (Gemini) — Lecturer duyệt/sửa

**Luồng:** Lecturer mở form tạo quiz → bấm **Soạn đề** (chọn số câu + chủ đề) →
AI sinh **nháp** đề từ tài liệu môn → đề đổ vào form để **chỉnh sửa** → bấm **Lưu**
(qua `POST /api/quizzes` như bình thường). AI **không tự lưu**.

**Backend:** `POST /api/quizzes/generate` (Lecturer/Admin) → `GeneratedQuiz`.
- Lấy ngữ cảnh bằng `RagFacade.retrieve(topic, k=8, course_id)`.
- Gemini (qua `llm/` wrapper) được ép trả JSON; `QuizService._parse_generated()`
  bóc mảng JSON, validate từng câu bằng `QuestionIn` (bỏ câu sai, giữ phần hợp lệ).
- Cần bật Gemini (`LLM_PROVIDER=gemini`); chế độ `local` trả `400` báo rõ.
