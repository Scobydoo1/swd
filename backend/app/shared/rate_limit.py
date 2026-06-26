"""Rate limiting cho AI chat endpoint (§12: tránh lạm dụng).

Sliding-window đơn giản trong bộ nhớ — đủ cho modular monolith single-process.
Dùng như một FastAPI dependency: nó vừa xác thực (qua get_current_user) vừa
giới hạn số request mỗi người dùng trong một cửa sổ thời gian.

Giới hạn cố định cho Sinh viên (AI chat chỉ dành cho Sinh viên); Giảng viên &
Admin không bị giới hạn.
"""
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status

from app.modules.users.models import Role, User
from app.shared.dependencies import get_current_user

# Số câu hỏi tối đa mỗi phút cho một Sinh viên (thay cho giới hạn theo gói cũ).
STUDENT_CHAT_PER_MIN = 30


class RateLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window = window_seconds
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        # Chỉ Sinh viên (USER) bị giới hạn. Giảng viên & Admin không giới hạn.
        if user.role != Role.USER:
            return user
        max_calls = STUDENT_CHAT_PER_MIN
        now = time.monotonic()
        hits = self._hits[user.id]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Bạn đã đạt giới hạn câu hỏi mỗi phút. "
                    "Vui lòng thử lại sau ít phút."
                ),
            )
        hits.append(now)
        return user


# Cửa sổ 60 giây; số lượng cho phép lấy theo gói của từng người dùng.
chat_rate_limit = RateLimiter(window_seconds=60)


class IPRateLimiter:
    """Giới hạn theo IP cho endpoint công khai (không cần đăng nhập).

    Dùng cho form 'Yêu cầu tài khoản' — chống spam nhẹ, đủ cho monolith
    single-process (sliding window trong bộ nhớ, giống RateLimiter ở trên).
    """

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[ip]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn gửi yêu cầu quá nhanh. Vui lòng thử lại sau.",
            )
        hits.append(now)


# Form yêu cầu tài khoản: tối đa 5 yêu cầu / giờ / IP.
account_request_rate_limit = IPRateLimiter(max_calls=5, window_seconds=3600)
