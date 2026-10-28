"""Session 保持の単体テスト（L-203 ステップ6・L-208・05 §8.2）。

失効は **idle 30 分／絶対 8 時間**。時計は `time.monotonic` をモジュール差し替えで固定する
（`SessionStore` は時計を引数に取らないため、`session_store` モジュールの `time` を偽物に置き換える）。
"""

from __future__ import annotations

import pytest

from app.domain import session_store as session_store_module
from app.domain.session_store import SESSION_COOKIE_NAME, SessionStore

IDLE = 30 * 60
ABSOLUTE = 8 * 60 * 60

PAYLOAD = {"stfCd": "EMP_1", "loginAcsKais": 0}


class _Time:
    """`time` モジュールの顔のうち `monotonic` だけを持つ偽物。"""

    def __init__(self, now: float = 1_000.0) -> None:
        self.now = now

    def monotonic(self) -> float:
        return self.now


@pytest.fixture
def fake_time(monkeypatch: pytest.MonkeyPatch) -> _Time:
    clock = _Time()
    monkeypatch.setattr(session_store_module, "time", clock)
    return clock


@pytest.fixture
def store() -> SessionStore:
    return SessionStore(idle_seconds=IDLE, absolute_seconds=ABSOLUTE)


def test_cookie_name_is_defined_in_one_place() -> None:
    """Cookie 名は設計に無いため本節点で定めた（差異登記に記載）。空でないことだけを固定する。"""
    assert SESSION_COOKIE_NAME == "r60login.sid"


def test_create_then_get_returns_payload(fake_time: _Time, store: SessionStore) -> None:
    token = store.create(dict(PAYLOAD))

    assert token
    assert store.get(token) == PAYLOAD


def test_returned_payload_is_a_copy(fake_time: _Time, store: SessionStore) -> None:
    """呼出元が受け取った辞書を書き換えても、保持値は変わらない。"""
    token = store.create(dict(PAYLOAD))

    got = store.get(token)
    assert got is not None
    got["stfCd"] = "VAL_1"

    assert store.get(token) == PAYLOAD


def test_each_create_yields_a_new_token(fake_time: _Time, store: SessionStore) -> None:
    """多重ログインは許可する（識別子は呼出しごとに新規＝意図的な非冪等）。"""
    first = store.create(dict(PAYLOAD))
    second = store.create(dict(PAYLOAD))

    assert first != second
    assert store.get(first) == PAYLOAD
    assert store.get(second) == PAYLOAD


def test_idle_expiry_removes_the_session(fake_time: _Time, store: SessionStore) -> None:
    token = store.create(dict(PAYLOAD))

    fake_time.now += IDLE  # ちょうど 30 分（>= で失効）

    assert store.get(token) is None


def test_access_extends_the_idle_timer(fake_time: _Time, store: SessionStore) -> None:
    """idle は**最終アクセス**から数える。アクセスし続ける限り失効しない（絶対期限までは）。"""
    token = store.create(dict(PAYLOAD))

    fake_time.now += IDLE - 1
    assert store.get(token) == PAYLOAD  # ここで last_access が更新される

    fake_time.now += IDLE - 1
    assert store.get(token) == PAYLOAD


def test_absolute_expiry_wins_over_recent_access(fake_time: _Time, store: SessionStore) -> None:
    """絶対 8 時間は、アクセスがあっても延びない。"""
    token = store.create(dict(PAYLOAD))

    # idle（30 分）を跨がない間隔で 8 時間を超えるまでアクセスし続ける
    for _ in range(ABSOLUTE // IDLE + 2):
        fake_time.now += IDLE - 1
        store.get(token)

    assert store.get(token) is None


def test_delete_is_idempotent(fake_time: _Time, store: SessionStore) -> None:
    """L-208: 存在しない識別子の破棄も成功として扱う（冪等・05 §2.9）。"""
    token = store.create(dict(PAYLOAD))

    assert store.delete(token) is True
    assert store.delete(token) is True
    assert store.get(token) is None


def test_empty_token_is_handled_without_error(fake_time: _Time, store: SessionStore) -> None:
    assert store.get("") is None
    assert store.delete("") is True


def test_unknown_token_returns_none(fake_time: _Time, store: SessionStore) -> None:
    assert store.get("VAL_1") is None
