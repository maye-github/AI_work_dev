"""L-219 削除処理（/delete。MKR03 のみ）。

手順（設計 §2.8）:
  ③ 被参照チェック（ReferenceChecker.check。対象 D-208・D-209。削除済み参照元は数えない）
  ④ 想定外の結果 → E-218（9／9101）。参照件数を 0 として扱わない
  ⑤ 排他（last_update_datetime と rev_no の両方の一致）→ 不一致は E-217（1／2003）
  ⑥ 論理削除（del_flg=1。物理削除しない）
  ⑦ コミット確定後に緊急配信があれば非同期起動（起動は api 側で commit 後に行う）
完了後の再検索（⑧）は api 側で最後の検索条件により 1 頁目を実行する。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.engine import Connection

from app.domain.preprocess import ServiceError
from app.ports import PortNotConnected
from app.repository import queries


@dataclass
class DeleteResult:
    # 緊急配信オンなら commit 後に非同期起動するための受付内容。オフなら None。
    dispatch_payload: dict | None = None


def delete(
    conn: Connection,
    params,  # noqa: ANN001 - schemas.DeleteParams
    *,
    reference_checker,
    upd_user: str,
    now: datetime,
) -> DeleteResult:
    # ③ 被参照チェック（共通部品に委ねる。再実装しない）
    try:
        result = reference_checker.check(params.maker_cd)
    except PortNotConnected as exc:  # ④ 未接続＝想定外扱い（E-218）
        raise ServiceError(9, "9101", None) from exc
    if result.unexpected:  # ④ 想定外（E-218）
        raise ServiceError(9, "9101", None)
    if result.referenced:  # 参照あり（E-216）
        raise ServiceError(1, "2002", "MSG-E-004")

    # ⑤ 排他キー欠落は比較不能のため不一致扱い（E-217）
    if params.last_update_datetime is None or params.rev_no is None:
        raise ServiceError(1, "2003", "MSG-E-005")

    # ⑤⑥ 排他 WHERE ＋ 論理削除を 1 文で実行（SQL 4.7）。rowcount 0 は不一致。
    affected = queries.logical_delete_maker(
        conn,
        maker_cd=params.maker_cd,
        new_last_update_datetime=now,
        last_update_datetime=params.last_update_datetime,
        rev_no=params.rev_no,
        upd_user=upd_user,
    )
    if affected == 0:
        raise ServiceError(1, "2003", "MSG-E-005")

    # ⑦ 緊急配信オンなら commit 後に非同期起動（api 側）。オン・オフの判定は押下時点の画面値。
    payload = (
        {"makerCd": params.maker_cd, "action": "delete"}
        if params.emergency_dispatch
        else None
    )
    return DeleteResult(dispatch_payload=payload)
