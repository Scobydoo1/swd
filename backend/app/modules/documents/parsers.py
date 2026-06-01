"""Strategy pattern: chọn parser theo loại file -> trả về list (text, page)."""
import io

from app.modules.documents.models import FileType


def _parse_pdf(content: bytes) -> list[tuple[str, int]]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((text, i))
    return pages


def _parse_docx(content: bytes) -> list[tuple[str, int]]:
    from docx import Document as DocxDocument

    doc = DocxDocument(io.BytesIO(content))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [(text, 1)] if text.strip() else []


def _parse_pptx(content: bytes) -> list[tuple[str, int]]:
    from pptx import Presentation

    prs = Presentation(io.BytesIO(content))
    pages = []
    for i, slide in enumerate(prs.slides, start=1):
        parts = [
            shape.text
            for shape in slide.shapes
            if shape.has_text_frame and shape.text.strip()
        ]
        if parts:
            pages.append(("\n".join(parts), i))
    return pages


_PARSERS = {
    FileType.PDF: _parse_pdf,
    FileType.DOCX: _parse_docx,
    FileType.PPTX: _parse_pptx,
}


def detect_file_type(filename: str) -> FileType:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return FileType.PDF
    if lower.endswith(".docx"):
        return FileType.DOCX
    if lower.endswith(".pptx"):
        return FileType.PPTX
    raise ValueError("Định dạng không hỗ trợ (chỉ PDF, DOCX, PPTX)")


# FR-LEC-01 / §11.3 / §12: chỉ chấp nhận PDF, DOCX, PPTX — validate cả MIME
# type lẫn extension ở server side.
_ALLOWED_MIME: dict[FileType, set[str]] = {
    FileType.PDF: {"application/pdf"},
    FileType.DOCX: {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    FileType.PPTX: {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    },
}

# MIME chung chung mà nhiều client gửi khi không nhận diện được — khi đó tin
# vào extension đã được kiểm ở detect_file_type.
_GENERIC_MIME = {"", "application/octet-stream", "binary/octet-stream"}


def validate_mime(file_type: FileType, content_type: str | None) -> None:
    if (content_type or "") in _GENERIC_MIME:
        return
    if content_type not in _ALLOWED_MIME[file_type]:
        raise ValueError(
            f"Nội dung tệp ({content_type}) không khớp định dạng "
            f"{file_type.value}"
        )


def parse(content: bytes, file_type: FileType) -> list[tuple[str, int]]:
    return _PARSERS[file_type](content)
