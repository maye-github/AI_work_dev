"""L-201 稼働判定の単体テスト（TC-213・TC-216 の下位。05 §2.2・§5.2）。

**0 件・無効値・例外はすべて「不可」**。0 件を「可」と読み替えない。
"""

from __future__ import annotations

import logging

import pytest
from conftest import FakeDb, LogCapture

from app.domain.availability import check_available


@pytest.fixture
def logger() -> logging.Logger:
    capture = LogCapture()
    instance = logging.getLogger("r60login.test.availability")
    instance.handlers = [capture]
    instance.setLevel(logging.INFO)
    instance.propagate = False
    return instance


def _check(db: FakeDb, logger: logging.Logger) -> bool:
    return check_available(db, operation_key="VAL_1", logger=logger)  # type: ignore[arg-type]


@pytest.mark.parametrize("flag", ["1", 1])
def test_enabled_flag_one_is_available(flag: object, logger: logging.Logger) -> None:
    """`1` のみ可（文字列・数値のどちらで返っても同じ判定）。"""
    assert _check(FakeDb(operation_flg=flag), logger) is True


@pytest.mark.parametrize("flag", ["0", 0, "Y", "", None, "2"])
def test_disabled_or_unexpected_value_is_unavailable(flag: object, logger: logging.Logger) -> None:
    """`0`・0 件（None）・想定外の値はすべて不可（無効値は不可）。"""
    assert _check(FakeDb(operation_flg=flag), logger) is False


def test_query_exception_is_unavailable(logger: logging.Logger) -> None:
    """照会の例外は「不可」に畳む。例外の内容はログへ出さない（禁⑤）。"""
    db = FakeDb(operation_raises=True)
    capture: LogCapture = logger.handlers[0]  # type: ignore[assignment]

    assert _check(db, logger) is False
    assert capture.result_codes("operation_check_failed") == ["R60W0004"]


def test_reads_only_sql_1(logger: logging.Logger) -> None:
    """稼働判定は SQL-1 だけを発行する（他の照会を起こさない）。"""
    db = FakeDb()

    _check(db, logger)

    assert db.calls == ["SQL-1"]


def test_is_idempotent(logger: logging.Logger) -> None:
    """同一状態なら何度呼んでも同一結果（読み取りのみ）。"""
    db = FakeDb()

    assert [_check(db, logger) for _ in range(3)] == [True, True, True]
