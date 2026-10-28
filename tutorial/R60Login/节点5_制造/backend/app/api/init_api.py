"""`POST /R60Login/init`（イベント１ 初期表示）。L-201 → L-202。05 §2.3。

* 端点は 3 本で固定であり、本ファイルがその 1 本である（05 §1.3）。4 本目を設けない。
* 応答は `errorCode` で区分する（I-318）。稼働不可だけは HTTP 403（E-206・05 §6.1）。
* 候補 0 件は**エラーではない**（`errorCode="0"`）。文言とボタン非活性はクライアントが行う（B-22）。
* エラー文言はサーバが SQL-6 で取得し、応答の `errorMessage`（`I-321`・発番待ち）に載せる（05 §5.7）。
"""

from __future__ import annotations

import logging
import secrets
import threading

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.domain.availability import check_available
from app.repository.queries import (
    VALID_FLG_ON,
    fetch_page_candidates,
    resolve_error_message,
)
from app.schemas import InitResponse, OptionItem

router = APIRouter()

_SCREEN_ID = "R60Login"

# 05 §2.3 ステップ5 / I-315: 権限区分候補は 2 件固定（画面値 Y/N。内部値 1/0 への写像は §4.4）。
_KBN_LIST = (
    OptionItem(value="Y", label="更新あり"),
    OptionItem(value="N", label="更新なし"),
)

# 05 §2.3 ステップ8〜9: 「同一クライアント内の連続 3 回」を数えるための識別子。
# 設計はクライアントの識別方法を定めていないため、本節点で Cookie を 1 本持たせる（差異登記に記載）。
_CLIENT_COOKIE_NAME = "r60login.cid"
_INIT_FAILURE_LOG_THRESHOLD = 3
_init_failure_counts: dict[str, int] = {}
_init_failure_lock = threading.Lock()


def _record_init_failure(client_id: str, logger: logging.Logger) -> None:
    """E-204 の連続回数を数え、ちょうど 3 回目に運用ログを 1 件だけ出す（05 §2.3 ステップ8〜9）。"""
    with _init_failure_lock:
        count = _init_failure_counts.get(client_id, 0) + 1
        _init_failure_counts[client_id] = count
    if count == _INIT_FAILURE_LOG_THRESHOLD:
        # 運用ログの項目は 時刻・画面ID・結果コードのみ（社員コードを出さない・05 §8.1）。
        logger.warning("init_failure_repeated", extra={"screen_id": _SCREEN_ID, "result_code": "R60E9999"})


def _reset_init_failures(client_id: str) -> None:
    """成功したら連続回数を 0 に戻す（「連続」の意味を保つ）。"""
    with _init_failure_lock:
        _init_failure_counts.pop(client_id, None)


def _respond(
    model: InitResponse,
    *,
    status_code: int = 200,
    client_id: str | None = None,
    secure: bool = False,
) -> JSONResponse:
    # 応答は camelCase（serialize_by_alias）。未設定項目は載せない（`errorDetailCode` は異常時のみ）。
    response = JSONResponse(
        status_code=status_code,
        content=model.model_dump(by_alias=True, mode="json", exclude_none=True),
    )
    if client_id is not None:
        # 連続失敗の計数にのみ用いる。利用者の識別情報は持たない（乱数のみ・ログへ出さない）。
        response.set_cookie(
            key=_CLIENT_COOKIE_NAME,
            value=client_id,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )
    return response


@router.post("/R60Login/init")
async def init(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    engine = request.app.state.engine
    logger: logging.Logger = request.app.state.logger
    client_id = request.cookies.get(_CLIENT_COOKIE_NAME) or secrets.token_urlsafe(16)
    secure = settings.url_scheme == "https"

    # L-201 稼働判定（先頭・1 回だけ）。不可なら E-206（HTTP 403）。
    if not check_available(engine, operation_key=settings.operation_key, logger=logger):
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60W0004"})
        return _respond(
            InitResponse(
                error_code="1",
                error_detail_code="R60W0004",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60W0004", logger=logger
                ),
            ),
            status_code=403,
            client_id=client_id,
            secure=secure,
        )

    # L-202 ステップ2: 画面マスタの照会（SQL-2）。
    try:
        with engine.connect() as conn:
            rows = fetch_page_candidates(conn, valid=VALID_FLG_ON)
    except Exception:
        # L-202 ステップ3 / 分岐 2: SQL-2 の例外は E-204（errorCode="2"・R60E9999・HTTP 200）。
        # 05 §2.3 ステップ8〜9: 同一クライアント内の連続 3 回で運用ログ 1 件（計数は Cookie の識別子で行う）。
        _record_init_failure(client_id, logger)
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60E9999"})
        return _respond(
            InitResponse(
                error_code="2",
                error_detail_code="R60E9999",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60E9999", logger=logger
                ),
            ),
            client_id=client_id,
            secure=secure,
        )

    # L-202 ステップ4: I-314 = {value: gmn_id, label: gmn_nm} の配列（有効行・表示順の昇順）。
    page_list = [OptionItem(value=str(gmn_id), label=str(gmn_nm)) for gmn_id, gmn_nm in rows]

    _reset_init_failures(client_id)
    logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "0"})
    # ステップ5: I-315 は 2 件固定。ステップ6: 0 件でも errorCode="0"（エラーではない）。
    return _respond(
        InitResponse(error_code="0", page_list=page_list, kbn_list=list(_KBN_LIST)),
        client_id=client_id,
        secure=secure,
    )
