"""Unit tests cho TTLCache (shared/cache.py) — cache trong-process cho
danh sách đọc nhiều (§12: tối ưu nhiều người dùng đồng thời)."""
import pytest


@pytest.fixture()
def cache():
    from app.shared.cache import TTLCache

    return TTLCache(ttl_seconds=60.0)


def test_set_get_roundtrip(cache):
    cache.set("k", [{"id": 1}])
    assert cache.get("k") == [{"id": 1}]


def test_get_missing_returns_none(cache):
    assert cache.get("khong-ton-tai") is None


def test_empty_list_is_a_valid_cached_value(cache):
    # [] là giá trị hợp lệ (danh sách rỗng) — phải phân biệt được với miss.
    cache.set("k", [])
    assert cache.get("k") == []


def test_entry_expires_after_ttl(cache, monkeypatch):
    import app.shared.cache as cache_module

    now = 1000.0
    monkeypatch.setattr(cache_module, "monotonic", lambda: now)
    cache.set("k", "v")
    assert cache.get("k") == "v"

    # Quá TTL -> coi như miss.
    monkeypatch.setattr(cache_module, "monotonic", lambda: now + 61.0)
    assert cache.get("k") is None


def test_invalidate_by_prefix(cache):
    cache.set("documents:1", ["a"])
    cache.set("documents:2", ["b"])
    cache.set("courses", ["c"])

    cache.invalidate("documents")

    assert cache.get("documents:1") is None
    assert cache.get("documents:2") is None
    assert cache.get("courses") == ["c"]


def test_clear_removes_everything(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
