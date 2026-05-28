import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Ensure data dir exists for SQLite file.
_db_path = settings.database_url.replace("sqlite:///", "")
os.makedirs(os.path.dirname(os.path.abspath(_db_path)), exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register on Base before create_all.
    from app.modules.users import models as user_models  # noqa: F401
    from app.modules.courses import models as course_models  # noqa: F401
    from app.modules.documents import models as doc_models  # noqa: F401
    from app.modules.chat import models as chat_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
