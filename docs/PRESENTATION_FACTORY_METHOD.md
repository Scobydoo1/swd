# Presentation: Design Patterns — Factory Method (8–10 phút)

Dàn ý theo đúng outline trên bảng: Định nghĩa → Phân loại DP → Demo.

## 1. Definition (~2 phút)

**Design Pattern** là một giải pháp tổng quát, đã được kiểm chứng, cho một vấn đề
thiết kế phần mềm lặp lại — không phải code copy-paste, mà là một *khuôn mẫu* mô
tả cách các object/class tương tác để giải quyết vấn đề đó trong một ngữ cảnh cụ
thể.

Vì sao cần: giúp code dễ mở rộng, dễ bảo trì, và tạo ngôn ngữ chung giữa các lập
trình viên ("à đây là Factory Method" thay vì phải giải thích lại toàn bộ logic).

## 2. Types of Design Patterns (~2 phút)

Ba nhóm chính (GoF – Gang of Four), phân loại theo **mục đích**:

| Nhóm | Trả lời câu hỏi | Ví dụ pattern |
|------|------------------|----------------|
| **Creational** (khởi tạo) | "Đối tượng được tạo ra như thế nào?" | Factory Method, Abstract Factory, Builder, Singleton, Prototype |
| **Structural** (cấu trúc) | "Các object/class được ghép với nhau ra sao?" | Adapter, Facade, Decorator, Composite, Proxy |
| **Behavioral** (hành vi) | "Các object giao tiếp / phân chia trách nhiệm ra sao?" | Strategy, Observer, Command, Template Method, State |

→ **Factory Method** thuộc nhóm **Creational**: nó giải quyết bài toán *"làm sao
tạo object mà không phải hard-code class cụ thể vào nơi gọi"*.

## 3. Factory Method — chi tiết

**Định nghĩa:** Định nghĩa một interface (hoặc phương thức) để tạo object, nhưng
để **subclass/implementation quyết định class nào sẽ được khởi tạo**. Caller chỉ
làm việc với interface chung (Product), không biết — và không cần biết — class cụ
thể.

**Thành phần:**
- **Product** — interface chung cho các object được tạo ra.
- **ConcreteProduct** — các implementation cụ thể của Product.
- **Factory method** — hàm/method nhận một "chìa khóa" (type/enum) và trả về đúng
  ConcreteProduct, ẩn logic `if/else` hoặc `switch` chọn class khỏi phần code
  nghiệp vụ.

**Khi nào dùng:** khi một class không thể biết trước chính xác object nào nó cần
tạo (phụ thuộc input tại runtime), và bạn muốn thêm loại object mới mà không sửa
code gọi hiện có (Open/Closed Principle).

## 4. Demo trong dự án (~4–5 phút)

File: `backend/app/modules/documents/parsers.py`

Bài toán: hệ thống RAG chatbot cho phép Lecturer upload tài liệu **PDF / DOCX /
PPTX**. Mỗi định dạng cần một cách parse hoàn toàn khác nhau (`pypdf`,
`python-docx`, `python-pptx`), nhưng phần code gọi (`DocumentService`) chỉ muốn
gọi một hàm `.parse(content)` duy nhất mà không cần biết đang xử lý định dạng gì.

```python
class DocumentParser(ABC):          # Product
    @abstractmethod
    def parse(self, content: bytes) -> list[tuple[str, int]]: ...

class PdfParser(DocumentParser): ...   # ConcreteProduct
class DocxParser(DocumentParser): ...  # ConcreteProduct
class PptxParser(DocumentParser): ...  # ConcreteProduct

_PARSER_FACTORIES: dict[FileType, type[DocumentParser]] = {
    FileType.PDF: PdfParser,
    FileType.DOCX: DocxParser,
    FileType.PPTX: PptxParser,
}

def create_parser(file_type: FileType) -> DocumentParser:   # Factory method
    return _PARSER_FACTORIES[file_type]()
```

`DocumentService.upload_document()` (trong `service.py`) chỉ gọi:

```python
file_type = parsers.detect_file_type(filename)
parsers.validate_mime(file_type, content_type)
pages = parsers.parse(content, file_type)   # nội bộ: create_parser(file_type).parse(content)
```

→ `service.py` không import `PdfParser`/`DocxParser`/`PptxParser`, không có
`if file_type == "pdf": ... elif ...`. Muốn hỗ trợ thêm định dạng mới (ví dụ
`.txt`) chỉ cần thêm 1 class `TxtParser` + 1 dòng trong `_PARSER_FACTORIES` —
không đụng vào `service.py` hay bất kỳ nơi nào khác gọi `parsers.parse(...)`.

**Điểm nhấn khi demo (live hoặc code walkthrough):**
1. Chỉ ra vấn đề nếu KHÔNG dùng Factory Method: `service.py` sẽ phải biết class
   cụ thể (`PdfParser()`, `DocxParser()`...) → vi phạm nguyên tắc *tách biệt
   trách nhiệm* và khó mở rộng.
2. Chạy thử: upload 1 file PDF và 1 file PPTX qua API `/api/documents`, cho thấy
   cùng một luồng code (`upload_document`) xử lý đúng cả hai nhờ factory method
   chọn đúng parser tại runtime.
3. So sánh nhanh với **Strategy pattern** (dễ nhầm lẫn): Strategy tập trung vào
   *chọn thuật toán/hành vi* để dùng ngay, còn Factory Method tập trung vào
   *tạo ra object* — ở đây `create_parser()` vừa chọn vừa khởi tạo instance
   `DocumentParser`, đúng bản chất Creational, nên xếp vào Factory Method.

## 5. Kết luận (~30s)

Factory Method giúp tách "quyết định tạo object nào" ra khỏi "cách dùng object
đó", làm code dễ mở rộng khi thêm định dạng tài liệu mới mà không sửa logic
nghiệp vụ hiện có — đúng tinh thần Open/Closed Principle.
