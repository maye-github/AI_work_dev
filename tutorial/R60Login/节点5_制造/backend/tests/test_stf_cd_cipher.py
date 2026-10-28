"""L-206 暗号化・復号の単体テスト（TC-206・TC-208、B-33〜B-35）。

値は占位（`COL_1` 相当の数字列）のみ。実在の社員コードは使わない（禁⑤）。
"""

from __future__ import annotations

import re

import pytest

from app.domain.stf_cd_cipher import (
    StfCdCipherError,
    decrypt_stf_cd,
    encrypt_stf_cd,
    today_jst_yyyymmdd,
)

KEY_DATE = "20261027"


# --- TC-208 / B-35: 5 桁目の分割境界 ---------------------------------------------------------
def test_tc208_five_digits_are_split_into_two_blocks() -> None:
    """5 桁は 1〜4 桁目／5 桁目で 2 ブロックに分かれ、`_` で 1 個だけ連結される。"""
    encrypted = encrypt_stf_cd("12345", KEY_DATE)

    assert encrypted.count("_") == 1
    first, second = encrypted.split("_")
    # 前ブロックは 4 桁分（+1 後の最大 4 要素 → 先頭 1 桁＋2 桁×3 ＋ 当日 8 桁加算）
    assert first.isdigit()
    assert second.isdigit()
    assert decrypt_stf_cd(encrypted, KEY_DATE) == "12345"


def test_tc208_four_digits_are_not_split() -> None:
    """B-34: 4 桁は分割しない（`_` を付けない）。"""
    encrypted = encrypt_stf_cd("1234", KEY_DATE)

    assert "_" not in encrypted
    assert decrypt_stf_cd(encrypted, KEY_DATE) == "1234"


def test_tc208_boundary_between_four_and_five_digits_differs() -> None:
    """B-34／B-35 の差が現れることを、同じ入力の形で押さえる（4 桁は `_` 無し、5 桁は有り）。"""
    four = encrypt_stf_cd("1234", KEY_DATE)
    five = encrypt_stf_cd("12345", KEY_DATE)

    assert ("_" in four, "_" in five) == (False, True)


# --- 算式そのもの（規則 03 §7.1 の決定性） ----------------------------------------------------
def test_encryption_is_deterministic() -> None:
    """同一入力＋同一日付 → 同一出力（現在時刻・乱数を使わない）。"""
    assert encrypt_stf_cd("1234567", KEY_DATE) == encrypt_stf_cd("1234567", KEY_DATE)


def test_nine_carries_into_ten_without_carrying_to_the_next_digit() -> None:
    """① の各桁 +1 は桁上げしない（`9` は `10`）。4 桁すべて 9 の期待値を固定する。"""
    # "9999" → ["10","10","10","10"] → "10101010" → + 20261027 = 30362037
    assert encrypt_stf_cd("9999", KEY_DATE) == "30362037"
    assert decrypt_stf_cd("30362037", KEY_DATE) == "9999"


@pytest.mark.parametrize("plain", ["1", "12", "1234", "12345", "1234567", "99999", "1000000"])
def test_round_trip_returns_the_original(plain: str) -> None:
    assert decrypt_stf_cd(encrypt_stf_cd(plain, KEY_DATE), KEY_DATE) == plain


# --- TC-206: 7 桁を暗号化した I-313 は 17 桁以内（`^[0-9_]+$`） --------------------------------
@pytest.mark.parametrize("plain", ["1234567", "9999999", "1000000"])
def test_tc206_seven_digits_stay_within_seventeen_characters(plain: str) -> None:
    encrypted = encrypt_stf_cd(plain, KEY_DATE)

    assert re.fullmatch(r"[0-9_]+", encrypted) is not None
    assert len(encrypted) <= 17


# --- TC-215 / 分岐: 復号不能な値は例外（呼出元が E-205 へ振り分ける） ---------------------------
@pytest.mark.parametrize(
    "bad_value",
    [
        "",  # 空
        "ABC",  # 非数字
        "1_2_3",  # 3 ブロック
        "20261027",  # 減算すると 0 になり、桁の値域（1〜10）を外れる
        "1000",  # 日付より小さい（整数減算が負になる）
    ],
)
def test_tc215_invalid_encrypted_value_raises(bad_value: str) -> None:
    with pytest.raises(StfCdCipherError):
        decrypt_stf_cd(bad_value, KEY_DATE)


@pytest.mark.parametrize("bad_key_date", ["2026-10-27", "", "2026102", "2026102a"])
def test_invalid_key_date_raises(bad_key_date: str) -> None:
    with pytest.raises(StfCdCipherError):
        encrypt_stf_cd("1234567", bad_key_date)
    with pytest.raises(StfCdCipherError):
        decrypt_stf_cd("22291432", bad_key_date)


@pytest.mark.parametrize("bad_plain", ["", "12a4", "１２３４"])
def test_encrypt_rejects_non_digit_plain(bad_plain: str) -> None:
    with pytest.raises(StfCdCipherError):
        encrypt_stf_cd(bad_plain, KEY_DATE)


# --- B-33（日跨ぎ）: 設計は E-205 を想定するが、算式は例外を出さない ---------------------------
def test_b33_day_rollover_produces_a_different_code_not_an_error() -> None:
    """B-33 の実測を固定する（設計の書き換えは本テストの役目ではない）。

    暗号化した日と復号する日が違うと、**別の社員コードに化ける**。算式は剰余を持たないため
    `StfCdCipherError` にならない。呼出元では「SQL-3 が 0 件 → E-201」となる。
    設計（05 §7.7 B-33）は E-205 を想定しており、この差は 節点7 で裁定する。
    """
    encrypted = encrypt_stf_cd("1234567", "20261027")

    decrypted = decrypt_stf_cd(encrypted, "20261028")

    assert decrypted != "1234567"


# --- today_jst_yyyymmdd は 1 箇所に閉じる（引数でテスト固定できる） ------------------------------
def test_today_jst_is_injectable() -> None:
    from datetime import datetime, timezone

    fixed = datetime(2026, 10, 27, 23, 30, tzinfo=timezone.utc)  # JST では翌日 08:30

    assert today_jst_yyyymmdd(fixed) == "20261028"
