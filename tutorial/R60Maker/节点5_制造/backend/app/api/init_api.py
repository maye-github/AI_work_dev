"""POST /init（L-212 前処理 → L-213 初期化処理）。検索画面の初期表示。

応答: errorCode/errorId・serverTime(I-323 JST)・company/dept/userName(I-324〜05)・
      pageSizeOptions(I-333)・messageInfo(SQL 4.2)・初期状態。HTTP は 200 固定。
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, Request

from app.config import INIT_MESSAGE_IDS, TZ_TOKYO
from app.domain import preprocess as pre
from app.repository import queries
from app.schemas import InitRequest, InitResponse, MessageInfo

router = APIRouter()


@router.post("/init", response_model=InitResponse)
def init(
    request: Request,
    body: InitRequest | None = None,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> InitResponse:
    state = request.app.state
    now = datetime.now(TZ_TOKYO)
    messages: list[MessageInfo] = []
    try:
        with state.engine.connect() as conn:
            info = pre.preprocess(
                session_store=state.session_store,
                session_token=x_session_id,
                conn=conn,
                endpoint="init",
                now=now,
                validate=lambda: None,  # L-213 は利用者入力を用いない
            )
            for msg_id in INIT_MESSAGE_IDS:
                row = queries.fetch_message(conn, msg_id)
                if row is not None:
                    messages.append(MessageInfo(**row))
        return InitResponse(
            server_time=now.strftime("%Y/%m/%d %H:%M:%S"),
            company_nm=info.company_nm,
            dept_nm=info.dept_nm,
            user_name=info.user_name,
            page_size=20,
            include_deleted=False,
            shikake_mode=False,
            condition_expanded=True,
            items=[],
            total_count=0,
            message_info=messages,
        )
    except pre.ServiceError as exc:
        return InitResponse(error_code=exc.error_code, error_id=exc.error_id, msg_id=exc.msg_id)
