import json

from sqlalchemy.orm import Session

from app.modules.chat.models import ChatSession, Message, MsgRole


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self, user_id: int | None, title: str, course_id: int | None
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title, course_id=course_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> ChatSession | None:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

    def list_sessions(self, user_id: int | None, is_admin: bool) -> list[ChatSession]:
        q = self.db.query(ChatSession)
        if not is_admin:
            q = q.filter(ChatSession.user_id == user_id)
        return q.order_by(
            ChatSession.pinned.desc(), ChatSession.created_at.desc()
        ).all()

    def update_session(
        self,
        session: ChatSession,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ChatSession:
        if title is not None:
            session.title = title
        if pinned is not None:
            session.pinned = pinned
        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session: ChatSession) -> None:
        self.db.delete(session)
        self.db.commit()

    def add_message(
        self,
        session_id: int,
        role: MsgRole,
        content: str,
        citations: list[dict] | None = None,
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            citations_json=json.dumps(citations) if citations else None,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def recent_history(self, session_id: int, limit: int = 6) -> list[Message]:
        msgs = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(msgs))
