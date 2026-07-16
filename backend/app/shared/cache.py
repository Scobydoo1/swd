"""Cache TTL trong-process cho danh sách đọc nhiều (§12: chịu tải nhiều người dùng).

Mọi role đều đọc /courses và /documents liên tục khi mở app — cache lại để
giảm tải DB. Đúng đắn vì backend deploy MỘT process (Render free): mọi đường
ghi đều đi qua process này nên invalidate tại chỗ là đủ. TTL ngắn làm lưới an
toàn: nếu một đường ghi nào đó quên invalidate, dữ liệu cũ sống tối đa TTL.

Nếu sau này chạy nhiều instance sau load balancer, thay bằng Redis — giữ
nguyên interface get/set/invalidate.
"""
import threading
from time import monotonic
from typing import Any


class TTLCache:
    """Cache key -> value với hạn sống, thread-safe (endpoint sync chạy
    trong threadpool nên nhiều thread cùng truy cập)."""

    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self.ttl = ttl_seconds
        self._lock = threading.Lock()
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Trả giá trị còn hạn, None nếu miss/hết hạn ([] vẫn là giá trị hợp lệ)."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if monotonic() >= expires_at:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = (monotonic() + self.ttl, value)

    def invalidate(self, prefix: str) -> None:
        """Xóa mọi key bắt đầu bằng prefix (vd. "documents" xóa documents:*)."""
        with self._lock:
            for key in [k for k in self._data if k.startswith(prefix)]:
                del self._data[key]

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


# Cache dùng chung cho các danh sách toàn cục (courses, documents).
list_cache = TTLCache(ttl_seconds=60.0)
