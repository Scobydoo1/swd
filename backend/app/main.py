from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.modules.account_requests.router import router as account_requests_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.courses.router import router as courses_router
from app.modules.documents.router import router as documents_router
from app.modules.quizzes.router import router as quizzes_router
from app.modules.rooms.router import router as rooms_router
from app.modules.users.router import router as users_router

app = FastAPI(title="Course Document RAG Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    # Seed Admin đầu tiên (không còn đăng ký công khai).
    from app.database import SessionLocal
    from app.modules.users.service import ensure_default_admin

    db = SessionLocal()
    try:
        ensure_default_admin(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(account_requests_router)
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(quizzes_router)
app.include_router(rooms_router)
