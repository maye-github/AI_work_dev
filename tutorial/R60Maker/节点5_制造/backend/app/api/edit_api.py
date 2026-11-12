"""POST /edit（L-212 → L-220 登録更新）。MKR02 以上。

新規・複製・修正を mode で分岐。登録・更新の完了時は最後の検索条件で 1 頁目を再検索した一覧を返す。
変更なし（MSG-I-003）は登録せず、画面を閉じない（再検索しない）。
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, Request

from app.config import TZ_TOKYO
from app.domain import edit as edit_domain
from app.domain import preprocess as pre
from app.domain import search as search_domain
from app.schemas import EditRequest, EditResponse, MakerItem, Pager

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


@router.post("/edit", response_model=EditResponse)
def edit(
    request: Request,
    body: EditRequest | None = None,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> EditResponse:
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
                endpoint="edit",
                now=now,
                validate=lambda: pre.validate_edit(params),
            )
            result = edit_domain.edit(
                conn,
                params,
                reference_checker=state.reference_checker,
                reg_user=info.user_id,
                upd_user=info.user_id,
                now=now,
            )
        # commit 確定後に緊急配信を非同期起動
        if result.dispatch_payload is not None:
            state.dispatcher.dispatch(result.dispatch_payload)
        if not result.wrote:
            # 変更なし（MSG-I-003）。登録せず、画面を閉じない＝再検索しない。
            return EditResponse(error_code=0, error_id="0000", msg_id=result.msg_id)
        items, total_count, pager = _research_first_page(state, x_session_id)
        return EditResponse(
            error_code=0,
            error_id="0000",
            items=items,
            total_count=total_count,
            pager=pager,
        )
    except pre.ServiceError as exc:
        return EditResponse(error_code=exc.error_code, error_id=exc.error_id, msg_id=exc.msg_id)
