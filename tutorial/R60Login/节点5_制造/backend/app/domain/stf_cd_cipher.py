"""L-206 社員コード暗号化・復号（共通処理・1 本に統合）。05 §2.7。

算式は 05 §2.7（上流 §10.3 の転記）のとおり。**AES-256-ECB ではない。**
判断を加えていない。順序は ①各桁 +1（桁上げしない・`9` は `10`）→ ②5 桁目で分割 →
③先頭はゼロ埋めなし・2 桁目以降は 2 桁ゼロ埋めで連結 → ④`yyyymmdd` を整数加算 →
⑤複数ブロックは `_` で連結 → ⑥復号は逆順。

* **日付は引数で受け取る**（05 §2.7 入力・規則 03 §7.1）。本モジュールは現在時刻を読まない。
  日付の取得は `today_jst_yyyymmdd()` の 1 箇所に閉じ、呼出元が引数として渡す（工程04 §6.3）。
* 同一入力＋同一日付 → 同一出力（決定的）。乱数・UUID を埋め込まない。
* 当日鍵の実値・平文／暗号化前後の実値はログに出さない（05 §8.1・§9）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# サーバのタイムゾーンは Asia/Tokyo（工程04 §1.4・§2.3）。当日鍵の日付判定は JST。
JST = timezone(timedelta(hours=9))

# 05 §2.7 境界規則: 分割境界は 5 桁目で固定（1〜4 桁目＝前、5 桁目以降＝後）。
_SPLIT_INDEX = 4


class StfCdCipherError(Exception):
    """暗号化・復号の失敗。呼出元が E-205（復号）／E-209（暗号化）へ振り分ける。"""


def today_jst_yyyymmdd(now: datetime | None = None) -> str:
    """サーバの JST 日付を `yyyymmdd` で返す（**日付の取得はこの 1 箇所のみ**）。

    `now` はテストで固定するための引数である（05 §2.7 順序・冪等性）。実運用では省略する。
    """
    current = now if now is not None else datetime.now(JST)
    return current.astimezone(JST).strftime("%Y%m%d")


def _validate_key_date(key_date: str) -> None:
    if len(key_date) != 8 or not key_date.isascii() or not key_date.isdigit():
        raise StfCdCipherError("key_date は 8 桁の半角数字（yyyymmdd）である")


def encrypt_stf_cd(plain_stf_cd: str, key_date: str) -> str:
    """平文社員コードを暗号化する。`key_date` は JST の `yyyymmdd`（引数注入）。"""
    _validate_key_date(key_date)
    if not plain_stf_cd or not plain_stf_cd.isascii() or not plain_stf_cd.isdigit():
        # 数字以外・0 桁は暗号化しない（05 §2.6 ステップ4 の可判定を呼出元が済ませている前提）。
        raise StfCdCipherError("平文社員コードは半角数字 1 桁以上である")

    # ① 各桁を +1（9 → "10"。次の桁へ桁上げしない）
    incremented = [str(int(ch) + 1) for ch in plain_stf_cd]

    # ② 5 桁目で固定分割。4 桁以下は分割しない（B-34）。
    blocks = [incremented] if len(incremented) <= _SPLIT_INDEX else [
        incremented[:_SPLIT_INDEX],
        incremented[_SPLIT_INDEX:],
    ]

    encrypted_blocks: list[str] = []
    for block in blocks:
        # ③ 先頭桁はゼロ埋めなし、2 桁目以降は 2 桁ゼロ埋めで連結
        block_text = block[0] + "".join(f"{int(value):02d}" for value in block[1:])
        # ④ 当日の yyyymmdd を整数加算
        encrypted_blocks.append(str(int(block_text) + int(key_date)))

    # ⑤ 複数ブロックは `_` で連結（1 ブロックなら付けない）
    return "_".join(encrypted_blocks)


def decrypt_stf_cd(encrypted_stf_cd: str, key_date: str) -> str:
    """暗号化社員コードを復号する。`key_date` は JST の `yyyymmdd`（引数注入）。

    05 §2.7 境界規則 6（復号は逆順）。不正な暗号化値は `StfCdCipherError` を送出する。
    """
    _validate_key_date(key_date)
    if not encrypted_stf_cd:
        raise StfCdCipherError("暗号化社員コードが空である")

    parts = encrypted_stf_cd.split("_")
    if len(parts) > 2:
        raise StfCdCipherError("ブロック数が 2 を超えている")
    if any(not part or not part.isascii() or not part.isdigit() for part in parts):
        raise StfCdCipherError("暗号化社員コードは半角数字と `_` のみで構成される")

    return "".join(_decrypt_block(part, key_date) for part in parts)


def _decrypt_block(block: str, key_date: str) -> str:
    # ④ の逆: 整数減算（引けない＝不正な暗号化値／日付の不一致）
    value = int(block) - int(key_date)
    if value < 0:
        raise StfCdCipherError("日付加算を戻せない")
    text = str(value)

    # ③ の逆: 先頭要素はゼロ埋めなし（1〜2 文字）。残余は 2 文字ずつ。
    # 先頭を 1 文字とすると残余長が奇数になる場合に限り、先頭は 2 文字（`10`）。
    first_length = 1 if (len(text) - 1) % 2 == 0 else 2
    first = text[:first_length]
    rest = text[first_length:]
    if len(rest) % 2 != 0:
        raise StfCdCipherError("ブロックの桁構成が不正である")

    elements = [first] + [rest[i : i + 2] for i in range(0, len(rest), 2)]
    digits: list[str] = []
    for element in elements:
        incremented = int(element)
        # ① の逆: `1`〜`10` のみが許される（`10` は元の `9`）
        if incremented < 1 or incremented > 10:
            raise StfCdCipherError("桁の値が範囲外である")
        digits.append(str(incremented - 1))
    return "".join(digits)
