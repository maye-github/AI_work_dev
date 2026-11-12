"""顧客提供の共通処理パッケージ v3.0 への薄い境界（port/adapter）。

- 公開するのは ReferenceChecker.check / EmergencyDispatcher.dispatch / 共通ログのみ。
- 実体パッケージは未提供（工程04 でも未確定）。取得未提供の間は**未接続で起動できる**（Q-327）。
- **共通部品の機能を当方で再実装してはならない**（工程04 §0 末尾）。本ファイルは呼出し境界だけを持つ。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass


class PortNotConnected(RuntimeError):
    """顧客共通部品が未接続のときに送出する（Q-327 の裁定まで未接続で運用）。"""


@dataclass(frozen=True)
class ReferenceResult:
    """被参照チェックの結果（削除済みの参照元は数えない）。"""

    referenced: bool
    count: int
    unexpected: bool = False


class ReferenceChecker:
    """D-208・D-209 の被参照チェック（共通部品が判定する。削除済み参照元は数えない）。"""

    def __init__(self, connected: bool) -> None:
        self._connected = connected

    def check(self, maker_cd: str) -> ReferenceResult:
        if not self._connected:
            # 未接続。共通部品が想定外の結果を返した場合と同じ扱い（E-218）に寄せる。
            raise PortNotConnected("ReferenceChecker (common package v3.0) is not connected")
        raise PortNotConnected("adapter not bound; bind the customer package when provided")


class EmergencyDispatcher:
    """緊急配信の非同期起動。配信の失敗で業務トランザクションをロールバックしない（L-219/L-220）。"""

    def __init__(self, connected: bool) -> None:
        self._connected = connected

    def dispatch(self, payload: dict) -> str | None:
        if not self._connected:
            # 未接続: 受付 ID は返さない（業務結果は確定済み。配信は後日接続後に再実行）。
            return None
        return None


def log_operation(logger_name: str, **fields: object) -> None:
    """共通ログ部品への薄い境界。本画面は独自のログファイルを持たない（設計 §5）。"""
    logging.getLogger(logger_name).info("operation", extra={"fields": fields})
