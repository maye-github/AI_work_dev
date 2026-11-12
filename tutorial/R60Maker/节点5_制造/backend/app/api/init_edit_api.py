"""POST /initEdit（L-212 → L-217 初期値取得）。mode="1"=新規／"2"=複製／"3"=修正。

mode="3" は現在値と排他情報（lastUpdateDatetime・revNo）を返す。削除済みも取得する。
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, Request

from app.config import TZ_TOKYO
from app.domain import init_edit as init_edit_domain
from app.domain import preprocess as pre
from app.schemas import InitEditRequest, InitEditResponse

router = APIRouter()


@router.post("/initEdit", response_model=InitEditResponse)
def init_edit(
    request: Request,
    body: InitEditRequest | None = None,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> InitEditResponse:
    state = request.app.state
    now = datetime.now(TZ_TOKYO)
    try:
        if body is None:
            raise pre.ServiceError(1, "2005", None)
        params = body.params
        with state.engine.connect() as conn:
            pre.preprocess(
                session_store=state.session_store,
                session_token=x_session_id,
                conn=conn,
                endpoint="init_edit",
                now=now,
                validate=lambda: pre.validate_init_edit(params),
            )
            result = init_edit_domain.init_edit(conn, params)
        return InitEditResponse(
            mode=result.mode,
            maker_cd=result.maker_cd,
            maker_nm=result.maker_nm,
            maker_kana_nm=result.maker_kana_nm,
            emergency_dispatch=result.emergency_dispatch,
            delete_flg=result.delete_flg,
            last_update_datetime=result.last_update_datetime,
            rev_no=result.rev_no,
        )
    except pre.ServiceError as exc:
        return InitEditResponse(error_code=exc.error_code, error_id=exc.error_id, msg_id=exc.msg_id)
