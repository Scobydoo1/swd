import time
from functools import lru_cache

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings


@lru_cache
def _client() -> genai.Client:
    return genai.Client(api_key=settings.google_api_key)


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
        # Model có thể trả 503 (quá tải) hoặc 429 (quota) tạm thời -> retry.
        for attempt in range(4):
            try:
                resp = _client().models.generate_content(
                    model=settings.google_chat_model,
                    contents=contents,
                    config=config,
                )
                return resp.text or ""
            except genai_errors.APIError as exc:
                if exc.code in (429, 503) and attempt < 3:
                    time.sleep(5)
                    continue
                raise

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Gemini embedding API giới hạn tối đa 100 nội dung mỗi batch
        # và 100 request/phút (free tier) -> chia batch + retry khi 429.
        vectors: list[list[float]] = []
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            for attempt in range(6):
                try:
                    resp = _client().models.embed_content(
                        model=settings.google_embed_model,
                        contents=batch,
                    )
                    vectors.extend(e.values for e in resp.embeddings)
                    break
                except genai_errors.ClientError as exc:
                    if exc.code == 429 and attempt < 5:
                        time.sleep(20)
                        continue
                    raise
        return vectors
