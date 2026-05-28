# Yêu cầu gốc của dự án

Tài liệu môn học là các chapters trong textbook trên FLM: *Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures*.

## Các yêu cầu tối thiểu

### A. Tính năng hệ thống

**1. Quản lý tài liệu**
- Upload PDF, DOCX, slide bài giảng
- Tự động chunk & embed tài liệu
- Quản lý theo môn học / chương (chỉ cần demo 1 môn)
- Xem danh sách tài liệu đã index

**2. Chat & Hỏi đáp**
- Chat tự nhiên theo ngữ cảnh hội thoại
- Trích dẫn nguồn tài liệu gốc
- Giới hạn trả lời trong phạm vi tài liệu
- Lịch sử hội thoại theo phiên

### B. Sản phẩm bàn giao (Deliverables)

1. Sản phẩm kỹ thuật:
   - Web app chatbot
   - Source code trên GitHub (có README)
   - Test set 50 câu hỏi + ground truth (tập câu hỏi + câu trả lời đúng được chuẩn bị sẵn bởi con người, dùng để đánh giá độ chính xác của chatbot)

## Lựa chọn thiết kế
- Kiến trúc **Modular Monolith**, project đơn giản chỉ đáp ứng đủ yêu cầu, giao diện đẹp bắt mắt.
- Frontend dùng **React**.
- Bổ sung 3 actor: **Admin**, **Lecturer**, **User**.
- Sản phẩm thiết kế: **UML, Use Cases, Patterns, Software Architectures** — xem [DESIGN.md](DESIGN.md).
