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
)
from app.modules.chat.service import ChatService
from app.modules.users.models import Role
from app.shared.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return ChatService(db).answer(req, user_id=user.id)


@router.post("/sessions", response_model=SessionOut)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return ChatRepository(db).create_session(
        user.id, payload.title or "Cuộc trò chuyện mới", payload.course_id
    )


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return ChatRepository(db).list_sessions(
        user.id, is_admin=user.role == Role.ADMIN
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = ChatRepository(db).get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên")
    if user.role != Role.ADMIN and session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền xem phiên này")

    messages = []
    for m in session.messages:
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
        created_at=session.created_at,
        messages=messages,
    )
