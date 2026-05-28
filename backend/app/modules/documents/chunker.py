from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_pages(pages: list[tuple[str, int]]) -> list[dict]:
    """pages: list of (text, page_no) -> list of {text, page, chunk_index}."""
    chunks: list[dict] = []
    idx = 0
    for text, page in pages:
        for piece in _splitter.split_text(text):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append({"text": piece, "page": page, "chunk_index": idx})
            idx += 1
    return chunks
