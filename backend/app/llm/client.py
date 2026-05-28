from functools import lru_cache

from openai import OpenAI

from app.config import settings


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


class LlmClient:
    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        resp = _client().chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = _client().embeddings.create(
            model=settings.openai_embed_model,
            input=texts,
        )
        return [d.embedding for d in resp.data]
