"""SQL 4.1〜4.11 の実行。SQLAlchemy Core の `text()` に `:name` バインドで発行する。

- 値は必ず名前付きバインド（`:maker_cd` 等）で受け、**f-string で値を連結しない**（禁③・設計 §4）。
- 発行するのは設計 §4 の SELECT／INSERT／UPDATE のみ。**物理削除は行わない**（論理削除 del_flg）。
- 物理型・物理方言・物理行識別子は**本層に閉じ込める**（Q-326・設計の論理型は書き換えない）:
    文字列 VARCHAR2(n CHAR) / 数値 NUMBER / 日時 DATE / 行識別子 ROWID / 頁送り OFFSET/FETCH。
    NLS_DATE_FORMAT は顧客運用標準に従う（日時は typed bind で渡し、文字列連結しない）。
- 表名・列名は設計 §1 の物理名（AI 素案 Q-308b）をそのまま用いる。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

# 動的ソートの白名单（設計 §4.4）。追加は設計変更（CR）。識別子は値ではないため :BIND 不可。
ALLOWED_SORT_FIELDS = {"MAKER_CD", "MAKER_NM"}
ALLOWED_PAGE_SIZES = {10, 20, 50, 100}
MAX_RESULT_ROWS = 500

# D-210 コード区分の実値（設計 v1.0.1 で確定）。SQL 4.11 の :cd_kbn_* はこの値をバインドする。
CODE_KIND_SEND_STS = "SEND_STS"
CODE_KIND_DEL_FLG = "DEL_FLG"


# ---------------------------------------------------------------------------
# 4.1 前処理（L-212）権限コードの取得
# ---------------------------------------------------------------------------
def fetch_auth_cd(conn: Connection, user_id: str) -> str | None:
    sql = text(
        """
        SELECT auth_cd
          FROM AUTH_TBL
         WHERE user_id = :user_id
        """
    )
    row = conn.execute(sql, {"user_id": user_id}).first()
    return None if row is None else row[0]


# ---------------------------------------------------------------------------
# 4.2 初期化処理（L-213）メッセージ情報の取得
# ---------------------------------------------------------------------------
def fetch_message(conn: Connection, msg_id: str) -> dict[str, Any] | None:
    sql = text(
        """
        SELECT msg_id, msg_kind, msg_txt
          FROM MSG_TBL
         WHERE msg_id = :msg_id
        """
    )
    row = conn.execute(sql, {"msg_id": msg_id}).mappings().first()
    return None if row is None else dict(row)


# ---------------------------------------------------------------------------
# 検索条件のバインド生成（4.3／4.4／4.5 で共通）
# ---------------------------------------------------------------------------
def build_search_binds(
    maker_cd: str | None,
    maker_nm: str | None,
    include_deleted: bool,
    shikake_mode: bool,
) -> dict[str, Any]:
    """設計 §4.3 の `OR :x IS NULL` 形へ空条件を写す。

    - maker_cd は前方一致、maker_nm は中間一致。空は None を渡し条件から除外する。
    - include_deleted: オンで OR 節を真にする（del_flg 条件を無効化）。
    - shikake_mode: オンで reg_kbn=1 のみ。オフで OR 節を真にする。
    """
    return {
        "maker_cd_prefix": f"{maker_cd}%" if maker_cd else None,
        "maker_nm_partial": f"%{maker_nm}%" if maker_nm else None,
        "not_deleted": "0",
        "include_deleted": 1 if include_deleted else 0,
        "include_deleted_val": 1,
        "shikake_kbn": "1",
        "shikake_mode": 0 if shikake_mode else 1,
        "shikake_off": 1,
    }


_COUNT_SQL = """
    SELECT COUNT(*)
      FROM MKR_TBL
     WHERE (maker_cd LIKE :maker_cd_prefix OR :maker_cd_prefix IS NULL)
       AND (maker_nm LIKE :maker_nm_partial OR :maker_nm_partial IS NULL)
       AND (del_flg = :not_deleted OR :include_deleted = :include_deleted_val)
       AND (reg_kbn = :shikake_kbn OR :shikake_mode = :shikake_off)
"""

_LIST_SELECT = """
    SELECT maker_cd, maker_nm, maker_kana_nm, send_sts, del_flg
      FROM MKR_TBL
     WHERE (maker_cd LIKE :maker_cd_prefix OR :maker_cd_prefix IS NULL)
       AND (maker_nm LIKE :maker_nm_partial OR :maker_nm_partial IS NULL)
       AND (del_flg = :not_deleted OR :include_deleted = :include_deleted_val)
       AND (reg_kbn = :shikake_kbn OR :shikake_mode = :shikake_off)
"""


def _order_by(sort_field: str | None) -> str:
    """白名单ヒット時のみ項目名を採用。白名单外・未指定は固定ソートへフォールバック。

    白名单指定時も第 1 キーは del_flg（未削除を先）を維持する。安定順序のため末尾に ROWID（Q-326）。
    """
    if sort_field and sort_field.upper() in ALLOWED_SORT_FIELDS:
        # 列名は白名单で担保する（値ではないため bind 不可）。利用者入力をそのまま連結しない。
        return f" ORDER BY del_flg, {sort_field.upper()}, ROWID"
    return " ORDER BY del_flg, maker_cd, ROWID"


# ---------------------------------------------------------------------------
# 4.3 検索処理（L-214）総件数の取得
# ---------------------------------------------------------------------------
def count_maker(conn: Connection, binds: dict[str, Any]) -> int:
    row = conn.execute(text(_COUNT_SQL), binds).first()
    return 0 if row is None else int(row[0])


# ---------------------------------------------------------------------------
# 4.4 検索処理（L-214）一覧の取得
# ---------------------------------------------------------------------------
def fetch_maker_page(
    conn: Connection,
    binds: dict[str, Any],
    sort_field: str | None,
    offset: int,
    page_size: int,
) -> list[dict[str, Any]]:
    sql = text(
        _LIST_SELECT
        + _order_by(sort_field)
        + " OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY"
    )
    params = dict(binds)
    params["offset"] = offset
    params["page_size"] = page_size
    return [dict(r) for r in conn.execute(sql, params).mappings().all()]


# ---------------------------------------------------------------------------
# 4.5 ダウンロード処理（L-218）一覧の取得（全件・頁送りなし）
# ---------------------------------------------------------------------------
def fetch_maker_all(conn: Connection, binds: dict[str, Any]) -> list[dict[str, Any]]:
    sql = text(_LIST_SELECT + " ORDER BY del_flg, maker_cd, ROWID")
    return [dict(r) for r in conn.execute(sql, binds).mappings().all()]


# ---------------------------------------------------------------------------
# 4.6 初期値取得処理（L-217）mode=2/3 現在値と排他情報の取得（削除済みも取得）
# ---------------------------------------------------------------------------
def fetch_maker_for_edit(conn: Connection, maker_cd: str) -> dict[str, Any] | None:
    sql = text(
        """
        SELECT maker_cd, maker_nm, maker_kana_nm, send_sts, del_flg,
               last_update_datetime, rev_no
          FROM MKR_TBL
         WHERE maker_cd = :maker_cd
        """
    )
    row = conn.execute(sql, {"maker_cd": maker_cd}).mappings().first()
    return None if row is None else dict(row)


# ---------------------------------------------------------------------------
# 4.7 削除処理（L-219）論理削除（排他: last_update_datetime と rev_no の両方の一致）
# ---------------------------------------------------------------------------
def logical_delete_maker(
    conn: Connection,
    maker_cd: str,
    new_last_update_datetime: datetime,
    last_update_datetime: datetime,
    rev_no: int,
    upd_user: str,
) -> int:
    sql = text(
        """
        UPDATE MKR_TBL
           SET del_flg = :deleted,
               last_update_datetime = :new_last_update_datetime,
               rev_no = rev_no + 1,
               upd_user = :upd_user
         WHERE maker_cd = :maker_cd
           AND last_update_datetime = :last_update_datetime
           AND rev_no = :rev_no
        """
    )
    result = conn.execute(
        sql,
        {
            "deleted": "1",
            "new_last_update_datetime": new_last_update_datetime,
            "upd_user": upd_user,
            "maker_cd": maker_cd,
            "last_update_datetime": last_update_datetime,
            "rev_no": rev_no,
        },
    )
    return result.rowcount


# ---------------------------------------------------------------------------
# 4.8 登録更新処理（L-220）キー重複の判定（削除済みも存在とみなす）
# ---------------------------------------------------------------------------
def exists_maker_key(conn: Connection, maker_cd: str) -> bool:
    sql = text(
        """
        SELECT 1
          FROM MKR_TBL
         WHERE maker_cd = :maker_cd
        """
    )
    return conn.execute(sql, {"maker_cd": maker_cd}).first() is not None


# ---------------------------------------------------------------------------
# 4.9 登録更新処理（L-220）INSERT（新規・複製。登録区分は仕掛=1）
# ---------------------------------------------------------------------------
def insert_maker(
    conn: Connection,
    *,
    maker_cd: str,
    maker_nm: str | None,
    maker_kana_nm: str | None,
    send_sts: str,
    reg_user: str,
    reg_dat: datetime,
    upd_user: str,
    last_update_datetime: datetime,
    initial_rev_no: int = 1,
) -> None:
    sql = text(
        """
        INSERT INTO MKR_TBL (
          maker_cd, maker_nm, maker_kana_nm, send_sts, del_flg, reg_kbn,
          reg_user, reg_dat, upd_user, last_update_datetime, rev_no
        ) VALUES (
          :maker_cd, :maker_nm, :maker_kana_nm, :send_sts, :not_deleted, :shikake_kbn,
          :reg_user, :reg_dat, :upd_user, :last_update_datetime, :initial_rev_no
        )
        """
    )
    conn.execute(
        sql,
        {
            "maker_cd": maker_cd,
            "maker_nm": maker_nm,
            "maker_kana_nm": maker_kana_nm,
            "send_sts": send_sts,
            "not_deleted": "0",
            "shikake_kbn": "1",
            "reg_user": reg_user,
            "reg_dat": reg_dat,
            "upd_user": upd_user,
            "last_update_datetime": last_update_datetime,
            "initial_rev_no": initial_rev_no,
        },
    )


# ---------------------------------------------------------------------------
# 4.10 登録更新処理（L-220）UPDATE（修正。削除オンなら論理削除。排他は両キー一致）
# ---------------------------------------------------------------------------
def update_maker(
    conn: Connection,
    *,
    maker_cd: str,
    maker_nm: str | None,
    maker_kana_nm: str | None,
    del_flg: str,
    new_last_update_datetime: datetime,
    last_update_datetime: datetime,
    rev_no: int,
    upd_user: str,
) -> int:
    sql = text(
        """
        UPDATE MKR_TBL
           SET maker_nm = :maker_nm,
               maker_kana_nm = :maker_kana_nm,
               del_flg = :del_flg,
               last_update_datetime = :new_last_update_datetime,
               rev_no = rev_no + 1,
               upd_user = :upd_user
         WHERE maker_cd = :maker_cd
           AND last_update_datetime = :last_update_datetime
           AND rev_no = :rev_no
        """
    )
    result = conn.execute(
        sql,
        {
            "maker_nm": maker_nm,
            "maker_kana_nm": maker_kana_nm,
            "del_flg": del_flg,
            "new_last_update_datetime": new_last_update_datetime,
            "upd_user": upd_user,
            "maker_cd": maker_cd,
            "last_update_datetime": last_update_datetime,
            "rev_no": rev_no,
        },
    )
    return result.rowcount


# ---------------------------------------------------------------------------
# 4.11 一覧描画（L-214）コード値の名称取得
# ---------------------------------------------------------------------------
def fetch_code_values(
    conn: Connection,
    cd_kbn_send_sts: str = CODE_KIND_SEND_STS,
    cd_kbn_del_flg: str = CODE_KIND_DEL_FLG,
) -> dict[tuple[str, str], str]:
    sql = text(
        """
        SELECT cd_kbn, cd_val, cd_nm
          FROM CD_VAL_TBL
         WHERE cd_kbn IN (:cd_kbn_send_sts, :cd_kbn_del_flg)
         ORDER BY cd_kbn, cd_val
        """
    )
    rows = conn.execute(
        sql, {"cd_kbn_send_sts": cd_kbn_send_sts, "cd_kbn_del_flg": cd_kbn_del_flg}
    ).mappings().all()
    return {(r["cd_kbn"], r["cd_val"]): r["cd_nm"] for r in rows}
