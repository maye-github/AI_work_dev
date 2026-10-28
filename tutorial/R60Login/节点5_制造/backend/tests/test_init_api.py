"""`POST /R60Login/init` の単体テスト（TC-201・TC-209・TC-210・TC-214・TC-216）。

応答の形（camelCase・`errorDetailCode`/`errorMessage` は異常時のみ）も併せて固定する。
"""

from __future__ import annotations

import pytest
from conftest import SQL_MESSAGE, SQL_OPERATION, SQL_PAGES, FakeDb

from app.repository.queries import FALLBACK_SYSTEM_ERROR_MESSAGE

ENDPOINT = "/R60Login/init"
KBN_LIST = [
    {"value": "Y", "label": "更新あり"},
    {"value": "N", "label": "更新なし"},
]


# --- TC-201: 正常系（候補あり） ---------------------------------------------------------------
def test_tc201_returns_candidates_and_fixed_kbn_list(harness) -> None:
    db = FakeDb(pages=[("VAL_1", "VAL_2"), ("VAL_3", "VAL_4")])
    client, _capture, _ = harness(db)

    response = client.post(ENDPOINT)

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "0"
    assert body["pageList"] == [
        {"value": "VAL_1", "label": "VAL_2"},
        {"value": "VAL_3", "label": "VAL_4"},
    ]
    assert body["kbnList"] == KBN_LIST
    # 正常時は異常系の項目を載せない（05 §4.2）
    assert "errorDetailCode" not in body
    assert "errorMessage" not in body


def test_tc201_order_follows_the_sql_not_the_endpoint(harness) -> None:
    """並び順は SQL-2 の `ORDER BY disp_order, gmn_id` が決める。端点は並べ替えない。"""
    db = FakeDb(pages=[("VAL_2", "VAL_2"), ("VAL_1", "VAL_1")])
    client, _capture, _ = harness(db)

    body = client.post(ENDPOINT).json()

    assert [item["value"] for item in body["pageList"]] == ["VAL_2", "VAL_1"]


def test_tc201_issues_sql_1_then_sql_2(harness) -> None:
    db = FakeDb()
    client, _capture, _ = harness(db)

    client.post(ENDPOINT)

    assert db.calls == [SQL_OPERATION, SQL_PAGES]


def test_tc201_sets_the_client_cookie(harness) -> None:
    """連続失敗の計数に用いる識別子を Cookie で持たせる（利用者の識別情報は持たない）。"""
    client, _capture, _ = harness(FakeDb())

    response = client.post(ENDPOINT)

    assert "r60login.cid" in response.cookies
    assert response.cookies["r60login.cid"]


# --- TC-209 / B-22: 候補 0 件はエラーではない ------------------------------------------------
def test_tc209_zero_candidates_is_not_an_error(harness) -> None:
    db = FakeDb(pages=[])
    client, capture, _ = harness(db)

    response = client.post(ENDPOINT)

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "0"
    assert body["pageList"] == []
    assert body["kbnList"] == KBN_LIST  # 権限区分は 2 件固定のまま
    assert "errorDetailCode" not in body
    # 0 件はエラーではないため、失敗の計数も起こさない
    assert capture.events("init_failure_repeated") == []


# --- TC-214 / E-204: 画面マスタ取得失敗 ------------------------------------------------------
def test_tc214_sql_2_exception_is_error_code_2(harness) -> None:
    db = FakeDb(pages_raises=True, messages={"R60E9999": "MSG_1"})
    client, _capture, _ = harness(db)

    response = client.post(ENDPOINT)

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "2"
    assert body["errorDetailCode"] == "R60E9999"
    assert body["errorMessage"] == "MSG_1"
    assert "pageList" not in body
    assert "kbnList" not in body


def test_tc214_falls_back_when_the_message_master_has_no_row(harness) -> None:
    """SQL-6 が 0 件なら汎用文言に替える（コード文字列を利用者に見せない・05 §5.7）。"""
    client, _capture, _ = harness(FakeDb(pages_raises=True))

    body = client.post(ENDPOINT).json()

    assert body["errorMessage"] == FALLBACK_SYSTEM_ERROR_MESSAGE
    assert "R60E9999" not in body["errorMessage"]


# --- TC-210 / B-29〜B-31: 連続 3 回で運用ログ 1 件 -------------------------------------------
def test_tc210_logs_exactly_once_on_the_third_consecutive_failure(harness) -> None:
    db = FakeDb(pages_raises=True)
    client, capture, _ = harness(db)

    counts = []
    for _ in range(3):
        response = client.post(ENDPOINT)
        assert response.json()["errorCode"] == "2"
        counts.append(len(capture.events("init_failure_repeated")))

    assert counts == [0, 0, 1]
    record = capture.events("init_failure_repeated")[0]
    assert record.__dict__["screen_id"] == "R60Login"
    assert record.__dict__["result_code"] == "R60E9999"


def test_tc210_counter_resets_on_success(harness) -> None:
    """B-31: 3 回未満で成功したら計数を 0 に戻す（「連続」の意味を保つ）。"""
    db = FakeDb(pages_raises=True)
    client, capture, _ = harness(db)

    client.post(ENDPOINT)  # 1 回目
    client.post(ENDPOINT)  # 2 回目

    db.pages_raises = False
    assert client.post(ENDPOINT).json()["errorCode"] == "0"

    db.pages_raises = True
    client.post(ENDPOINT)
    client.post(ENDPOINT)

    assert capture.events("init_failure_repeated") == []


# --- TC-216 / E-206: /init の稼働不可 --------------------------------------------------------
@pytest.mark.parametrize("db_kwargs", [{"operation_flg": "0"}, {"operation_flg": None}, {"operation_raises": True}])
def test_tc216_unavailable_returns_403_and_skips_sql_2(db_kwargs: dict, harness) -> None:
    db = FakeDb(messages={"R60W0004": "MSG_1"}, **db_kwargs)
    client, _capture, _ = harness(db)

    response = client.post(ENDPOINT)

    assert response.status_code == 403
    body = response.json()
    assert body["errorCode"] == "1"
    assert body["errorDetailCode"] == "R60W0004"
    assert body["errorMessage"] == "MSG_1"
    # 候補取得をしない（SQL-2 を発行しない）。文言は SQL-6 で取得する。
    assert "pageList" not in body
    assert db.calls == [SQL_OPERATION, SQL_MESSAGE]
