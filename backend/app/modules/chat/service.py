import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.llm.client import LlmClient
from app.modules.chat.models import MsgRole
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import ChatRequest, ChatResponse, Citation
from app.modules.rag.facade import RagFacade

SYSTEM_PROMPT = """Bạn là trợ lý học tập, chỉ trả lời dựa trên NGỮ CẢNH tài liệu được cung cấp bên dưới.

QUY TẮC BẮT BUỘC:
- Chỉ sử dụng thông tin trong phần NGỮ CẢNH. Tuyệt đối KHÔNG bịa đặt.
- Nếu NGỮ CẢNH không chứa thông tin để trả lời, hãy nói rõ: "Tôi không tìm thấy thông tin này trong tài liệu."
- Trả lời bằng tiếng Việt, rõ ràng, súc tích.
- Khi có thể, hãy nhắc đến tên tài liệu/trang mà bạn dựa vào.
- Với công thức/ký hiệu toán học, dùng cú pháp LaTeX: $...$ cho công thức trong dòng và $$...$$ cho công thức tách dòng.
"""

NO_CONTEXT_MSG = "Tôi không tìm thấy thông tin này trong tài liệu."


def _local_answer(retrieved: list[dict]) -> str:
    """Chế độ offline ("ẩn AI"): trả lời trích xuất từ các đoạn liên quan nhất,
    không gọi LLM ngoài. Citations vẫn được trả về riêng như thường."""
    lines = []
    for r in retrieved[:3]:
        snippet = re.sub(r"\s+", " ", r["source_text"]).strip()[:400]
        lines.append(f"• ({r['document_name']}, trang {r['page']}): {snippet}")
    body = "\n".join(lines)
    return (
        "🔌 Chế độ offline (AI đang tắt). Dưới đây là những đoạn tài liệu liên "
        f"quan nhất tới câu hỏi của bạn:\n\n{body}\n\n"
        "Để nhận câu trả lời tổng hợp, hãy đặt GOOGLE_API_KEY và LLM_PROVIDER=gemini."
    )


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChatRepository(db)
        self.rag = RagFacade()
        self.llm = LlmClient()

    def answer(self, req: ChatRequest, user_id: int | None) -> ChatResponse:
        session = self._resolve_session(req, user_id)

        retrieved = self.rag.retrieve(
            req.question, k=4, course_id=req.course_id or session.course_id
        )
        citations = [Citation(**r) for r in retrieved]

        self.repo.add_message(session.id, MsgRole.USER, req.question)

        if not retrieved:
            self.repo.add_message(session.id, MsgRole.ASSISTANT, NO_CONTEXT_MSG)
            return ChatResponse(
                session_id=session.id, answer=NO_CONTEXT_MSG, citations=[]
            )

        if settings.llm_provider == "local":
            answer = _local_answer(retrieved)
        else:
            context = "\n\n---\n".join(
                f"[Nguồn: {r['document_name']} - trang {r['page']}]\n{r['source_text']}"
                for r in retrieved
            )
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in self.repo.recent_history(session.id, limit=6):
                messages.append({"role": m.role.value, "content": m.content})
            messages.append(
                {
                    "role": "user",
                    "content": f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {req.question}",
                }
            )
            answer = self.llm.chat(messages)
        self.repo.add_message(
            session.id, MsgRole.ASSISTANT, answer, [c.model_dump() for c in citations]
        )
        return ChatResponse(
            session_id=session.id, answer=answer, citations=citations
        )

    def _resolve_session(self, req: ChatRequest, user_id: int | None):
        if req.session_id:
            session = self.repo.get_session(req.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Không tìm thấy phiên")
            return session
        title = req.question[:50] + ("..." if len(req.question) > 50 else "")
        return self.repo.create_session(user_id, title, req.course_id)
