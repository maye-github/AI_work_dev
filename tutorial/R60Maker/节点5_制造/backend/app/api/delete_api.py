"""POST /delete（L-212 → L-219 削除）。MKR03 のみ。

被参照 → 排他 → 論理削除 → commit 確定後に緊急配信を非同期起動 → 最後の検索条件で 1 頁目を再検索。
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, Request

from app.config import TZ_TOKYO
from app.domain import delete as delete_domain
from app.domain import preprocess as pre
from app.domain import search as search_domain
from app.schemas import DeleteRequest, DeleteResponse, MakerItem, Pager

router = APIRouter()


def _research_first_page(state, session_token: str | None):  # noqa: ANN001
    last = state.session_store.get_last_search(session_token) if session_token else None
    if last is None:
        return [], 0, None
    params = last.model_copy(update={"page_no": 1})
    with state.engine.connect() as conn:
        result = search_domain.search(conn, params)
    items = [MakerItem(**item) for item in result.items]
    pager = Pager(
        page_no=result.page_no,
        total_pages=result.total_pages,
        page_size=result.page_size,
        total_count=result.total_count,
    )
    return items, result.total_count, pager


@router.post("/delete", response_model=DeleteResponse)
def delete(
    request: Request,
    body: DeleteRequest | None = None,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> DeleteResponse:
    state = request.app.state
    now = datetime.now(TZ_TOKYO)
    try:
        if body is None:
            raise pre.ServiceError(1, "2005", None)
        params = body.params
        with state.engine.begin() as conn:
            info = pre.preprocess(
                session_store=state.session_store,
                session_token=x_session_id,
                conn=conn,
                endpoint="delete",
                now=now,
                validate=lambda: pre.validate_delete(params),
            )
            result = delete_domain.delete(
                conn,
                params,
                reference_checker=state.reference_checker,
                upd_user=info.user_id,
                now=now,
            )
        # commit 確定後に緊急配信を非同期起動（業務トランザクションをロールバックしない）
        if result.dispatch_payload is not None:
            state.dispatcher.dispatch(result.dispatch_payload)
        items, total_count, pager = _research_first_page(state, x_session_id)
        return DeleteResponse(
            error_code=0,
            error_id="0000",
            msg_id="MSG-I-002",
            items=items,
            total_count=total_count,
            pager=pager,
        )
    except pre.ServiceError as exc:
        return DeleteResponse(error_code=exc.error_code, error_id=exc.error_id, msg_id=exc.msg_id)
