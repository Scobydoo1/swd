"""Retriever: similarity search trên ChromaDB + filter theo môn/chương."""
from app.modules.rag.embedder import Embedder
from app.modules.rag.vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def search(
        self, query: str, k: int = 4, course_id: int | None = None
    ) -> list[dict]:
        embedding = self._embedder.embed_query(query)
        where = {"course_id": course_id} if course_id is not None else None
        results = self._store.query(embedding, k=k, where=where)
        return [
            {
                "source_text": r["text"],
                "document_name": r["meta"].get("document_name", ""),
                "page": r["meta"].get("page"),
                "score": round(r["score"], 4),
            }
            for r in results
        ]
