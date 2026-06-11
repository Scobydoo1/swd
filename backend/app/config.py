from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    google_chat_model: str = "gemini-2.5-flash"
    google_embed_model: str = "gemini-embedding-001"

    # Provider AI: "local" (offline, không cần API key — ẩn AI) hoặc "gemini"
    # (gọi Google API). Mặc định "local" để chạy được ngay không cần key.
    embed_provider: str = "local"
    llm_provider: str = "local"
    local_embed_dim: int = 512

    chroma_dir: str = "./data/chroma"
    database_url: str = "sqlite:///./data/app.db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # Google OAuth (đăng nhập Google) — Client ID từ Google Cloud Console.
    google_oauth_client_id: str = ""

    # Gmail SMTP (App Password) để gửi email cấp tài khoản.
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""  # mặc định dùng smtp_user
    app_login_url: str = "http://localhost:5173"

    # Seed Admin đầu tiên khi startup (vì không còn đăng ký công khai).
    admin_email: str = ""
    admin_password: str = ""
    admin_full_name: str = "Quản trị viên"

    # Vector store backend: "chroma" (dev local) | "pgvector" (Neon/Postgres).
    vector_backend: str = "chroma"

    cors_origins: str = (
        "http://localhost:5173,http://localhost,https://localhost,"
        "capacitor://localhost,https://scobydoo1.github.io"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
