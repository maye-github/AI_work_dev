"""任意: FastAPI 版の検索 API。

システム Python に fastapi が入っていない場合があるため、
run.py からは import しない。導入後に単体起動するか、
既存 FastAPI アプリに build_router() で合流させる。

    pip install fastapi uvicorn
    uvicorn api:app --reload
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from kbkit import store
from kbkit.embedder import get_embedder
from kbkit.retrieval import build_context, search

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "kb.sqlite3"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, title="検索文")
    project_id: Optional[str] = Field(None, title="案件ID")
    user_level: int = Field(30, ge=10, le=40, title="利用者の権限レベル")
    top_k: int = Field(5, ge=1, le=50)
    with_context: bool = Field(False, title="LLM用コンテキストを返す")


class Hit(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    heading: Optional[str]
    scope: str
    project_id: Optional[str]
    doc_type: str
    text: str
    score: float
    citation: str


class SearchResponse(BaseModel):
    hits: list[Hit]
    context: Optional[str] = None


def build_router(db_path: str | Path = DEFAULT_DB, embedder_name: str = "hash") -> APIRouter:
    router = APIRouter(prefix="/kb", tags=["kb"])
    embedder = get_embedder(embedder_name)

    def _conn():
        conn = store.connect(db_path)
        store.init_schema(conn)
        try:
            yield conn
        finally:
            conn.close()

    @router.post("/search", response_model=SearchResponse)
    def kb_search(req: SearchRequest, conn=Depends(_conn)):
        hits = search(
            conn, req.query, embedder,
            project_id=req.project_id,
            user_level=req.user_level,
            top_k=req.top_k,
        )
        ctx = build_context(hits) if req.with_context else None
        return {"hits": hits, "context": ctx}

    @router.get("/stats")
    def kb_stats(conn=Depends(_conn)):
        return store.stats(conn)

    return router


def create_app(db_path: str | Path = DEFAULT_DB) -> "object":
    from fastapi import FastAPI

    app = FastAPI(title="kb-platform", version="0.1.0")
    app.include_router(build_router(db_path))
    return app


try:
    app = create_app()
except Exception:  # fastapi 未導入時は API 単体起動不可。run.py は影響なし
    app = None


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    if app is None:
        raise SystemExit("fastapi が未導入です: pip install fastapi uvicorn")
    uvicorn.run(app, host="127.0.0.1", port=8000)
