"""Định nghĩa 3 gói đăng ký: Free / Pro / Max (nguồn duy nhất).

Một quyền lợi được THỰC THI cụ thể: giới hạn tốc độ chat theo gói
(`chat_per_min`). Các quyền lợi khác hiển thị trên trang giá để demo.
"""

PLANS: list[dict] = [
    {
        "id": "FREE",
        "name": "Free",
        "price": 0,
        "price_label": "0₫",
        "tagline": "Bắt đầu miễn phí",
        "chat_per_min": 20,
        "doc_limit": 3,
        "quiz_limit": 2,
        "features": [
            "20 câu hỏi mỗi phút",
            "Hỏi đáp RAG có trích dẫn nguồn",
            "Làm quiz của giảng viên",
            "Lưu lịch sử hội thoại cơ bản",
        ],
    },
    {
        "id": "PRO",
        "name": "Pro",
        "price": 99000,
        "price_label": "99.000₫/tháng",
        "tagline": "Cho người học nghiêm túc",
        "chat_per_min": 60,
        "doc_limit": 50,
        "quiz_limit": 20,
        "highlight": True,
        "features": [
            "60 câu hỏi mỗi phút",
            "Lịch sử hội thoại không giới hạn",
            "Làm mọi quiz, xem lại kết quả",
            "Ưu tiên truy xuất tài liệu khi hỏi đáp",
        ],
    },
    {
        "id": "MAX",
        "name": "Max",
        "price": 199000,
        "price_label": "199.000₫/tháng",
        "tagline": "Toàn bộ sức mạnh",
        "chat_per_min": 120,
        "doc_limit": 1000,
        "quiz_limit": 1000,
        "features": [
            "Câu hỏi gần như không giới hạn (120/phút)",
            "Ưu tiên xử lý phản hồi",
            "Làm mọi quiz, xem lại kết quả & lời giải",
            "Hỗ trợ ưu tiên",
        ],
    },
]

PLAN_BY_ID: dict[str, dict] = {p["id"]: p for p in PLANS}


def _key(plan) -> str:
    # Chấp nhận cả Enum Plan lẫn chuỗi.
    return getattr(plan, "value", plan) or "FREE"


def chat_per_min(plan) -> int:
    return PLAN_BY_ID.get(_key(plan), PLAN_BY_ID["FREE"])["chat_per_min"]
