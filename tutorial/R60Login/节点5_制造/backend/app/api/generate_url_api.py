"""`POST /R60Login/generateUrl`（イベント４ URL 出力）。L-201 → L-205 → L-206。05 §2.6。

* **組立（ステップ6）と 150 桁判定（ステップ7）はサーバ**が行う（裁定 Q-233）。
  クライアントは応答の `url`（I-310）を表示するだけで、組み立て直さない・桁判定をやり直さない。
* パラメータ順は `stfCd` → `stfKbn` → `gmnId` → `kgnKbn` の**固定順**。UTF-8・パーセントエンコード不要（Q-201）。
* I-303 未入力は文字列 `"NaN"` を社員コードとして扱い、**暗号化せず** `stfCd=NaN` を載せる（裁定 Q-231）。
* 150 桁超は**切捨てない**（E-210）。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.domain.availability import check_available
from app.domain.stf_cd_cipher import StfCdCipherError, encrypt_stf_cd, today_jst_yyyymmdd
from app.repository.queries import resolve_error_message
from app.schemas import GenerateUrlRequest, GenerateUrlResponse

router = APIRouter()

_SCREEN_ID = "R60Login"

# 05 §7.3 B-20／B-21: 受付上限は 150 桁ちょうど。151 桁以上は E-210。
_URL_MAX_LENGTH = 150


def _respond(model: GenerateUrlResponse, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=model.model_dump(by_alias=True, mode="json", exclude_none=True),
    )


def _normalize_stf_cd(raw: str) -> str:
    """L-205 ステップ3: 前後空白は trim せず、全角・非 ASCII を半角へ変換して除去する（Q-210）。

    全角 ASCII（U+FF01〜U+FF5E）だけ半角へ写し、残った非 ASCII は落とす。
    ASCII 空白（0x20）は「非 ASCII」ではないため残る（B-07 と同じ扱い）。
    """
    normalized: list[str] = []
    for char in raw:
        code = ord(char)
        if 0xFF01 <= code <= 0xFF5E:
            char = chr(code - 0xFEE0)
        if ord(char) < 0x80:
            normalized.append(char)
    return "".join(normalized)


def _mask_stf_cd(stf_cd: str) -> str:
    """工程04 §6.2: 先頭 1 桁と末尾 1 桁を残し、中間を `*` に置換する。"""
    if len(stf_cd) <= 2:
        return "*" * len(stf_cd)
    return stf_cd[0] + "*" * (len(stf_cd) - 2) + stf_cd[-1]


@router.post("/R60Login/generateUrl")
async def generate_url(payload: GenerateUrlRequest, request: Request) -> JSONResponse:
    settings = request.app.state.settings
    engine = request.app.state.engine
    logger: logging.Logger = request.app.state.logger

    # L-201 稼働判定（先頭・1 回だけ）。不可なら E-203（HTTP 403）。
    if not check_available(engine, operation_key=settings.operation_key, logger=logger):
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60W0004"})
        return _respond(
            GenerateUrlResponse(
                error_code="1",
                error_detail_code="R60W0004",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60W0004", logger=logger
                ),
            ),
            status_code=403,
        )

    # L-205 ステップ2: 未入力（空文字）は入力エラーとせず `"NaN"` を社員コードとして扱う（Q-214・Q-231）。
    masked_stf_cd: str | None = None
    if payload.stf_cd == "":
        url_stf_cd = "NaN"
    else:
        # ステップ3: 正規化（trim しない・全角／非 ASCII の除去）。
        normalized = _normalize_stf_cd(payload.stf_cd)
        # ステップ4: 半角数字 1 桁以上なら可（7 桁固定は課さない・裁定 Q-231）。数字以外が残る／0 桁は不可。
        if not normalized or not normalized.isascii() or not normalized.isdigit():
            # 分岐 4 / B-40: E-202（`1`／`R60W0001`）。URL を生成しない。
            logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60W0001"})
            return _respond(
                GenerateUrlResponse(
                    error_code="1",
                    error_detail_code="R60W0001",
                    error_message=resolve_error_message(
                        engine, error_detail_code="R60W0001", logger=logger
                    ),
                )
            )

        # ステップ5: L-206 で暗号化する。日付はサーバの JST（05 §2.7・§8.4）。
        try:
            url_stf_cd = encrypt_stf_cd(normalized, today_jst_yyyymmdd())
        except StfCdCipherError:
            # 分岐 2: 暗号化失敗・設定不備は E-209（`2`／`R60E9999`・HTTP 200）。
            logger.error("system_error", extra={"screen_id": _SCREEN_ID, "result_code": "R60E9999"})
            return _respond(
                GenerateUrlResponse(
                    error_code="2",
                    error_detail_code="R60E9999",
                    error_message=resolve_error_message(
                        engine, error_detail_code="R60E9999", logger=logger
                    ),
                )
            )
        masked_stf_cd = _mask_stf_cd(normalized)

    # ステップ6: URL を組み立てる（サーバ）。順序固定・パーセントエンコードなし（Q-201）。
    # `{route}` の値は設計に無く、設定（`R60_URL_ROUTE`）で与える（差異登記 #4）。
    stf_kbn = payload.stf_kbn if payload.stf_kbn is not None else ""
    gmn_id = payload.gmn_id if payload.gmn_id is not None else ""
    kgn_kbn = payload.kgn_kbn if payload.kgn_kbn is not None else ""
    url = (
        f"{settings.url_scheme}://{settings.url_host}:{settings.url_port}/"
        f"{settings.url_context}/{settings.url_route}"
        f"?stfCd={url_stf_cd}&stfKbn={stf_kbn}&gmnId={gmn_id}&kgnKbn={kgn_kbn}"
    )

    # ステップ7: 150 桁超は E-210（`1`／`R60W0001`・HTTP 200）。**切捨てない**（B-21）。
    if len(url) > _URL_MAX_LENGTH:
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60W0001", "kgn_kbn": kgn_kbn})
        return _respond(
            GenerateUrlResponse(
                error_code="1",
                error_detail_code="R60W0001",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60W0001", logger=logger
                ),
            )
        )

    # ステップ8: 150 桁以内なら I-310 に返す（表示幅 120 桁・超過分は表示上スクロールはクライアント）。
    log_extra: dict[str, str] = {"screen_id": _SCREEN_ID, "result_code": "0", "kgn_kbn": kgn_kbn}
    if masked_stf_cd is not None:
        log_extra["stf_cd_masked"] = masked_stf_cd
    logger.info("access", extra=log_extra)

    return _respond(GenerateUrlResponse(error_code="0", url=url))
