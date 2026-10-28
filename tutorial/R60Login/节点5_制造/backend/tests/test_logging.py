"""運用ログの書式と文脈の注入（工程04 §6.2・05 §8.1）。

05 §8.1 の運用ログ 5 項目（時刻・画面ID・結果コード・インスタンスID・要求ID）を満たすこと、
および**白名单に無い項目を捨てる**ことを固定する（社員コードの平文が混ざらないための最後の関門）。
"""

from __future__ import annotations

import json
import logging

from app.main import _INSTANCE_ID, _LOG_EXTRA_KEYS, _REQUEST_ID, JsonLineFormatter, _LogContextFilter


def _record(event: str = "access", **extra: object) -> logging.LogRecord:
    record = logging.LogRecord("r60login", logging.INFO, __file__, 1, event, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_filter_injects_instance_and_request_ids() -> None:
    record = _record()

    assert _LogContextFilter().filter(record) is True
    assert record.instance_id == _INSTANCE_ID
    assert len(record.instance_id) == 32
    assert record.request_id == "-"  # 要求の外（起動直後など）は既定値


def test_filter_reads_the_current_request_id() -> None:
    token = _REQUEST_ID.set("VAL_1")
    try:
        record = _record()
        _LogContextFilter().filter(record)
        assert record.request_id == "VAL_1"
    finally:
        _REQUEST_ID.reset(token)


def test_formatter_emits_one_json_line_with_the_five_items() -> None:
    record = _record(result_code="0", screen_id="R60Login")
    _LogContextFilter().filter(record)

    payload = json.loads(JsonLineFormatter().format(record))

    assert set(payload) == {"time", "level", "event", "result_code", "screen_id", "instance_id", "request_id"}
    assert payload["level"] == "INFO"
    assert payload["event"] == "access"
    assert payload["result_code"] == "0"
    assert payload["screen_id"] == "R60Login"


def test_formatter_drops_keys_outside_the_allow_list() -> None:
    """白名单外の項目は捨てる（社員コードの平文・当日鍵などを載せない）。"""
    record = _record(stf_cd="VAL_1", key_date="VAL_2", stf_cd_masked="V*1")

    payload = json.loads(JsonLineFormatter().format(record))

    assert "stf_cd" not in payload
    assert "key_date" not in payload
    assert payload["stf_cd_masked"] == "V*1"  # マスク済みの項目だけは載せてよい


def test_allow_list_covers_the_designed_log_items() -> None:
    for key in ("screen_id", "result_code", "instance_id", "request_id"):
        assert key in _LOG_EXTRA_KEYS
