"""POST /download（L-212 → L-218 ダウンロード）。MKR03 のみ。CSV 生成はサーバ、保存はクライアント。

- **最後に実行した検索条件**を用いる（画面の現在値は使わない。設計 §2.7 手順①）。
- 成功時は CSV ファイル（UTF-8 BOM・CRLF・ヘッダ・5 列）。失敗時は JSON（errorCode/errorId）。HTTP は 200 固定。
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse

from app.config import TZ_TOKYO
from app.domain import download as download_domain
from app.domain import preprocess as pre
from app.schemas import DownloadParams

router = APIRouter()

CSV_FILENAME = "maker_master.csv"


@router.post("/download")
def download(
    request: Request,
    body: DownloadRequest | None = None,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> Response:
    state = request.app.state
    now = datetime.now(TZ_TOKYO)
    try:
        last = state.session_store.get_last_search(x_session_id) if x_session_id else None
        if last is None:
            # 前提（検索成功後）未成立。設計に専用エラーが無いため入力エラー扱い（要確認）。
            raise pre.ServiceError(1, "2005", None)
        # 最後の検索条件から /download 用の項目へ写す（pageNo は対象外。全件出力）
        params = DownloadParams(
            maker_cd=last.maker_cd,
            maker_nm=last.maker_nm,
            include_deleted=last.include_deleted,
            page_size=last.page_size,
            shikake_mode=last.shikake_mode,
            sort_field=last.sort_field,
        )
        with state.engine.connect() as conn:
            pre.preprocess(
                session_store=state.session_store,
                session_token=x_session_id,
                conn=conn,
                endpoint="download",
                now=now,
                validate=lambda: pre.validate_download(params),
            )
            content = download_domain.build_csv(conn, params)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{CSV_FILENAME}"'},
        )
    except pre.ServiceError as exc:
        return JSONResponse(
            status_code=200,
            content={"errorCode": exc.error_code, "errorId": exc.error_id, "msgId": exc.msg_id},
        )
