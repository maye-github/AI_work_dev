"""設定の読込（R60Login / F-201・D-201）。

* 05 §2.3・§2.5・§2.6・§8.2 と工程04 §3.2 の「値の取得方式」だけを実装する。
* **値は持たない。** DB 接続情報・URL 組立用の値・稼働フラグの共通キーは、
  起動時に環境変数（又はシークレット注入）から読む。コード・リポジトリに実値を置かない（禁⑤）。
* Session の失効秒数（idle 30 分／絶対 8 時間）は設計の水準値であり、環境ごとに変えない（05 §8.2）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote_plus

# 05 §8.2 の水準値。設定ではなく設計値なので環境変数にしない（値を変えない）。
SESSION_IDLE_SECONDS = 30 * 60
SESSION_ABSOLUTE_SECONDS = 8 * 60 * 60


class SettingsError(RuntimeError):
    """必須の環境変数が無いときに送出する（起動時に落とす）。"""


def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise SettingsError(f"環境変数 {name} が未設定である")
    return value


def _required_int(name: str) -> int:
    raw = _required(name)
    try:
        return int(raw)
    except ValueError as exc:  # 数値でない値を起動時に拒否する
        raise SettingsError(f"環境変数 {name} が整数でない") from exc


@dataclass(frozen=True)
class Settings:
    """起動時に 1 回だけ組み立てる不変の設定（工程04 §3.2「起動時に読む」）。"""

    # DB 接続情報（占位: TBL_1 / PWD_1 / IP_1 / PORT_1 / SID_1）
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_service_name: str
    # 稼働判定（SQL-1）の cmn_key。値は環境設定で与える（裁定 Q-234）
    operation_key: str
    # URL 組立（L-205 ステップ6・裁定 Q-233）
    url_scheme: str
    url_host: str
    url_port: int
    url_context: str
    # 05 §2.6 の URL 形 `{scheme}://{host}:{port}/{context}/{route}` の `{route}`。
    # 設計は値も設定キーも定めていないため、環境変数で受けざるを得ない（未確定・ノード3 へ）。
    url_route: str
    # L-208 ステップ3 の Session 破棄要求の接続先（裁定 Q-232）。
    # 破棄の実行主体はクライアント（05 §2.9）であり、本版は前端の `VITE_R60_SESSION_PURGE_URL` を用いる。
    # 本項目は**予約**（サーバから要求する構成へ移す場合に使う）。差異登記 #2 を参照。
    session_purge_url: str | None
    session_idle_seconds: int = SESSION_IDLE_SECONDS
    session_absolute_seconds: int = SESSION_ABSOLUTE_SECONDS

    @staticmethod
    def from_env() -> "Settings":
        purge_url = os.environ.get("R60_SESSION_PURGE_URL") or None
        return Settings(
            db_user=_required("R60_DB_USER"),
            db_password=_required("R60_DB_PASSWORD"),
            db_host=_required("R60_DB_HOST"),
            db_port=_required_int("R60_DB_PORT"),
            db_service_name=_required("R60_DB_SERVICE_NAME"),
            operation_key=_required("R60_OPERATION_KEY"),
            url_scheme=_required("R60_URL_SCHEME"),
            url_host=_required("R60_URL_HOST"),
            url_port=_required_int("R60_URL_PORT"),
            url_context=_required("R60_URL_CONTEXT"),
            url_route=_required("R60_URL_ROUTE"),
            session_purge_url=purge_url,
        )

    def database_url(self) -> str:
        """oracledb（Thin）接続用の DSN。値は環境変数由来であり、ログには出さない。"""
        return (
            f"oracle+oracledb://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/?service_name={quote_plus(self.db_service_name)}"
        )
