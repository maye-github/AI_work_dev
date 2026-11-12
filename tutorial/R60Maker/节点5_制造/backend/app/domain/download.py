"""L-218 ダウンロード処理（CSV 生成はサーバ、保存はクライアント）。

- **最後に実行した検索条件**を用いる（画面の現在値は使わない。設計 §2.7 手順①）。
- 500 件超は E-214（1／1002）でファイルを出力しない（同 ②）。0 件も押下可（検索成功扱い）。
- CSV: UTF-8（BOM あり）・CRLF・ヘッダ行あり・一覧 5 列。**排他情報を含めない**（同 ④）。
- 5 列は SQL 4.5 の選択列（送信状態・削除区分はコード値）。一覧画面の表示名変換（4.11）は含めない。
"""
from __future__ import annotations

import csv
import io

from sqlalchemy.engine import Connection

from app.domain.preprocess import ServiceError
from app.repository import queries

# ヘッダは項目名称（設計 §3.1 I-341／I-343／I-345／I-347／I-349 の名称）を用いる。
CSV_HEADER = ["メーカーコード", "メーカー日本語名", "メーカーカナ名", "送信状態", "削除区分"]


def build_csv(conn: Connection, params) -> bytes:  # noqa: ANN001 - schemas.DownloadParams
    binds = queries.build_search_binds(
        params.maker_cd, params.maker_nm, params.include_deleted, params.shikake_mode
    )
    total_count = queries.count_maker(conn, binds)
    if total_count > queries.MAX_RESULT_ROWS:
        # ② 上限超は E-214。ファイルを出力しない。
        raise ServiceError(1, "1002", "MSG-E-002")

    rows = queries.fetch_maker_all(conn, binds)  # ③ 明細（全件・頁送りなし）

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_HEADER)
    for row in rows:
        writer.writerow(
            [
                row["maker_cd"],
                row["maker_nm"] or "",
                row["maker_kana_nm"] or "",
                row["send_sts"],
                row["del_flg"],
            ]
        )

    # ④ UTF-8（BOM あり）。BOM はクライアントの Excel 等での文字化け防止。
    return buffer.getvalue().encode("utf-8-sig")
