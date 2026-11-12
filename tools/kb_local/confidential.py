"""`client_only`（`conf_level: 40`）の知識が対外文書へ漏れていないかを見る。

なぜ要るか
----------
`conf_level` の絞り込み（`d.conf_level <= :user_level`）は**検索**には効くが、
**人が手でコピーして顧客向け資料に貼る**経路は止められない。
構築ガイド §4.7 の「`client_only` は生成对外提交物で引用禁止」を、
検索とは別の入口で担保するのがこのモジュールである。

やること
--------
対外に出そうなファイルを受け取り、L40 の文書本文と**長い一致**があるかを調べる。
断定はしない——一致箇所を並べるだけである。最終判断は人（紅線③）。

なぜ「長い一致」か
------------------
短い語句（「登録」「画面」）はどこにでも出るので、一致を見ても意味がない。
**20 文字以上の連続一致**だけを拾う。これは「コピーした」に近い挙動であり、
偶然の一致はほぼ起きない。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_MIN_LEN = 20


def shingles(text: str, n: int = DEFAULT_MIN_LEN) -> set[str]:
    """改行・空白を潰した本文から、n 文字の連続部分を集合で返す。"""
    flat = "".join(text.split())
    if len(flat) < n:
        return {flat} if flat else set()
    return {flat[i : i + n] for i in range(len(flat) - n + 1)}


def find_copies(target_text: str, sources: dict[str, str],
                n: int = DEFAULT_MIN_LEN) -> list[dict]:
    """`target_text` の中で `sources` と n 文字以上一致する箇所を返す。

    Returns:
        `[{"source": 文書ID, "count": 一致した断片数, "sample": 例}]`
    """
    target = shingles(target_text, n)
    if not target:
        return []
    out: list[dict] = []
    for doc_id, text in sources.items():
        hits = target & shingles(text, n)
        if hits:
            sample = sorted(hits)[0]
            out.append({"source": doc_id, "count": len(hits), "sample": sample})
    out.sort(key=lambda item: item["count"], reverse=True)
    return out


def load_confidential(conn: sqlite3.Connection, repo_root: Path,
                      threshold: int = 40) -> dict[str, str]:
    """`conf_level >= threshold` の文書本文を `{doc_id: text}` で返す。"""
    rows = conn.execute(
        "SELECT doc_id, path FROM kb_doc WHERE conf_level >= ?", (threshold,)
    ).fetchall()
    out: dict[str, str] = {}
    for doc_id, rel in rows:
        path = repo_root / str(rel)
        try:
            out[str(doc_id)] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return out
