"""Facade: che giấu embedder + vector_store + retriever khỏi các module khác.

Các module nghiệp vụ (documents, chat) chỉ dùng RagFacade, không chạm trực
tiếp vào embedder/vector store/retriever.
"""
from app.modules.rag.embedder import Embedder
from app.modules.rag.retriever import Retriever
from app.modules.rag.vector_store import get_vector_store


class RagFacade:
    def __init__(self) -> None:
        self.embedder = Embedder()
        self.store = get_vector_store()
        self.retriever = Retriever(self.embedder, self.store)

    def index_chunks(
        self,
        document_id: int,
        course_id: int,
        document_name: str,
        chunks: list[dict],
    ) -> int:
        if not chunks:
            return 0
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed(texts)
        ids = [f"{document_id}-{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "course_id": course_id,
                "document_name": document_name,
                "page": c["page"],
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ]
        self.store.add(ids, embeddings, texts, metadatas)
        return len(chunks)

    def retrieve(
        self, query: str, k: int = 4, course_id: int | None = None
    ) -> list[dict]:
        return self.retriever.search(query, k=k, course_id=course_id)

    def delete_document(self, document_id: int) -> None:
        self.store.delete_document(document_id)
