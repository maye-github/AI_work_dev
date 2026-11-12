"""L-214 検索処理 と L-215 ページャ制御処理（ページャは /search へ委譲する）。

- 条件は AND 結合、空条件は除外。I-332 削除含む・I-334 仕掛モードを反映（設計 §2.3）。
- 0 件は E-213（1／1001・MSG-E-001）を返しつつ**検索成功として扱う**（明細のみ空）。
- 500 件超は E-214（1／1002・MSG-E-002）で明細を返さない。ちょうど 500 件は許容。
- 並び順は削除区分（未削除先）→メーカーコード昇順。白名单指定時も第 1 キーは del_flg を維持。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.engine import Connection

from app.domain.preprocess import ServiceError
from app.repository import queries


@dataclass
class SearchResult:
    error_code: int
    error_id: str
    msg_id: str | None
    items: list[dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page_no: int = 1
    total_pages: int = 0
    page_size: int = 20


def _to_items(
    rows: list[dict[str, Any]],
    code_map: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in rows:
        items.append(
            {
                "maker_cd": row["maker_cd"],
                "maker_nm": row["maker_nm"],
                "maker_kana_nm": row["maker_kana_nm"],
                # コードを直接返さず名称を返す（I-347／I-349。SQL 4.11）
                "send_sts": code_map.get((queries.CODE_KIND_SEND_STS, row["send_sts"])),
                "del_flg": code_map.get((queries.CODE_KIND_DEL_FLG, row["del_flg"])),
            }
        )
    return items


def search(
    conn: Connection,
    params,  # noqa: ANN001 - schemas.SearchParams
) -> SearchResult:
    binds = queries.build_search_binds(
        params.maker_cd, params.maker_nm, params.include_deleted, params.shikake_mode
    )
    total_count = queries.count_maker(conn, binds)  # ⑤

    page_no = max(params.page_no, 1)
    page_size = params.page_size
    total_pages = math.ceil(total_count / page_size) if page_size else 0

    if total_count == 0:
        # ⑥ 0 件は E-213。検索成功として扱う（項目の活性はクライアント側で維持）。
        return SearchResult(
            error_code=1,
            error_id="1001",
            msg_id="MSG-E-001",
            items=[],
            total_count=0,
            page_no=page_no,
            total_pages=0,
            page_size=page_size,
        )

    if total_count > queries.MAX_RESULT_ROWS:
        # ⑦ 上限超は E-214。明細・CSV を出力しない。
        raise ServiceError(1, "1002", "MSG-E-002")

    offset = (page_no - 1) * page_size
    rows = queries.fetch_maker_page(conn, binds, params.sort_field, offset, page_size)  # ⑧
    code_map = queries.fetch_code_values(conn)
    items = _to_items(rows, code_map)

    return SearchResult(
        error_code=0,
        error_id="0000",
        msg_id=None,
        items=items,
        total_count=total_count,
        page_no=page_no,
        total_pages=total_pages,
        page_size=page_size,
    )
