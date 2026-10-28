"""ログイン試行ロック（L-203 §2.4.1・05 v1.0.5・BUG-002）。

上流 節点2 §11「ログイン試行 5 回／10 分でロック。10 分後に自動解除」の実装。

* **数えるのは認証失敗（ステップ3 の社員照会が 0 件＝E-201）だけ**である。E-204／E-205／E-208 は数えない
  （前者は基盤障害、後者は識別子の不正であり、同一利用者の試行と見なさない・§2.4.1）。
* 計数のキーは**社員コードの SHA-256（プロセス起動時に生成する salt 付き）**。**平文を保持しない**。
* 保持先は**プロセス内**（節点4 OQ-05「本件は単一インスタンス」の裁定）。多インスタンス化する場合は
  外部ストアが必要で構成変更（CR）となる。差異は `06_設計との差異.md` に記録する。
* **ロック中であることを利用者へ示さない**——呼出元は E-201 と同じ形式（`errorCode` の `"1"` のみ）で応答する
  （§2.4.1・§6.2）。
* 時計は**注入できる**（`clock`）。§8.3 が「テストで固定できるよう引数化する」と定めているため。
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from collections.abc import Callable

# §2.4.1 の水準値。設計値であり環境変数にしない（値を環境ごとに変えない）。
MAX_FAILURES = 5
WINDOW_SECONDS = 10 * 60
LOCK_SECONDS = 10 * 60


class LoginLockout:
    """社員コードごとの認証失敗を滑り窓で数え、5 回で 10 分ロックする（§2.4.1）。

    計数の加算と判定は**同一の排他区間**で行う（同時要求で 5 回を超えて通さない・§2.4.1「順序・冪等性」）。
    """

    def __init__(
        self,
        *,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        lock_seconds: float = LOCK_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._lock_seconds = lock_seconds
        self._clock = clock or time.monotonic
        self._salt = secrets.token_bytes(16)
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._mutex = threading.Lock()

    def key_for(self, stf_cd: str) -> str:
        """社員コードから計数キーを作る。平文の社員コードは保持しない（§2.4.1）。"""
        return hashlib.sha256(self._salt + stf_cd.encode("utf-8")).hexdigest()

    def is_locked(self, key: str) -> bool:
        """ロック中なら True。**解除は成立時刻から 10 分の経過のみ**（人手の解除操作は無い）。"""
        now = self._clock()
        with self._mutex:
            until = self._locked_until.get(key)
            if until is None:
                return False
            if now < until:
                return True
            del self._locked_until[key]
            self._failures.pop(key, None)
            return False

    def record_failure(self, key: str) -> bool:
        """認証失敗を 1 件数える。**ロックを成立させたときだけ True** を返す（運用ログ 1 件の判定に使う）。

        5 回目の失敗はここでロックを成立させるが、**その応答自体は通常の E-201** である
        （照会は済んでいるため。§2.4.1・境界 B-45）。照会しないのは 6 回目からである。
        """
        now = self._clock()
        with self._mutex:
            recent = [t for t in self._failures.get(key, ()) if now - t < self._window_seconds]
            recent.append(now)
            if len(recent) >= self._max_failures:
                self._locked_until[key] = now + self._lock_seconds
                # ロック成立後は窓の計数を捨てる（解除後は 0 から数え直す）。
                self._failures.pop(key, None)
                return True
            self._failures[key] = recent
            return False

    def reset(self, key: str) -> None:
        """成功時に計数を 0 に戻す（§2.4.1「成功時の扱い」）。"""
        with self._mutex:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)
