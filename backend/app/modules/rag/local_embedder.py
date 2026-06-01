"""Embedding cục bộ, không cần API key (chế độ "ẩn AI").

Hashing vectorizer xác định (deterministic) trên unigram + bigram -> vector
cố định chiều, chuẩn hóa L2. Cosine similarity trên vector này cho retrieval
theo độ trùng lặp từ khóa — đủ dùng cho demo offline. Bật lại Gemini bằng
EMBED_PROVIDER=gemini khi đã có GOOGLE_API_KEY.
"""
import hashlib
import math
import re

from app.config import settings

_TOKEN = re.compile(r"\w+", re.UNICODE)


def _bucket(feature: str) -> tuple[int, float]:
    digest = hashlib.md5(feature.encode("utf-8")).digest()
    h = int.from_bytes(digest[:8], "big")
    idx = h % settings.local_embed_dim
    sign = 1.0 if (h >> 1) & 1 else -1.0
    return idx, sign


def _features(text: str) -> list[str]:
    toks = _TOKEN.findall(text.lower())
    bigrams = [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
    return toks + bigrams


def embed(text: str) -> list[float]:
    dim = settings.local_embed_dim
    vec = [0.0] * dim
    for feature in _features(text):
        idx, sign = _bucket(feature)
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]
