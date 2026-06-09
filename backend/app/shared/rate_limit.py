"""Rate limiting cho AI chat endpoint (§12: tránh lạm dụng).

Sliding-window đơn giản trong bộ nhớ — đủ cho modular monolith single-process.
Dùng như một FastAPI dependency: nó vừa xác thực (qua get_current_user) vừa
giới hạn số request mỗi người dùng trong một cửa sổ thời gian.

Giới hạn theo GÓI đăng ký (Free/Pro/Max) — đây là quyền lợi được thực thi
cụ thể của subscription, xem `subscriptions/plans.py`.
"""
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status

from app.modules.subscriptions.plans import chat_per_min
from app.modules.users.models import Role, User
from app.shared.dependencies import get_current_user


class RateLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window = window_seconds
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        # Chỉ Sinh viên (USER) bị giới hạn theo gói. Giảng viên & Admin
        # không cần subscription nên được dùng không giới hạn.
        if user.role != Role.USER:
            return user
        max_calls = chat_per_min(user.plan)
        now = time.monotonic()
        hits = self._hits[user.id]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Bạn đã đạt giới hạn câu hỏi của gói hiện tại. "
                    "Hãy thử lại sau hoặc nâng cấp gói."
                ),
            )
        hits.append(now)
        return user


# Cửa sổ 60 giây; số lượng cho phép lấy theo gói của từng người dùng.
chat_rate_limit = RateLimiter(window_seconds=60)
