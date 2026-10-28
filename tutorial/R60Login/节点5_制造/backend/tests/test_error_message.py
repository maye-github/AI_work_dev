"""利用者向け文言の取得（SQL-6・05 §5.7）。

**コード文字列を利用者に見せない。** 0 件・取得失敗は汎用文言に替え、結果コードは運用ログへ残す。
"""

from __future__ import annotations

import logging

import pytest
from conftest import FakeDb, LogCapture

from app.repository.queries import FALLBACK_SYSTEM_ERROR_MESSAGE, fetch_error_message, resolve_error_message


@pytest.fixture
def logger() -> logging.Logger:
    instance = logging.getLogger("r60login.test.message")
    instance.handlers = [LogCapture()]
    instance.setLevel(logging.INFO)
    instance.propagate = False
    return instance


def test_returns_the_message_from_the_master(logger: logging.Logger) -> None:
    db = FakeDb(messages={"R60W0001": "MSG_1"})

    assert resolve_error_message(db, error_detail_code="R60W0001", logger=logger) == "MSG_1"  # type: ignore[arg-type]


def test_zero_rows_falls_back_to_the_generic_message(logger: logging.Logger) -> None:
    db = FakeDb()

    message = resolve_error_message(db, error_detail_code="R60W0001", logger=logger)  # type: ignore[arg-type]

    assert message == FALLBACK_SYSTEM_ERROR_MESSAGE
    record = logger.handlers[0].records[0]  # type: ignore[attr-defined]
    assert record.__dict__["msg_id"] == "R60W0001"


def test_query_failure_falls_back_the_same_way(logger: logging.Logger) -> None:
    """取得の例外も 0 件と同じ扱いにする（利用者へ例外文を出さない）。"""
    db = FakeDb(messages_raises=True)

    message = resolve_error_message(db, error_detail_code="R60W0001", logger=logger)  # type: ignore[arg-type]

    assert message == FALLBACK_SYSTEM_ERROR_MESSAGE
    assert "failed" not in message


def test_fetch_returns_none_for_missing_row() -> None:
    connection = FakeDb().connect()

    assert fetch_error_message(connection, error_detail_code="R60W0001") is None


def test_fallback_message_is_the_designed_text() -> None:
    """上流 §9.1 の E-204／E-208 と同じ文言（C・v1.0.2）。"""
    assert FALLBACK_SYSTEM_ERROR_MESSAGE == "システムエラーが発生しました。画面を再読み込みしてください。"
