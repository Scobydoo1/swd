def test_factory_returns_chroma_by_default(client):
    from app.modules.rag.vector_store import VectorStore, get_vector_store

    store = get_vector_store()
    assert isinstance(store, VectorStore)


def test_factory_returns_pgvector_when_configured(client, monkeypatch):
    from app.config import settings
    from app.modules.rag import vector_store

    monkeypatch.setattr(settings, "vector_backend", "pgvector")
    # Không có Postgres thật trong test -> chặn phần tạo bảng.
    monkeypatch.setattr(
        vector_store.PgVectorStore, "_ensure_schema", lambda self: None
    )
    store = vector_store.get_vector_store()
    assert isinstance(store, vector_store.PgVectorStore)


def test_pgvector_literal_format(client):
    from app.modules.rag.vector_store import PgVectorStore

    assert PgVectorStore._vec([0.1, 0.25, -1]) == "[0.1,0.25,-1.0]"
