"""設定の読込（工程04 §3.2・05 §2.3／§2.6／§8.2）。

**値はコードに持たない。** 本テストも占位のみを環境変数へ入れる（禁⑤）。
"""

from __future__ import annotations

import pytest

from app.config import SESSION_ABSOLUTE_SECONDS, SESSION_IDLE_SECONDS, Settings, SettingsError

ENV = {
    "R60_DB_USER": "TBL_1",
    "R60_DB_PASSWORD": "PWD_1",
    "R60_DB_HOST": "IP_1",
    "R60_DB_PORT": "1521",
    "R60_DB_SERVICE_NAME": "SID_1",
    "R60_OPERATION_KEY": "VAL_1",
    "R60_URL_SCHEME": "http",
    "R60_URL_HOST": "IP_1",
    "R60_URL_PORT": "8080",
    "R60_URL_CONTEXT": "ctx",
    "R60_URL_ROUTE": "login",
}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(ENV) + ["R60_SESSION_PURGE_URL"]:
        monkeypatch.delenv(name, raising=False)


def _set_env(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> None:
    for name, value in {**ENV, **overrides}.items():
        monkeypatch.setenv(name, value)


def test_from_env_reads_all_required_values(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)

    settings = Settings.from_env()

    assert settings.db_user == "TBL_1"
    assert settings.db_port == 1521
    assert settings.url_port == 8080
    assert settings.url_route == "login"
    assert settings.session_purge_url is None  # 未設定なら None（予約項目）


def test_optional_purge_url_is_taken_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.setenv("R60_SESSION_PURGE_URL", "VAL_2")

    assert Settings.from_env().session_purge_url == "VAL_2"


def test_session_levels_are_design_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """idle 30 分／絶対 8 時間は設計値であり、環境変数で変えない（05 §8.2）。"""
    _set_env(monkeypatch)

    settings = Settings.from_env()

    assert settings.session_idle_seconds == SESSION_IDLE_SECONDS == 1800
    assert settings.session_absolute_seconds == SESSION_ABSOLUTE_SECONDS == 28800


@pytest.mark.parametrize("missing", sorted(ENV))
def test_missing_required_value_stops_the_startup(missing: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch)
    monkeypatch.delenv(missing)

    with pytest.raises(SettingsError):
        Settings.from_env()


@pytest.mark.parametrize("bad_port", ["", "abc", "1521.5"])
def test_non_integer_port_is_rejected(bad_port: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, R60_DB_PORT=bad_port)

    with pytest.raises(SettingsError):
        Settings.from_env()


def test_database_url_has_no_literal_credentials() -> None:
    """DSN は設定値から組み立てる。本テストは占位で組み立てられることだけを見る。"""
    settings = Settings(
        db_user="TBL_1",
        db_password="PWD_1",
        db_host="IP_1",
        db_port=1521,
        db_service_name="SID_1",
        operation_key="VAL_1",
        url_scheme="http",
        url_host="IP_1",
        url_port=8080,
        url_context="ctx",
        url_route="login",
        session_purge_url=None,
    )

    assert settings.database_url().startswith("oracle+oracledb://TBL_1:PWD_1@IP_1:1521/")
    assert "service_name=SID_1" in settings.database_url()
