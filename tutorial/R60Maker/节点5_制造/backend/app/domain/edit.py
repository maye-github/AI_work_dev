"""L-220 登録更新処理（/edit。MKR02 以上）。

新規・複製（mode="1"/"2"）: 入力チェック（前処理）→ 変更なし判定（複製のみ）→ 重複判定（削除済みも存在とみなす）
  → INSERT（登録区分は仕掛=1）→ commit 後に緊急配信を非同期起動。
修正（mode="3"）: 入力チェック（前処理）→ 変更なし判定 → 削除オン時のみ被参照チェック
  → 排他（両キーの一致）→ UPDATE（削除オンなら論理削除）→ commit 後に緊急配信を非同期起動。
一意制約はメーカーコードのみ。名称の重複は許容する（設計 §2.9）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.engine import Connection

from app.config import INITIAL_SEND_STS
from app.domain.preprocess import ServiceError
from app.ports import PortNotConnected
from app.repository import queries


@dataclass
class EditResult:
    msg_id: str | None = None        # MSG-I-003（変更なし）等
    wrote: bool = False              # 登録・更新を行ったか
    dispatch_payload: dict | None = None


def _same(old: str | None, new: str | None) -> bool:
    return (old or "") == (new or "")


def edit(
    conn: Connection,
    params,  # noqa: ANN001 - schemas.EditParams
    *,
    reference_checker,
    reg_user: str,
    upd_user: str,
    now: datetime,
) -> EditResult:
    if params.mode in ("1", "2"):
        return _insert(conn, params, reg_user, upd_user, now)
    if params.mode == "3":
        return _update(conn, params, reference_checker, upd_user, now)
    # mode の妥当性は前処理（E-224）で担保済み。ここに来るのは想定外。
    raise ServiceError(1, "2005", None)


def _insert(
    conn: Connection,
    params,  # noqa: ANN001 - schemas.EditParams
    reg_user: str,
    upd_user: str,
    now: datetime,
) -> EditResult:
    # ⑤ 変更なし（複製のみ）の判定: 引き継ぎ元と 3 項目が同一なら登録しない
    if params.mode == "2":
        source = queries.fetch_maker_for_edit(conn, params.maker_cd)
        if source is not None and (
            _same(source["maker_nm"], params.maker_nm)
            and _same(source["maker_kana_nm"], params.maker_kana_nm)
        ):
            return EditResult(msg_id="MSG-I-003", wrote=False, dispatch_payload=None)

    # ⑦ キー重複（削除済みも存在とみなす）→ E-215
    if queries.exists_maker_key(conn, params.maker_cd):
        raise ServiceError(1, "2001", "MSG-E-003")

    # ⑧ INSERT（登録区分は仕掛=1。send_sts の既定値は設計 v1.0.1 で 0=未送信。SQL 4.9）
    queries.insert_maker(
        conn,
        maker_cd=params.maker_cd,
        maker_nm=params.maker_nm,
        maker_kana_nm=params.maker_kana_nm,
        send_sts=INITIAL_SEND_STS,
        reg_user=reg_user,
        reg_dat=now,
        upd_user=upd_user,
        last_update_datetime=now,
    )

    payload = (
        {"makerCd": params.maker_cd, "action": "insert"}
        if params.emergency_dispatch
        else None
    )
    return EditResult(msg_id=None, wrote=True, dispatch_payload=payload)


def _update(
    conn: Connection,
    params,  # noqa: ANN001 - schemas.EditParams
    reference_checker,
    upd_user: str,
    now: datetime,
) -> EditResult:
    current = queries.fetch_maker_for_edit(conn, params.maker_cd)
    # Q-328 と同様、対象なしの分岐は上流に明文が無い。明示分岐を置かず汎用例外（E-223）に委ねる。
    requested_del = "1" if params.delete_flg else "0"

    # ④ 変更なしの判定（名称・削除状態が現行と同一なら登録しない）
    if (
        _same(current["maker_nm"], params.maker_nm)
        and _same(current["maker_kana_nm"], params.maker_kana_nm)
        and current["del_flg"] == requested_del
    ):
        return EditResult(msg_id="MSG-I-003", wrote=False, dispatch_payload=None)

    # ⑥ 削除をオンにした場合のみ被参照チェック
    if params.delete_flg:
        try:
            result = reference_checker.check(params.maker_cd)
        except PortNotConnected as exc:
            raise ServiceError(9, "9101", None) from exc
        if result.unexpected:
            raise ServiceError(9, "9101", None)
        if result.referenced:
            raise ServiceError(1, "2002", "MSG-E-004")

    # ⑦ 排他（両キーの一致）。新規・複製では通らない分岐。
    if params.last_update_datetime is None or params.rev_no is None:
        raise ServiceError(1, "2003", "MSG-E-005")

    # ⑧ UPDATE（削除オンなら del_flg=1。SQL 4.10）。rowcount 0 は排他不一致。
    affected = queries.update_maker(
        conn,
        maker_cd=params.maker_cd,
        maker_nm=params.maker_nm,
        maker_kana_nm=params.maker_kana_nm,
        del_flg=requested_del,
        new_last_update_datetime=now,
        last_update_datetime=params.last_update_datetime,
        rev_no=params.rev_no,
        upd_user=upd_user,
    )
    if affected == 0:
        raise ServiceError(1, "2003", "MSG-E-005")

    payload = (
        {"makerCd": params.maker_cd, "action": "update"}
        if params.emergency_dispatch
        else None
    )
    return EditResult(msg_id=None, wrote=True, dispatch_payload=payload)
