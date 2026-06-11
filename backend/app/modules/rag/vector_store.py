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


class PgVectorStore:
    """Vector store trên Postgres + pgvector (Neon free).

    Dùng khi deploy Render free (disk ephemeral): vector lưu DB ngoài nên
    không mất khi service restart. Cùng interface với VectorStore (Chroma).
    Cột `embedding vector` không khai báo số chiều -> một bảng theo
    provider (chiều local 512 / gemini 3072 không trộn lẫn, như Chroma).
    """

    def __init__(self) -> None:
        from app.database import engine

        self._engine = engine
        self._table = f"rag_chunks_{settings.embed_provider}"
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        from sqlalchemy import text

        with self._engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table} (
                        id TEXT PRIMARY KEY,
                        document_id INTEGER NOT NULL,
                        course_id INTEGER,
                        document_name TEXT NOT NULL DEFAULT '',
                        page INTEGER,
                        chunk_index INTEGER,
                        text TEXT NOT NULL,
                        embedding vector NOT NULL
                    )
                    """
                )
            )

    @staticmethod
    def _vec(embedding) -> str:
        # Literal pgvector: "[0.1,0.2,...]".
        return "[" + ",".join(str(float(x)) for x in embedding) + "]"

    def add(self, ids: list[str], embeddings, documents, metadatas) -> None:
        from sqlalchemy import text

        rows = [
            {
                "id": id_,
                "document_id": meta["document_id"],
                "course_id": meta.get("course_id"),
                "document_name": meta.get("document_name", ""),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index"),
                "text": doc,
                "embedding": self._vec(emb),
            }
            for id_, emb, doc, meta in zip(ids, embeddings, documents, metadatas)
        ]
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    f"""
                    INSERT INTO {self._table}
                        (id, document_id, course_id, document_name, page,
                         chunk_index, text, embedding)
                    VALUES
                        (:id, :document_id, :course_id, :document_name, :page,
                         :chunk_index, :text, CAST(:embedding AS vector))
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding
                    """
                ),
                rows,
            )

    def query(self, embedding, k: int, where: dict | None = None) -> list[dict]:
        from sqlalchemy import text

        filter_sql = ""
        params: dict = {"vec": self._vec(embedding), "k": k}
        if where and where.get("course_id") is not None:
            filter_sql = "WHERE course_id = :course_id"
            params["course_id"] = where["course_id"]

        sql = text(
            f"""
            SELECT text, document_id, course_id, document_name, page,
                   chunk_index,
                   1 - (embedding <=> CAST(:vec AS vector)) AS score
            FROM {self._table}
            {filter_sql}
            ORDER BY embedding <=> CAST(:vec AS vector)
            LIMIT :k
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
        return [
            {
                "text": r["text"],
                "meta": {
                    "document_id": r["document_id"],
                    "course_id": r["course_id"],
                    "document_name": r["document_name"],
                    "page": r["page"],
                    "chunk_index": r["chunk_index"],
                },
                "score": float(r["score"]),
            }
            for r in rows
        ]

    def delete_document(self, document_id: int) -> None:
        from sqlalchemy import text

        with self._engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {self._table} WHERE document_id = :doc_id"),
                {"doc_id": document_id},
            )


def get_vector_store():
    """Factory chọn backend vector theo env VECTOR_BACKEND."""
    if settings.vector_backend == "pgvector":
        return PgVectorStore()
    return VectorStore()
