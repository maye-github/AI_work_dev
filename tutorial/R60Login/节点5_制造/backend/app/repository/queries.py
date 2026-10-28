"""SQL-1〜SQL-6 の実行（05 §5）。

* SQL は明示手書き。**値はすべて `:name` の名前付きバインド**で受け、f-string 等で連結しない（05 §5.1 #1）。
* 列名・表名を利用者入力から組み立てない。本画面に動的ソートは無いため `ALLOWED_SORT_FIELDS` 白名单は
  適用対象が存在しない（05 §5.1 #2）。
* **SELECT のみ。** INSERT／UPDATE／DELETE を持たない（05 §3.1・§5.1 #3）。
* 物理名は大文字（工程04 §2.1）。接続は oracledb（Thin）。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

# --- 裁定値（SQL の外で持つ。実値を SQL 本文へ書かない・05 §5.1 #5）-------------------------
DEL_FLG_NOT_DELETED = "0"  # 裁定 Q-227／Q-234（del_flg: 0=未削除）
VALID_FLG_ON = "1"  # 裁定 Q-234（valid_flg: 1=有効）
OPERATION_FLG_ON = "1"  # 裁定 Q-234（operation_flg: 1=有効）

# 05 §5.7 の 0 件時の代替表示（C・v1.0.2 で確定）。上流 §9.1 の E-204／E-208 と同じ文言。
FALLBACK_SYSTEM_ERROR_MESSAGE = "システムエラーが発生しました。画面を再読み込みしてください。"

# --- SQL-1 稼働判定（L-201。呼出元 3 端点の先頭） -----------------------------------------
SQL_1_OPERATION_FLG = text(
    """
    SELECT operation_flg
      FROM SYS_CMN_TBL
     WHERE cmn_key = :operation_key
    """
)

# --- SQL-2 画面候補の取得（L-202。有効行のみ・表示順の昇順。全社共通） ----------------------
SQL_2_PAGE_CANDIDATES = text(
    """
    SELECT gmn_id,
           gmn_nm
      FROM GMN_MST
     WHERE valid_flg = :valid
     ORDER BY disp_order, gmn_id
    """
)

# --- SQL-3 社員検証（L-203。未削除の該当行の有無だけを見る） --------------------------------
SQL_3_EMPLOYEE_EXISTS = text(
    """
    SELECT 1
      FROM STF_MST
     WHERE stf_cd  = :stf_cd
       AND del_flg = :not_deleted
    """
)

# --- SQL-4 社員情報の取得（L-203。I-316 の 6 項目。内部結合） -------------------------------
SQL_4_USER_INFO = text(
    """
    SELECT s.stf_cd,
           s.stf_nm,
           o.cmp_cd,
           o.cmp_nm,
           o.jig_cd,
           o.jig_nm
      FROM STF_MST s
      JOIN ORG_JIG_MST o
        ON o.cmp_cd = s.cmp_cd
       AND o.jig_cd = s.jig_cd
     WHERE s.stf_cd  = :stf_cd
       AND s.del_flg = :not_deleted
    """
)

# --- SQL-5 管理情報の取得（L-203。I-317 の 5 項目。供給元は社員マスタ・裁定 Q-229） ---------
SQL_5_MNG_INFO = text(
    """
    SELECT scmp_cd,
           sjig_cd,
           ji_kjo_ksn_flg,
           ta_kjo_ksn_flg,
           login_acs_kais
      FROM STF_MST
     WHERE stf_cd  = :stf_cd
       AND del_flg = :not_deleted
    """
)

# --- SQL-6 エラー文言の取得（サーバのみ実行・05 §5.7） ---------------------------------------
SQL_6_ERROR_MESSAGE = text(
    """
    SELECT msg_txt
      FROM CD_MSG_MST
     WHERE msg_id = :error_detail_code
    """
)


def fetch_operation_flg(conn: Connection, *, operation_key: str) -> Any:
    """SQL-1。0 件は None（＝不可。0 件を「可」と読み替えない・05 §5.2）。"""
    row = conn.execute(SQL_1_OPERATION_FLG, {"operation_key": operation_key}).first()
    return None if row is None else row[0]


def fetch_page_candidates(conn: Connection, *, valid: str) -> list[tuple[Any, Any]]:
    """SQL-2。件数はマスタの有効行数に従う（59 行を固定値として扱わない・Q-211）。"""
    rows = conn.execute(SQL_2_PAGE_CANDIDATES, {"valid": valid}).all()
    return [(row[0], row[1]) for row in rows]


def employee_exists(conn: Connection, *, stf_cd: str, not_deleted: str) -> bool:
    """SQL-3。`stf_cd` は PK のため最大 1 行。件数の集計は不要（05 §5.4）。"""
    row = conn.execute(SQL_3_EMPLOYEE_EXISTS, {"stf_cd": stf_cd, "not_deleted": not_deleted}).first()
    return row is not None


def fetch_user_info(conn: Connection, *, stf_cd: str, not_deleted: str) -> tuple[Any, ...] | None:
    """SQL-4。結合先が無い行は返らない（0 件は E-201 と同じ扱い・裁定 Q-237）。"""
    row = conn.execute(SQL_4_USER_INFO, {"stf_cd": stf_cd, "not_deleted": not_deleted}).first()
    return None if row is None else tuple(row)


def fetch_mng_info(conn: Connection, *, stf_cd: str, not_deleted: str) -> tuple[Any, ...] | None:
    """SQL-5。フラグ 2 列は 'Y'/'N' をそのまま扱う（変換しない・裁定 Q-234）。"""
    row = conn.execute(SQL_5_MNG_INFO, {"stf_cd": stf_cd, "not_deleted": not_deleted}).first()
    return None if row is None else tuple(row)


def fetch_error_message(conn: Connection, *, error_detail_code: str) -> str | None:
    """SQL-6。戻りは `msg_txt` 0〜1 行。値はバインドで渡し、本文へ連結しない。"""
    row = conn.execute(SQL_6_ERROR_MESSAGE, {"error_detail_code": error_detail_code}).first()
    return None if row is None else row[0]


def resolve_error_message(engine: Engine, *, error_detail_code: str, logger: logging.Logger) -> str:
    """エラー応答に載せる利用者向け文言を SQL-6 で取得する（サーバ実行・05 §5.7）。

    0 件（又は取得失敗）のときは、コード文字列を利用者に見せず、汎用のシステムエラー文言を返し、
    `errorDetailCode` と `msg_id` を運用ログへ記録する（C・05 §5.7）。
    """
    message: str | None = None
    try:
        with engine.connect() as conn:
            message = fetch_error_message(conn, error_detail_code=error_detail_code)
    except Exception:
        message = None  # 取得失敗も 0 件と同じ扱い（代替表示）
    if message:
        return str(message)
    logger.warning(
        "error_message_missing",
        extra={"result_code": error_detail_code, "msg_id": error_detail_code},
    )
    return FALLBACK_SYSTEM_ERROR_MESSAGE
