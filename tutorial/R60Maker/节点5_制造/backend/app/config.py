"""設定の読込（方式のみ。値は環境変数から起動時に読む。実値を持たない）。

- DB 接続情報・タイムゾーン・Session 失効・オンライン稼働帯・共通部品の接続名を扱う。
- 敏感値（接続先・資格情報）はコードに埋め込まない。環境変数名のみを定義する（禁⑤・紅線⑦）。
- スタックは工程04 §1.2（Python 3.12 + FastAPI + SQLAlchemy Core + oracledb Thin）、DB は Oracle（§1.3）。
- NLS_DATE_FORMAT は顧客運用標準に従う（値は本コードで固定しない。Q-326）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo

TZ_TOKYO = ZoneInfo("Asia/Tokyo")

# オンライン稼働帯（平日 7:00–22:00 JST。L-212 手順②・設計 §6）。業務定数として設計に明記済み。
ONLINE_START = time(7, 0)
ONLINE_END = time(22, 0)

# Session の最終操作からの失効分（L-212 手順①・30 分）。
SESSION_IDLE_MINUTES = 30

# --- 設計 v1.0.1 で確定した値（環境依存ではないためコード内の定数とする）---
# D-207 send_sts の登録時既定値 = 0（未送信）。Q-315 の承認結果。
INITIAL_SEND_STS = "0"
# L-213（/init）が取得するメッセージ ID（D-211）: MSG-C-001〜004・MSG-I-001〜003・MSG-E-001〜008（15 件）。
INIT_MESSAGE_IDS: tuple[str, ...] = (
    "MSG-C-001",
    "MSG-C-002",
    "MSG-C-003",
    "MSG-C-004",
    "MSG-I-001",
    "MSG-I-002",
    "MSG-I-003",
    "MSG-E-001",
    "MSG-E-002",
    "MSG-E-003",
    "MSG-E-004",
    "MSG-E-005",
    "MSG-E-006",
    "MSG-E-007",
    "MSG-E-008",
)


@dataclass(frozen=True)
class Settings:
    """起動時設定。値はすべて環境変数から注入する。"""

    # DB 接続（実値は環境変数。ソースに実値を持たない）
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_sid: str

    # 顧客提供の共通部品 v3.0 の接続名（未提供の間は None＝未接続。Q-327）
    common_package: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        def required(name: str) -> str:
            value = os.environ.get(name)
            if value is None or value == "":
                raise RuntimeError(f"environment variable {name} is required")
            return value

        return cls(
            db_user=required("DB_USER"),
            db_password=required("DB_PASSWORD"),
            db_host=required("DB_HOST"),
            db_port=int(required("DB_PORT")),
            db_sid=required("DB_SID"),
            common_package=os.environ.get("COMMON_PACKAGE") or None,
        )

    def sqlalchemy_url(self) -> str:
        """接続 URL を設定から組み立てる（ソースに実値を持たない）。oracledb Thin（工程04 §1.2）。"""
        return (
            f"oracle+oracledb://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_sid}"
        )
