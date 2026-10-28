"""埋め込み。

Phase 0 は外部モデル不要の決定的なハッシュ埋め込み。
本番は BgeM3Embedder に差し替える（インタフェースは同じ）。
"""

from __future__ import annotations

import re
import unicodedata
import zlib

import numpy as np

_KEEP_RE = re.compile(r"[^0-9a-z぀-ヿ㐀-䶿一-鿿]+")
_SPACE_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"[a-z0-9_]+")


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = _KEEP_RE.sub(" ", s)
    return _SPACE_RE.sub(" ", s).strip()


class HashingEmbedder:
    """文字 n-gram の符号付きハッシュ。日本語は文字 bigram が効く。"""

    name = "hash-ngram"

    def __init__(self, dim: int = 1024):
        self.dim = dim
        self.name = f"hash-ngram-{dim}"

    def _add(self, vec: np.ndarray, gram: str, weight: float) -> None:
        h = zlib.crc32(gram.encode("utf-8"))
        idx = h % self.dim
        sign = 1.0 if (h >> 16) & 1 else -1.0
        vec[idx] += sign * weight

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        norm = normalize_text(text)
        compact = norm.replace(" ", "")
        for n, w in ((1, 0.35), (2, 1.0), (3, 0.7)):
            if len(compact) < n:
                continue
            for i in range(len(compact) - n + 1):
                self._add(vec, f"{n}:{compact[i:i + n]}", w)
        for tok in _WORD_RE.findall(norm):
            self._add(vec, "w:" + tok, 1.2)
        norm2 = float(np.linalg.norm(vec))
        if norm2 > 0:
            vec /= norm2
        return vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return (
            np.vstack([self.embed(t) for t in texts])
            if texts
            else np.zeros((0, self.dim), dtype=np.float32)
        )


class BgeM3Embedder:
    """本番用。sentence-transformers とモデルの DL が必要。"""

    name = "bge-m3"

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        from sentence_transformers import SentenceTransformer  # 遅延 import

        self.model = SentenceTransformer(model_name, trust_remote_code=True)

    def embed(self, text: str) -> np.ndarray:
        v = self.model.encode([text], normalize_embeddings=True)[0]
        return np.asarray(v, dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1024), dtype=np.float32)
        return np.asarray(
            self.model.encode(texts, normalize_embeddings=True), dtype=np.float32
        )


def get_embedder(name: str = "hash"):
    if name in ("hash", "hash-ngram"):
        return HashingEmbedder()
    if name in ("bge", "bge-m3"):
        return BgeM3Embedder()
    raise ValueError(f"unknown embedder: {name}")
