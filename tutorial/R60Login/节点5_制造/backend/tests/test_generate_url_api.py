"""`POST /R60Login/generateUrl` の単体テスト（TC-204・TC-207・TC-219・TC-220）。

組立（ステップ6）と 150 桁判定（ステップ7）は**サーバ**が行う（裁定 Q-233）。
**150 桁超は切捨てない**（E-210・B-21）。
"""

from __future__ import annotations

import pytest
from conftest import SQL_EMPLOYEE, SQL_OPERATION, FakeDb, encrypted_stf_cd

from app.api import generate_url_api
from app.domain.stf_cd_cipher import StfCdCipherError
from app.repository.queries import FALLBACK_SYSTEM_ERROR_MESSAGE

ENDPOINT = "/R60Login/generateUrl"
BASE = "http://IP_1:8080/ctx/login"


def _skeleton(encrypted: str) -> str:
    """空のパラメータで組んだ URL。ここに桁数を足して境界を作る。"""
    return f"{BASE}?stfCd={encrypted}&stfKbn=&gmnId=&kgnKbn="


# --- TC-204: 正常系（サーバが組み立て、順序は固定） -------------------------------------------
def test_tc204_builds_the_url_on_the_server(harness) -> None:
    client, _capture, _ = harness(FakeDb())

    response = client.post(
        ENDPOINT,
        json={"stfCd": "1234567", "stfKbn": "VAL_1", "gmnId": "VAL_2", "kgnKbn": "VAL_3"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["errorCode"] == "0"
    assert body["url"] == (
        f"{BASE}?stfCd={encrypted_stf_cd('1234567')}"
        "&stfKbn=VAL_1&gmnId=VAL_2&kgnKbn=VAL_3"
    )
    assert len(body["url"]) <= 150
    assert "errorDetailCode" not in body


def test_tc204_does_not_percent_encode_or_reorder(harness) -> None:
    """UTF-8・パーセントエンコードなし、順序は `stfCd`→`stfKbn`→`gmnId`→`kgnKbn` の固定（Q-201）。"""
    client, _capture, _ = harness(FakeDb())

    url = client.post(
        ENDPOINT,
        json={"kgnKbn": "VAL_3", "gmnId": "VAL_2", "stfKbn": "VAL_1", "stfCd": "1234567"},
    ).json()["url"]

    assert "%" not in url
    assert url.index("stfCd=") < url.index("stfKbn=") < url.index("gmnId=") < url.index("kgnKbn=")


def test_tc204_available_check_runs_first(harness) -> None:
    db = FakeDb()
    client, _capture, _ = harness(db)

    client.post(ENDPOINT, json={"stfCd": "1234567"})

    assert db.calls[0] == SQL_OPERATION


def test_unfilled_stf_cd_is_sent_as_nan_without_encryption(harness) -> None:
    """Q-231: I-303 が空欄なら `"NaN"` を社員コードとして載せ、暗号化しない。"""
    client, _capture, _ = harness(FakeDb())

    body = client.post(ENDPOINT, json={"stfCd": ""}).json()

    assert body["errorCode"] == "0"
    assert "stfCd=NaN" in body["url"]


@pytest.mark.parametrize("raw", ["１２３４５６７", "１２３あ４５６７"])
def test_normalization_maps_full_width_and_drops_non_ascii(raw: str, harness) -> None:
    """Q-210: 全角 ASCII は半角へ写し、残った非 ASCII は落とす。結果が数字なら暗号化する。"""
    client, _capture, _ = harness(FakeDb())

    body = client.post(ENDPOINT, json={"stfCd": raw}).json()

    assert body["errorCode"] == "0"
    assert f"stfCd={encrypted_stf_cd('1234567')}" in body["url"]


@pytest.mark.parametrize("bad_stf_cd", ["VAL_1", "12a4567", " ", "１２３４５６Ａ"])
def test_non_digit_stf_cd_is_rejected_without_building_a_url(bad_stf_cd: str, harness) -> None:
    """分岐 4 / B-40: 正規化後に数字でなければ E-202（`R60W0001`）。URL を組み立てない。"""
    client, _capture, _ = harness(FakeDb(messages={"R60W0001": "MSG_1"}))

    body = client.post(ENDPOINT, json={"stfCd": bad_stf_cd}).json()

    assert body["errorCode"] == "1"
    assert body["errorDetailCode"] == "R60W0001"
    assert "url" not in body


# --- TC-207 / B-20: 150 桁ちょうどは正常 ------------------------------------------------------
def test_tc207_exactly_150_characters_is_accepted(harness) -> None:
    client, _capture, _ = harness(FakeDb())
    encrypted = encrypted_stf_cd("1234567")
    padding = 150 - len(_skeleton(encrypted))

    body = client.post(ENDPOINT, json={"stfCd": "1234567", "kgnKbn": "X" * padding}).json()

    assert body["errorCode"] == "0"
    assert len(body["url"]) == 150
    assert body["url"].endswith("kgnKbn=" + "X" * padding)


# --- TC-220 / B-21・E-210: 151 桁は切捨てずエラー ----------------------------------------------
def test_tc220_151_characters_is_rejected_without_truncation(harness) -> None:
    client, _capture, _ = harness(FakeDb(messages={"R60W0001": "MSG_1"}))
    encrypted = encrypted_stf_cd("1234567")
    padding = 151 - len(_skeleton(encrypted))

    body = client.post(ENDPOINT, json={"stfCd": "1234567", "kgnKbn": "X" * padding}).json()

    assert body["errorCode"] == "1"
    assert body["errorDetailCode"] == "R60W0001"
    assert "url" not in body  # 150 桁へ切り詰めた URL を返さない


# --- TC-219 / E-209: 暗号化失敗・設定不備 -----------------------------------------------------
def test_tc219_encryption_failure_returns_error_code_2(harness, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args, **_kwargs):
        raise StfCdCipherError("鍵日付が不正である")

    monkeypatch.setattr(generate_url_api, "encrypt_stf_cd", _raise)
    client, _capture, db = harness(FakeDb())

    body = client.post(ENDPOINT, json={"stfCd": "1234567"}).json()

    assert body["errorCode"] == "2"
    assert body["errorDetailCode"] == "R60E9999"
    assert body["errorMessage"] == FALLBACK_SYSTEM_ERROR_MESSAGE  # E-208 と同一文面
    assert "url" not in body
    assert db.calls[0] == SQL_OPERATION  # 稼働判定から入る
    assert SQL_EMPLOYEE not in db.calls  # 社員検証へは進まない


# --- 稼働不可（TC-213 の /generateUrl 側） ----------------------------------------------------
def test_unavailable_returns_403_and_no_url(harness) -> None:
    db = FakeDb(operation_flg="0", messages={"R60W0004": "MSG_1"})
    client, _capture, _ = harness(db)

    response = client.post(ENDPOINT, json={"stfCd": "1234567"})

    assert response.status_code == 403
    body = response.json()
    assert body["errorCode"] == "1"
    assert body["errorDetailCode"] == "R60W0004"
    assert "url" not in body


def test_short_stf_cd_is_fully_masked_in_the_log(harness) -> None:
    """工程04 §6.2: 2 桁以下は全桁を `*` にする（ログに平文を残さない）。"""
    client, capture, _ = harness(FakeDb())

    body = client.post(ENDPOINT, json={"stfCd": "12"}).json()

    assert body["errorCode"] == "0"
    assert capture.events("access")[-1].__dict__["stf_cd_masked"] == "**"
