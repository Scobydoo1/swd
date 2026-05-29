import time
from functools import lru_cache

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings


@lru_cache
def _client() -> genai.Client:
    # Timeout cứng cho mỗi lần gọi (ms): nếu Gemini/mạng treo, request sẽ
    # bị hủy thay vì giữ chặt thread vô hạn -> không bao giờ làm treo app.
    return genai.Client(
        api_key=settings.google_api_key,
        http_options=types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
    )


# Mỗi lần gọi Gemini tối đa 30s; quá thì hủy và để retry/lỗi xử lý.
_REQUEST_TIMEOUT_MS = 30_000


def _retry_delay(exc: genai_errors.APIError, attempt: int) -> float:
    """Lấy retryDelay server gợi ý (giây), nếu không có thì backoff tăng dần.

    Giới hạn trần delay để một request lỗi không giữ chặt thread (threadpool)
    quá lâu — tránh làm cạn threadpool và treo toàn bộ app.
    """
    try:
        for d in exc.details.get("error", {}).get("details", []):
            if d.get("@type", "").endswith("RetryInfo"):
                raw = d.get("retryDelay", "")  # ví dụ "5s" hoặc "5.7s"
                return min(float(raw.rstrip("s")) + 1, _MAX_RETRY_DELAY)
    except (AttributeError, ValueError, TypeError):
        pass
    return min(2 ** attempt * 2, _MAX_RETRY_DELAY)


# Giữ retry ngắn gọn: chat/embed thất bại sẽ trả lỗi nhanh thay vì ngậm thread.
_MAX_RETRY_DELAY = 8.0
_MAX_ATTEMPTS = 3


def _to_gemini(messages: list[dict]) -> tuple[str | None, list[types.Content]]:
    """Chuyển messages kiểu chat (role/content) -> (system_instruction, contents Gemini)."""
    system_instruction: str | None = None
    contents: list[types.Content] = []
    for m in messages:
        role = m["role"]
        text = m["content"]
        if role == "system":
            system_instruction = text
            continue
        gem_role = "model" if role == "assistant" else "user"
        contents.append(
            types.Content(role=gem_role, parts=[types.Part(text=text)])
        )
    return system_instruction, contents


class LlmClient:
    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        system_instruction, contents = _to_gemini(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )
        # Model có thể trả 503 (quá tải) hoặc 429 (quota) tạm thời -> retry,
        # tôn trọng retryDelay server gợi ý, fallback sang backoff tăng dần.
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = _client().models.generate_content(
                    model=settings.google_chat_model,
                    contents=contents,
                    config=config,
                )
                return resp.text or ""
            except genai_errors.APIError as exc:
                if exc.code in (429, 503) and attempt < _MAX_ATTEMPTS - 1:
                    time.sleep(_retry_delay(exc, attempt))
                    continue
                raise

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Gemini embedding API giới hạn tối đa 100 nội dung mỗi batch
        # và 100 request/phút (free tier) -> chia batch + retry khi 429.
        vectors: list[list[float]] = []
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            for attempt in range(_MAX_ATTEMPTS):
                try:
                    resp = _client().models.embed_content(
                        model=settings.google_embed_model,
                        contents=batch,
                    )
                    vectors.extend(e.values for e in resp.embeddings)
                    break
                except genai_errors.APIError as exc:
                    if exc.code in (429, 503) and attempt < _MAX_ATTEMPTS - 1:
                        time.sleep(_retry_delay(exc, attempt))
                        continue
                    raise
        return vectors
