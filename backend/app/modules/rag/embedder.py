"""Embedder: cổng duy nhất tạo vector cho RAG.

§11.7: embedding chỉ đi qua module này. Chọn provider theo cấu hình:
- "local": hashing vectorizer offline (không cần key) — xem local_embedder.
- "gemini": gọi Google embedding qua `llm/` client wrapper.
"""
from app.config import settings
from app.llm.client import LlmClient
from app.modules.rag import local_embedder


class Embedder:
    def __init__(self) -> None:
        self._llm = LlmClient()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed một batch văn bản (dùng khi ingest tài liệu)."""
        if settings.embed_provider == "local":
            return [local_embedder.embed(t) for t in texts]
        return self._llm.embed(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed một câu hỏi đơn -> vector (dùng khi truy vấn)."""
        if settings.embed_provider == "local":
            return local_embedder.embed(text)
        return self._llm.embed([text])[0]
