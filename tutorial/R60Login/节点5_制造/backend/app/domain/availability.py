"""L-201 稼働判定（共通前処理）。05 §2.2・SQL-1。

* 呼出元は `/init`・`/login`・`/generateUrl` の**先頭**。各端点で 1 回だけ呼ぶ（キャッシュしない・C）。
* **0 件・無効値・例外はすべて「不可」**（05 §2.2 ステップ2〜4・§5.2）。0 件を「可」と読み替えない。
* 読み取りのみ。同一状態なら何度呼んでも同一結果（冪等）。
* 判定結果（I-320）は**応答に含めない**（05 §4.2 I-320）。呼出元の分岐にのみ使う。
"""

from __future__ import annotations

import logging

from sqlalchemy.engine import Engine

from app.repository.queries import OPERATION_FLG_ON, fetch_operation_flg


def check_available(engine: Engine, *, operation_key: str, logger: logging.Logger) -> bool:
    """稼働状態を判定する。`True` のときだけ呼出元は後続処理へ進む。

    不可の理由は「行が無い」「値が `1` でない」「照会が例外で終わった」の 3 種であり、
    いずれも同じ `False` に畳む（05 §2.2 分岐表 1・2 は呼出元で振り分ける）。
    """
    try:
        with engine.connect() as conn:
            operation_flg = fetch_operation_flg(conn, operation_key=operation_key)
    except Exception:
        # 05 §2.2 ステップ4: 接続の取得失敗を含む例外は「不可」に区分する。
        # 例外の内容（接続文字列等）はログへ出さない（禁⑤）。結果コードのみ記録する。
        logger.warning("operation_check_failed", extra={"screen_id": "R60Login", "result_code": "R60W0004"})
        return False

    if operation_flg is None:
        # 05 §2.2 ステップ2 / §5.2: 0 件は不可。
        return False

    # 05 §2.2 ステップ3 / §5.2: `1` のみ可。`0` も想定外の値も不可（無効値は不可）。
    return str(operation_flg) == OPERATION_FLG_ON
