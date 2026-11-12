"""POST /search（L-212 → L-214 検索 → L-215 ページャ委譲）。

- 0 件は E-213（1／1001）を返しつつ検索成功扱い。500 件超は E-214（1／1002）。HTTP は 200 固定。
- 成功時は「最後に実行した検索条件」を Session へ保持する（/download・/delete・/edit の再検索で使う）。
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, Request

from app.config import TZ_TOKYO
from app.domain import preprocess as pre
from app.domain import search as search_domain
from app.schemas import MakerItem, Pager, SearchRequest, SearchResponse

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(
    request: Request,
    body: SearchRequest | None = None,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> SearchResponse:
    state = request.app.state
    req = body or SearchRequest()
    params = req.params
    now = datetime.now(TZ_TOKYO)
    try:
        with state.engine.connect() as conn:
            pre.preprocess(
                session_store=state.session_store,
                session_token=x_session_id,
                conn=conn,
                endpoint="search",
                now=now,
                validate=lambda: pre.validate_search(params),
            )
            result = search_domain.search(conn, params)
        # 検索が成立した条件を保持（0 件も含む）
        if x_session_id is not None:
            state.session_store.set_last_search(x_session_id, params)
        return SearchResponse(
            error_code=result.error_code,
            error_id=result.error_id,
            msg_id=result.msg_id,
            items=[MakerItem(**item) for item in result.items],
            total_count=result.total_count,
            pager=Pager(
                page_no=result.page_no,
                total_pages=result.total_pages,
                page_size=result.page_size,
                total_count=result.total_count,
            ),
        )
    except pre.ServiceError as exc:
        return SearchResponse(error_code=exc.error_code, error_id=exc.error_id, msg_id=exc.msg_id)
