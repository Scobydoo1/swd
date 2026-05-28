"""Facade: che giấu embedder (LlmClient) + VectorStore khỏi các module khác."""
from app.llm.client import LlmClient
from app.modules.rag.vector_store import VectorStore


class Citation(dict):
    pass


class RagFacade:
    def __init__(self):
        self.llm = LlmClient()
        self.store = VectorStore()

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
        embeddings = self.llm.embed(texts)
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
        embedding = self.llm.embed([query])[0]
        where = {"course_id": course_id} if course_id is not None else None
        results = self.store.query(embedding, k=k, where=where)
        return [
            {
                "source_text": r["text"],
                "document_name": r["meta"].get("document_name", ""),
                "page": r["meta"].get("page"),
                "score": round(r["score"], 4),
            }
            for r in results
        ]

    def delete_document(self, document_id: int) -> None:
        self.store.delete_document(document_id)
