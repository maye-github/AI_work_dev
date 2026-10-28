"""`POST /R60Login/login`（イベント２ ログイン・イベント３ メニューが共用）。L-201 → L-203。05 §2.4。

* **I-313（`encryptedStfCd`）のみを使用する。** `stfKbn`（I-304）・`gmnId`（I-306）・`kgnKbn`（I-307）は
  同じ要求に載るが、**受信するだけで検証も保存もせず無視する**（05 §4.2・Q-212）。
* E-201／E-207（該当なし）は **`errorCode` のみ**を返す（`errorDetailCode` も文言も載せない・裁定 Q-235）。
* エラー文言はサーバが SQL-6 で取得し、応答の `errorMessage`（`I-321`・台帳登録済み）に載せる（05 §5.7）。
  E-201／E-207 はこの限りでない（クライアントが固定文言を表示する）。
* 成功時は **Session を生成**し、識別子のみを HttpOnly Cookie で返す（05 §2.4 ステップ6・§8.2）。
  保持先はプロセス内辞書（OQ-05 の裁定。複数インスタンスでは共有されない）。
* **試行ロック（05 §2.4.1・v1.0.5）**：復号の後・社員照会の前にロックを判定する。数えるのは
  社員照会 0 件（E-201）だけで、5 回でロック・10 分で自動解除。**ロック中の応答は E-201 と同じ形式**で、
  ロック中であることを利用者へ示さない。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.domain.availability import check_available
from app.domain.login_lockout import LoginLockout
from app.domain.session_store import SESSION_COOKIE_NAME, SessionStore
from app.domain.stf_cd_cipher import StfCdCipherError, decrypt_stf_cd, today_jst_yyyymmdd
from app.repository.queries import (
    DEL_FLG_NOT_DELETED,
    employee_exists,
    fetch_mng_info,
    fetch_user_info,
    resolve_error_message,
)
from app.schemas import LoginRequest, LoginResponse, MngInfo, UserInfo

router = APIRouter()

_SCREEN_ID = "R60Login"


def _respond(
    model: LoginResponse,
    *,
    status_code: int = 200,
    session_token: str | None = None,
    secure: bool = False,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content=model.model_dump(by_alias=True, mode="json", exclude_none=True),
    )
    if session_token is not None:
        # 05 §8.2: **識別子のみ**を HttpOnly Cookie で持たせる（JS から読ませない）。
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )
    return response


def _mask_stf_cd(stf_cd: str) -> str:
    """工程04 §6.2: 先頭 1 桁と末尾 1 桁を残し、中間を `*` に置換する（氏名は出さない）。"""
    if len(stf_cd) <= 2:
        return "*" * len(stf_cd)
    return stf_cd[0] + "*" * (len(stf_cd) - 2) + stf_cd[-1]


@router.post("/R60Login/login")
async def login(payload: LoginRequest, request: Request) -> JSONResponse:
    settings = request.app.state.settings
    engine = request.app.state.engine
    logger: logging.Logger = request.app.state.logger

    # L-201 稼働判定（先頭・1 回だけ）。不可なら E-203（HTTP 403）。
    if not check_available(engine, operation_key=settings.operation_key, logger=logger):
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60W0004"})
        return _respond(
            LoginResponse(
                error_code="1",
                error_detail_code="R60W0004",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60W0004", logger=logger
                ),
            ),
            status_code=403,
        )

    # L-203 ステップ2: I-313 を復号する（L-206）。日付はサーバの JST（05 §2.7・§8.4）。
    key_date = today_jst_yyyymmdd()
    try:
        stf_cd = decrypt_stf_cd(payload.encrypted_stf_cd, key_date)
    except StfCdCipherError:
        # 分岐 2: 復号失敗は E-205（`1`／`R60W0003`・HTTP 200）。
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "R60W0003"})
        return _respond(
            LoginResponse(
                error_code="1",
                error_detail_code="R60W0003",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60W0003", logger=logger
                ),
            )
        )

    # NOTE: `payload.stf_kbn` / `payload.gmn_id` / `payload.kgn_kbn` はここで**使わない**（Q-212）。

    # ステップ3（前段）: 試行ロックを判定する（05 §2.4.1）。キーは復号済み社員コードのハッシュ。
    lockout: LoginLockout = request.app.state.login_lockout
    lock_key = lockout.key_for(stf_cd)
    if lockout.is_locked(lock_key):
        # ロック中は**照会しない**。応答は E-201 と同じ形式（`1` のみ）で、ロック中であることを示さない。
        logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "1"})
        return _respond(LoginResponse(error_code="1"))

    try:
        with engine.connect() as conn:
            # ステップ3: 未削除の該当行の有無だけを見る（SQL-3）。0 件は E-201（応答は E-207 の形式）。
            if not employee_exists(conn, stf_cd=stf_cd, not_deleted=DEL_FLG_NOT_DELETED):
                # 認証失敗として計数する（§2.4.1）。ロックを成立させた 5 回目だけ運用ログを 1 件出す。
                if lockout.record_failure(lock_key):
                    logger.warning("login_locked", extra={"screen_id": _SCREEN_ID, "result_code": "1"})
                logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "1"})
                return _respond(LoginResponse(error_code="1"))

            # ステップ4: I-316 の 6 項目（SQL-4・内部結合）。
            user_row = fetch_user_info(conn, stf_cd=stf_cd, not_deleted=DEL_FLG_NOT_DELETED)
            if user_row is None:
                # 分岐 4 / B-42: SQL-4 が 0 件（結合先なし）は E-201 と同じ扱い。運用ログに 1 件記録する。
                logger.warning(
                    "master_inconsistency",
                    extra={"screen_id": _SCREEN_ID, "result_code": "1"},
                )
                logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "1"})
                return _respond(LoginResponse(error_code="1"))

            # ステップ5: I-317 の 5 項目（SQL-5。供給元は社員マスタ・裁定 Q-229）。
            mng_row = fetch_mng_info(conn, stf_cd=stf_cd, not_deleted=DEL_FLG_NOT_DELETED)
            if mng_row is None:
                # 設計に 0 件の分岐が無い（05 §2.4 ステップ5）。SQL-4 が 1 行返した後に同一表・同一条件の
                # SQL-5 が 0 件になるのはマスタ不整合であり、**E-201 と同じ扱い**とする（裁定 Q-237 と同旨）。
                logger.warning(
                    "master_inconsistency",
                    extra={"screen_id": _SCREEN_ID, "result_code": "1", "error_type": "SQL-5_EMPTY"},
                )
                logger.info("access", extra={"screen_id": _SCREEN_ID, "result_code": "1"})
                return _respond(LoginResponse(error_code="1"))
            scmp_cd, sjig_cd, ji_kjo_ksn_flg, ta_kjo_ksn_flg, login_acs_kais = mng_row

            user_info = UserInfo(
                stf_cd=str(user_row[0]),
                stf_nm=str(user_row[1]),
                cmp_cd=str(user_row[2]),
                cmp_nm=str(user_row[3]),
                jig_cd=str(user_row[4]),
                jig_nm=str(user_row[5]),
            )
            mng_info = MngInfo(
                scmp_cd=None if scmp_cd is None else str(scmp_cd),
                sjig_cd=None if sjig_cd is None else str(sjig_cd),
                # フラグ 2 列は `'Y'`／`'N'` をそのまま扱う（変換しない・裁定 Q-234）。
                ji_kjo_ksn_flg=None if ji_kjo_ksn_flg is None else str(ji_kjo_ksn_flg),
                ta_kjo_ksn_flg=None if ta_kjo_ksn_flg is None else str(ta_kjo_ksn_flg),
                login_acs_kais=int(login_acs_kais),
            )

            # ステップ6: Session を生成する（05 §2.4・§8.2）。保持するのは I-316（6）＋ I-317（5）＝ 11 項目のみ。
            # 保持先はプロセス内辞書（OQ-05 の裁定）。**識別子のみ**を HttpOnly Cookie で返す。
            session_store: SessionStore = request.app.state.session_store
            session_token = session_store.create(
                {**user_info.model_dump(), **mng_info.model_dump()}
            )
            # §2.4.1「成功時の扱い」: 認証が成立したので当該社員コードの計数を 0 に戻す。
            lockout.reset(lock_key)

            # ステップ7: 正常応答（I-316・I-317）。遷移先の解決はクライアント（L-204）。
            logger.info(
                "access",
                extra={
                    "screen_id": _SCREEN_ID,
                    "result_code": "0",
                    "stf_cd_masked": _mask_stf_cd(stf_cd),
                },
            )
            return _respond(
                LoginResponse(error_code="0", user_info=user_info, mng_info=mng_info),
                session_token=session_token,
                secure=settings.url_scheme == "https",
            )
    except Exception:
        # 分岐 5: その他の例外は E-208（`2`／`R60E9999`・HTTP 200）。
        # 例外の内容は利用者向け文言へ出さない（05 §8.1・§9.2）。結果コードのみ記録する。
        logger.error("system_error", extra={"screen_id": _SCREEN_ID, "result_code": "R60E9999"})
        return _respond(
            LoginResponse(
                error_code="2",
                error_detail_code="R60E9999",
                error_message=resolve_error_message(
                    engine, error_detail_code="R60E9999", logger=logger
                ),
            )
        )
