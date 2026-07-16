import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    MessageOut,
    SessionCreate,
    SessionDetail,
    SessionOut,
    SessionUpdate,
)
from app.modules.chat.service import ChatService
from app.modules.users.models import Role
from app.shared.dependencies import get_current_user, require_role
from app.shared.rate_limit import chat_rate_limit

router = APIRouter(prefix="/api", tags=["chat"])


# FR-USR-02 / FR-USR-03: Chat hỏi đáp RAG -> answer + citations.
# §12: rate-limited để tránh lạm dụng (chat_rate_limit cũng xác thực user).
# Chỉ Sinh viên cần hỏi đáp AI (Admin giữ toàn quyền); Giảng viên bị chặn.
@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user=Depends(chat_rate_limit),
    _=Depends(require_role(Role.USER, Role.ADMIN)),
):
    return ChatService(db).answer(req, user_id=user.id)


# Chat chỉ dành cho Sinh viên (+Admin) nên tạo phiên cũng giới hạn tương ứng.
@router.post("/sessions", response_model=SessionOut)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(Role.USER, Role.ADMIN)),
):
    return ChatRepository(db).create_session(
        user.id, payload.title or "Cuộc trò chuyện mới", payload.course_id
    )


# FR-USR-04: Danh sách phiên chat của chính mình (Admin xem tất cả).
@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return ChatRepository(db).list_sessions(
        user.id, is_admin=user.role == Role.ADMIN
    )


# FR-USR-04 / §11.4: Lịch sử messages của một phiên (Owner hoặc Admin).
# Hỗ trợ phân trang qua limit/offset; mặc định trả từ đầu phiên.
@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    limit: int | None = None,
    offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = ChatRepository(db).get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên")
    if user.role != Role.ADMIN and session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền xem phiên này")

    page = session.messages[offset:]
    if limit is not None:
        page = page[:limit]
    messages = []
    for m in page:
        cites = json.loads(m.citations_json) if m.citations_json else []
        messages.append(
            MessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                created_at=m.created_at,
                citations=[Citation(**c) for c in cites],
            )
        )
    return SessionDetail(
        id=session.id,
        title=session.title,
        course_id=session.course_id,
        pinned=session.pinned,
        created_at=session.created_at,
        messages=messages,
    )


def _get_owned_session(repo: ChatRepository, session_id: int, user):
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên")
    if user.role != Role.ADMIN and session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền với phiên này")
    return session


@router.patch("/sessions/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    repo = ChatRepository(db)
    session = _get_owned_session(repo, session_id, user)
    return repo.update_session(session, title=payload.title, pinned=payload.pinned)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    repo = ChatRepository(db)
    session = _get_owned_session(repo, session_id, user)
    repo.delete_session(session)
