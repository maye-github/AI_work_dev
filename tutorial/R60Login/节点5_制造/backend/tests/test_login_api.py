"""`POST /R60Login/login` の単体テスト（TC-202・TC-211・TC-213・TC-215・TC-217・TC-218・TC-221）。

E-201／E-207 は **`errorCode` のみ**を返す（裁定 Q-235）。文言を載せないことをキー集合で固定する。
"""

from __future__ import annotations

import pytest
from conftest import (
    SQL_EMPLOYEE,
    SQL_MESSAGE,
    SQL_MNG_INFO,
    SQL_OPERATION,
    SQL_USER_INFO,
    FakeClock,
    FakeDb,
    encrypted_stf_cd,
)

from app.domain.login_lockout import LOCK_SECONDS
from app.main import app as fastapi_app
from app.repository.queries import FALLBACK_SYSTEM_ERROR_MESSAGE

ENDPOINT = "/R60Login/login"
SESSION_COOKIE = "r60login.sid"


def _login(client, **overrides):
    payload = {"encryptedStfCd": encrypted_stf_cd()}
    payload.update(overrides)
    return client.post(ENDPOINT, json=payload)


# --- TC-202: 正常系 ---------------------------------------------------------------------------
def test_tc202_success_returns_user_and_mng_info(harness) -> None:
    client, _capture, _ = harness(FakeDb())

    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "0"
    assert body["userInfo"] == {
        "stfCd": "EMP_1",
        "stfNm": "NAME_1",
        "cmpCd": "CMP_1",
        "cmpNm": "CMPNAME_1",
        "jigCd": "JIG_1",
        "jigNm": "JIGNAME_1",
    }
    assert body["mngInfo"] == {
        "scmpCd": "SCMP_1",
        "sjigCd": "SJIG_1",
        "jiKjoKsnFlg": "Y",  # 'Y'/'N' のまま。1/0 へ変換しない（裁定 Q-234）
        "taKjoKsnFlg": "N",
        "loginAcsKais": 3,
    }
    assert "errorDetailCode" not in body
    assert "errorMessage" not in body


def test_tc202_session_identifier_is_only_in_an_httponly_cookie(harness) -> None:
    client, _capture, _ = harness(FakeDb())

    response = _login(client)

    assert SESSION_COOKIE in response.cookies
    token = response.cookies[SESSION_COOKIE]
    assert token
    assert "httponly" in response.headers["set-cookie"].lower()
    # 応答本文に識別子を含めない（05 §8.2）
    assert token not in response.text


def test_tc202_ignored_request_fields_do_not_change_the_result(harness) -> None:
    """Q-212: `stfKbn`・`gmnId`・`kgnKbn` は受信するだけで、検証も保存もしない。"""
    client, _capture, _ = harness(FakeDb())

    with_extra = _login(client, stfKbn="VAL_1", gmnId="VAL_2", kgnKbn="VAL_3")
    without_extra = _login(client)

    assert with_extra.json()["userInfo"] == without_extra.json()["userInfo"]
    assert with_extra.json()["mngInfo"] == without_extra.json()["mngInfo"]


def test_tc202_sql_order_is_1_3_4_5(harness) -> None:
    db = FakeDb()
    client, _capture, _ = harness(db)

    _login(client)

    assert db.calls == [SQL_OPERATION, SQL_EMPLOYEE, SQL_USER_INFO, SQL_MNG_INFO]


# --- TC-211 / TC-217: E-201・E-207 は errorCode のみ -------------------------------------------
def test_tc211_no_matching_employee_returns_error_code_only(harness) -> None:
    db = FakeDb(employee=False)
    client, _capture, _ = harness(db)

    response = _login(client)

    assert response.status_code == 200
    assert response.json() == {"errorCode": "1"}  # キーは 1 個だけ（TC-217 の応答形式）
    assert SESSION_COOKIE not in response.cookies
    # 文言は取得しない（SQL-6 を実行しない）
    assert SQL_MESSAGE not in db.calls
    # 社員照会の後は進まない
    assert SQL_USER_INFO not in db.calls


def test_tc217_response_has_no_extra_keys(harness) -> None:
    client, _capture, _ = harness(FakeDb(employee=False))

    body = _login(client).json()

    assert set(body) == {"errorCode"}
    assert body["errorCode"] == "1"


# --- TC-213 / E-203: 稼働不可 ----------------------------------------------------------------
@pytest.mark.parametrize("db_kwargs", [{"operation_flg": "0"}, {"operation_flg": None}, {"operation_raises": True}])
def test_tc213_unavailable_returns_403_before_decryption(db_kwargs: dict, harness) -> None:
    db = FakeDb(messages={"R60W0004": "MSG_1"}, **db_kwargs)
    client, _capture, _ = harness(db)

    response = client.post(ENDPOINT, json={"encryptedStfCd": "VAL_1"})  # 復号できない値でも 403 が先

    assert response.status_code == 403
    body = response.json()
    assert body["errorCode"] == "1"
    assert body["errorDetailCode"] == "R60W0004"
    assert "userInfo" not in body
    assert SESSION_COOKIE not in response.cookies
    assert SQL_EMPLOYEE not in db.calls


# --- TC-215 / E-205: 復号失敗 -----------------------------------------------------------------
@pytest.mark.parametrize("bad_value", ["", "ABC", "1_2_3", "20261027"])
def test_tc215_decryption_failure_returns_w0003(bad_value: str, harness) -> None:
    db = FakeDb(messages={"R60W0003": "MSG_1"})
    client, capture, _ = harness(db)

    response = client.post(ENDPOINT, json={"encryptedStfCd": bad_value})

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "1"
    assert body["errorDetailCode"] == "R60W0003"
    assert body["errorMessage"] == "MSG_1"
    assert SESSION_COOKIE not in response.cookies
    # ログに暗号化値を出さない（結果コードのみ）
    accesses = capture.events("access")
    assert accesses[-1].__dict__["result_code"] == "R60W0003"
    assert "stf_cd_masked" not in accesses[-1].__dict__


# --- TC-218 / E-208: ログイン中の DB 障害 -----------------------------------------------------
@pytest.mark.parametrize("db_kwargs", [{"user_raises": True}, {"mng_raises": True}])
def test_tc218_db_failure_returns_error_code_2(db_kwargs: dict, harness) -> None:
    db = FakeDb(**db_kwargs)
    client, _capture, _ = harness(db)

    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "2"
    assert body["errorDetailCode"] == "R60E9999"
    assert body["errorMessage"] == FALLBACK_SYSTEM_ERROR_MESSAGE
    assert "userInfo" not in body
    assert "mngInfo" not in body
    assert SESSION_COOKIE not in response.cookies
    # 例外の中身（表名・例外文）を利用者向け文言へ出さない（05 §8.1）
    assert "STF_MST" not in body["errorMessage"]
    assert "failed" not in body["errorMessage"]


# --- TC-221 / B-44〜B-46: ログイン試行ロック --------------------------------------------------
def test_tc221_lock_is_established_on_the_fifth_failure(harness) -> None:
    """B-45: 5 回目の応答は**通常の E-201**（照会は済んでいる）。ロック成立時に運用ログ 1 件。"""
    clock = FakeClock()
    db = FakeDb(employee=False)
    client, capture, _ = harness(db, clock=clock)

    for _ in range(5):
        assert _login(client).json() == {"errorCode": "1"}

    assert db.count(SQL_EMPLOYEE) == 5
    assert len(capture.events("login_locked")) == 1
    assert fastapi_app.state.login_lockout.is_locked(
        fastapi_app.state.login_lockout.key_for("1234567")
    )


def test_tc221_locked_request_does_not_query_and_shows_nothing(harness) -> None:
    """ロック中は照会しない。応答は E-201 と同じ形式で、ロック中であることを示さない。"""
    clock = FakeClock()
    db = FakeDb(employee=False)
    client, _capture, _ = harness(db, clock=clock)
    for _ in range(5):
        _login(client)

    response = _login(client)

    assert response.json() == {"errorCode": "1"}
    assert db.count(SQL_EMPLOYEE) == 5  # 6 回目は SQL-3 を発行しない
    assert SESSION_COOKIE not in response.cookies


def test_tc221_b44_four_failures_do_not_lock(harness) -> None:
    clock = FakeClock()
    db = FakeDb(employee=False)
    client, _capture, _ = harness(db, clock=clock)

    for _ in range(4):
        assert _login(client).json() == {"errorCode": "1"}

    key = fastapi_app.state.login_lockout.key_for("1234567")
    assert fastapi_app.state.login_lockout.is_locked(key) is False

    _login(client)  # 5 回目も照会する（＝まだロックしていない）

    assert db.count(SQL_EMPLOYEE) == 5


def test_tc221_b46_lock_is_released_after_ten_minutes(harness) -> None:
    clock = FakeClock()
    db = FakeDb(employee=False)
    client, capture, _ = harness(db, clock=clock)
    for _ in range(5):
        _login(client)

    clock.advance(LOCK_SECONDS)

    _login(client)  # 解除後は照会する

    assert db.count(SQL_EMPLOYEE) == 6
    assert len(capture.events("login_locked")) == 1  # 解除はログを出さない


def test_tc221_success_resets_the_counter(harness) -> None:
    """成功したら計数を 0 に戻す（4 回失敗 → 成功 → 4 回失敗ではロックしない）。"""
    clock = FakeClock()
    db = FakeDb(employee=[False, False, False, False, True, False, False, False, False])
    client, _capture, _ = harness(db, clock=clock)

    for _ in range(5):  # 5 回目で成功する
        _login(client)
    for _ in range(4):
        _login(client)

    key = fastapi_app.state.login_lockout.key_for("1234567")
    assert fastapi_app.state.login_lockout.is_locked(key) is False


def test_tc221_lock_does_not_return_a_session_cookie(harness) -> None:
    clock = FakeClock()
    db = FakeDb(employee=False)
    client, _capture, _ = harness(db, clock=clock)
    for _ in range(5):
        _login(client)

    response = _login(client)

    assert SESSION_COOKIE not in response.cookies
    assert set(response.json()) == {"errorCode"}


# --- B-42: SQL-4・SQL-5 が 0 件（マスタ不整合）は E-201 と同じ扱い -------------------------------
def test_b42_sql_4_empty_is_treated_as_e201(harness) -> None:
    db = FakeDb(user_row=None)
    client, capture, _ = harness(db)

    response = _login(client)

    assert response.json() == {"errorCode": "1"}
    assert SESSION_COOKIE not in response.cookies
    assert len(capture.events("master_inconsistency")) == 1
    assert "error_type" not in capture.events("master_inconsistency")[0].__dict__


def test_sql_5_empty_is_treated_as_e201(harness) -> None:
    db = FakeDb(mng_row=None)
    client, capture, _ = harness(db)

    response = _login(client)

    assert response.json() == {"errorCode": "1"}
    assert SESSION_COOKIE not in response.cookies
    record = capture.events("master_inconsistency")[0]
    assert record.__dict__["error_type"] == "SQL-5_EMPTY"


def test_short_employee_code_is_fully_masked_in_the_log(harness) -> None:
    """工程04 §6.2: 2 桁以下は全桁を `*` にする（先頭・末尾を残さない）。"""
    client, capture, _ = harness(FakeDb())

    response = client.post(ENDPOINT, json={"encryptedStfCd": encrypted_stf_cd("12")})

    assert response.json()["errorCode"] == "0"
    assert capture.events("access")[-1].__dict__["stf_cd_masked"] == "**"
