"""L-217 初期値取得処理（/initEdit）。mode="1"=新規／"2"=複製／"3"=修正。

- mode="1": 全項目を空、緊急配信オフ、削除欄ブランク（設計 §2.6 手順②）。
- mode="2": D-207 から maker_cd・maker_nm・maker_kana_nm の 3 項目のみ引き継ぎ（同 ③）。
- mode="3": maker_cd で現在値と last_update_datetime・rev_no を取得（削除済みも取得。SQL 4.6）。
  メーカーコードは変更不可。削除済みは削除チェック固定・登録ボタン非活性（表示は L-221）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.engine import Connection

from app.repository import queries


@dataclass
class InitEditResult:
    mode: str
    maker_cd: str | None = None
    maker_nm: str | None = None
    maker_kana_nm: str | None = None
    emergency_dispatch: bool = False
    delete_flg: str | None = None
    last_update_datetime: datetime | None = None
    rev_no: int | None = None


def init_edit(conn: Connection, params) -> InitEditResult:  # noqa: ANN001 - schemas.InitEditParams
    if params.mode == "1":
        # ② 全項目空・緊急配信オフ・削除欄ブランク
        return InitEditResult(mode="1")

    if params.mode == "2":
        # ③ 3 項目のみ引き継ぎ。D-207 から取得する（SQL 4.6）。
        row = queries.fetch_maker_for_edit(conn, params.maker_cd)
        return InitEditResult(
            mode="2",
            maker_cd=params.maker_cd,
            maker_nm=None if row is None else row["maker_nm"],
            maker_kana_nm=None if row is None else row["maker_kana_nm"],
            emergency_dispatch=False,
            delete_flg=None,
        )

    # ④ mode="3" 現在値と排他情報（削除済みも取得）
    row = queries.fetch_maker_for_edit(conn, params.maker_cd)
    # Q-328: 対象が存在しない場合の分岐は上流設計に明文が無い。新たな業務エラーを発明しない。
    #        明示分岐を置かず、汎用例外処理（E-223）に委ねる。ノード3 へ戻すかは人が裁定する。
    return InitEditResult(
        mode="3",
        maker_cd=row["maker_cd"],
        maker_nm=row["maker_nm"],
        maker_kana_nm=row["maker_kana_nm"],
        emergency_dispatch=False,
        delete_flg=row["del_flg"],
        last_update_datetime=row["last_update_datetime"],
        rev_no=row["rev_no"],
    )
