"""起動処理（lifespan・NLS 固定）の単体テスト（工程04 §2.3・§3.2）。

**DB へは接続しない。** `create_engine` は接続プールを作るだけで、実際の接続は行わない。
したがって本テストは「起動時に何が組み立てられるか」だけを見る（照会は行わない）。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

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


@pytest.fixture
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)


@pytest.mark.usefixtures("_env")
def test_lifespan_wires_the_application_state() -> None:
    with TestClient(app) as client:
        assert client.get("/openapi.json").status_code == 200
        assert app.state.settings.db_user == "TBL_1"
        assert app.state.engine is not None
        assert app.state.logger.name == "r60login"
        assert app.state.session_store is not None
        assert app.state.login_lockout is not None


@pytest.mark.usefixtures("_env")
def test_startup_fails_when_a_required_value_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """必須の環境変数が無ければ起動しない（既定値で誤って動かさない）。"""
    from app.config import SettingsError

    monkeypatch.delenv("R60_DB_PASSWORD")

    with pytest.raises(SettingsError):
        with TestClient(app):
            pass  # pragma: no cover


def test_three_endpoints_are_registered() -> None:
    """端点は 3 本で固定（05 §1.3）。4 本目を設けない。"""
    paths = {path for path in app.openapi()["paths"] if path.startswith("/R60Login")}

    assert paths == {"/R60Login/init", "/R60Login/login", "/R60Login/generateUrl"}
