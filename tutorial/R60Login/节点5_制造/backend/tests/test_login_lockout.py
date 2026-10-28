"""ログイン試行ロックの単体テスト（TC-221・L-203 §2.4.1・05 v1.0.5）。

境界は B-44（4 回ではロックしない）・B-45（5 回で成立。5 回目の応答自体は通常の E-201）・
B-46（成立から 10 分で自動解除）。**E を増やさない**——ロック中の応答は E-201 と同じ形式である。
"""

from __future__ import annotations

import pytest

from app.domain.login_lockout import LOCK_SECONDS, MAX_FAILURES, WINDOW_SECONDS, LoginLockout
from conftest import FakeClock

KEY = "VAL_1"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def _lockout(clock: FakeClock) -> LoginLockout:
    return LoginLockout(clock=clock)


def test_design_values_are_five_and_ten_minutes() -> None:
    """§2.4.1 の水準値。環境変数で変えない（設計値）。"""
    assert MAX_FAILURES == 5
    assert WINDOW_SECONDS == 10 * 60
    assert LOCK_SECONDS == 10 * 60


# --- B-44: 4 回ではロックしない ----------------------------------------------------------------
def test_b44_four_failures_do_not_lock(clock: FakeClock) -> None:
    lockout = _lockout(clock)

    results = [lockout.record_failure(KEY) for _ in range(4)]

    assert results == [False, False, False, False]
    assert lockout.is_locked(KEY) is False


# --- B-45: 5 回目で成立。成立させた呼出しだけ True を返す --------------------------------------
def test_b45_fifth_failure_establishes_the_lock(clock: FakeClock) -> None:
    lockout = _lockout(clock)
    for _ in range(4):
        assert lockout.record_failure(KEY) is False

    assert lockout.record_failure(KEY) is True
    assert lockout.is_locked(KEY) is True


def test_b45_after_lock_further_failures_are_not_counted(clock: FakeClock) -> None:
    """ロック中の試行は数えない（呼出元は照会しないため、そもそもここへ来ない）。"""
    lockout = _lockout(clock)
    for _ in range(5):
        lockout.record_failure(KEY)

    assert lockout.record_failure(KEY) is False
    assert lockout.is_locked(KEY) is True


# --- B-46: 成立から 10 分で自動解除。解除後は 0 から数え直す ------------------------------------
def test_b46_lock_expires_ten_minutes_after_establishment(clock: FakeClock) -> None:
    lockout = _lockout(clock)
    for _ in range(5):
        lockout.record_failure(KEY)

    clock.advance(LOCK_SECONDS - 1)
    assert lockout.is_locked(KEY) is True

    clock.advance(1)  # ちょうど 10 分
    assert lockout.is_locked(KEY) is False


def test_b46_counter_restarts_from_zero_after_expiry(clock: FakeClock) -> None:
    lockout = _lockout(clock)
    for _ in range(5):
        lockout.record_failure(KEY)
    clock.advance(LOCK_SECONDS)
    lockout.is_locked(KEY)  # 期限切れを確定させる（遅延削除）

    results = [lockout.record_failure(KEY) for _ in range(4)]

    assert results == [False, False, False, False]
    assert lockout.is_locked(KEY) is False


# --- 数えない事象との切り分け（§2.4.1） -------------------------------------------------------
def test_success_resets_the_counter(clock: FakeClock) -> None:
    """成功時は 0 に戻す。4 回失敗 → 成功 → 4 回失敗ではロックしない。"""
    lockout = _lockout(clock)
    for _ in range(4):
        lockout.record_failure(KEY)

    lockout.reset(KEY)

    assert [lockout.record_failure(KEY) for _ in range(4)] == [False, False, False, False]
    assert lockout.is_locked(KEY) is False


def test_reset_clears_an_established_lock(clock: FakeClock) -> None:
    lockout = _lockout(clock)
    for _ in range(5):
        lockout.record_failure(KEY)

    lockout.reset(KEY)

    assert lockout.is_locked(KEY) is False


# --- 滑り窓（直近 10 分） ----------------------------------------------------------------------
def test_failures_outside_the_window_are_dropped(clock: FakeClock) -> None:
    """10 分を超えて間隔が空いた失敗は数えない（窓の外）。"""
    lockout = _lockout(clock)
    lockout.record_failure(KEY)

    clock.advance(WINDOW_SECONDS)  # ちょうど 10 分 → 窓の外

    assert [lockout.record_failure(KEY) for _ in range(4)] == [False, False, False, False]
    assert lockout.is_locked(KEY) is False


def test_failures_inside_the_window_are_summed(clock: FakeClock) -> None:
    """窓の内側（直近 10 分）の失敗は合算される（5 回目で成立）。"""
    lockout = _lockout(clock)
    for _ in range(4):
        lockout.record_failure(KEY)
        clock.advance(100)

    assert lockout.record_failure(KEY) is True


# --- 計数のキーは平文の社員コードではない（§8.1） --------------------------------------------
def test_key_is_a_hash_and_never_the_plain_code() -> None:
    lockout = LoginLockout()

    key = lockout.key_for("1234567")

    assert len(key) == 64
    assert "1234567" not in key
    assert key.isalnum()


def test_key_is_stable_within_an_instance_and_differs_across_instances() -> None:
    """salt はプロセス起動ごとに生成する。同一プロセス内では同じ社員コード → 同じキー。"""
    first = LoginLockout()
    second = LoginLockout()

    assert first.key_for("1234567") == first.key_for("1234567")
    assert first.key_for("1234567") != second.key_for("1234567")
    assert first.key_for("1234567") != first.key_for("1234568")


def test_lock_scope_is_per_employee_code(clock: FakeClock) -> None:
    """ロックは当該社員コードのみ。他の社員コードは影響を受けない（§2.4.1「ロックの範囲」）。"""
    lockout = _lockout(clock)
    locked_key = lockout.key_for("1234567")
    other_key = lockout.key_for("1234568")
    for _ in range(5):
        lockout.record_failure(locked_key)

    assert lockout.is_locked(locked_key) is True
    assert lockout.is_locked(other_key) is False
