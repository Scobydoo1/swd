from functools import lru_cache

import chromadb

from app.config import settings


def _collection_name() -> str:
    # Tách collection theo provider: vector local (512 chiều) và Gemini
    # (vài nghìn chiều) khác số chiều -> không được trộn chung một collection.
    return f"course_documents_{settings.embed_provider}"


@lru_cache
def _collection():
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    return client.get_or_create_collection(
        name=_collection_name(), metadata={"hnsw:space": "cosine"}
    )


class VectorStore:
    def add(self, ids: list[str], embeddings, documents, metadatas) -> None:
        _collection().add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(self, embedding, k: int, where: dict | None = None) -> list[dict]:
        res = _collection().query(
            query_embeddings=[embedding],
            n_results=k,
            where=where or None,
        )
        results = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            results.append({"text": doc, "meta": meta, "score": 1 - dist})
        return results

    def delete_document(self, document_id: int) -> None:
        _collection().delete(where={"document_id": document_id})
