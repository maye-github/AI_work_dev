"""サーバ側 Session の保持（L-203 ステップ6・05 §8.2）。

* 識別子のみを **HttpOnly Cookie** で持たせ、保持するのは **I-316（6）＋ I-317（5）＝ 11 項目のみ**（05 §8.2）。
* **idle 30 分／絶対 8 時間**で必ず失効する（05 §8.2。水準値は `config.py` の定数）。
* 多重ログインは許可する（上流 §11）。識別子は呼出しごとに新規であり、これは**意図的な非冪等**である
  （05 §2.4「順序・冪等性」）。
* **保持先はプロセス内の辞書**とする。複数インスタンス構成では Session が共有されない
  （`docs/...` ではなく本節点の差異登記 `06_設計との差異.md` に記録。OQ-05 の裁定による）。
* 識別子・保持値は**ログへ出さない**（05 §8.1）。
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any

# 05 §8.2: 識別子のみを HttpOnly Cookie で持たせる。Cookie 名は設計に無いため本節点で定める（差異登記に記載）。
SESSION_COOKIE_NAME = "r60login.sid"


@dataclass
class _Record:
    """1 Session 分の保持値と失効判定用の時刻（秒・単調時計）。"""

    created_at: float
    last_access_at: float
    payload: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """プロセス内 Session ストア（OQ-05 の裁定＝プロセス内辞書 + TTL）。

    期限切れの項目は**参照時に遅延削除**する（背景スレッドを持たない）。したがって辞書の大きさは
    「直近の失効時間内に発行した Session 数」で抑えられる。単一プロセス前提である。
    """

    def __init__(self, *, idle_seconds: int, absolute_seconds: int) -> None:
        self._idle_seconds = idle_seconds
        self._absolute_seconds = absolute_seconds
        self._records: dict[str, _Record] = {}
        self._lock = threading.Lock()

    def create(self, payload: dict[str, Any]) -> str:
        """Session を作り、不透明な識別子を返す（呼出しごとに新規・多重ログイン可）。"""
        token = secrets.token_urlsafe(32)
        now = time.monotonic()
        with self._lock:
            self._records[token] = _Record(
                created_at=now,
                last_access_at=now,
                payload=dict(payload),
            )
        return token

    def get(self, token: str) -> dict[str, Any] | None:
        """保持値を返す。失効していれば削除して `None`。取得時に idle を延長する。"""
        if not token:
            return None
        now = time.monotonic()
        with self._lock:
            record = self._records.get(token)
            if record is None:
                return None
            if self._is_expired(record, now):
                del self._records[token]
                return None
            record.last_access_at = now
            return dict(record.payload)

    def delete(self, token: str) -> bool:
        """Session を破棄する（L-208）。存在しない識別子の破棄は成功として扱う（冪等・05 §2.9）。"""
        if not token:
            return True
        with self._lock:
            self._records.pop(token, None)
        return True

    def _is_expired(self, record: _Record, now: float) -> bool:
        if now - record.created_at >= self._absolute_seconds:
            return True
        return now - record.last_access_at >= self._idle_seconds
