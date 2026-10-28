"""FastAPI 起動・DI（設定・DB 接続）。工程04 §5.1 の `app.main:app`。

* **設定値を持たない。** DB 接続情報・URL 組立用の値・稼働フラグの共通キーは、
  起動時に環境変数／シークレット注入から読む（工程04 §3.2・禁⑤）。
* 接続は SQLAlchemy Core ＋ oracledb（Thin）。**ORM マッピングは作らない**（工程04 §1.2・§1.6 #4）。
* Oracle セッションの `NLS_DATE_FORMAT` は `RR-MM-DD` 固定（規則 00 §2・工程04 §2.3）。
* ログは標準出力へ 1 行 1 JSON（構造化）。社員コードは中間を `*` に置換済みのものだけを出す（工程04 §6.2）。
* Session ストアは**プロセス内辞書 + TTL**（OQ-05 の裁定・05 §8.2）。**複数インスタンス構成では共有されない**
  （差異は `06_設計との差異.md` に記録する）。
* **試行ロックの計数もプロセス内**に持つ（05 §2.4.1・v1.0.5）。同じく単一インスタンス前提である。
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator

from fastapi import FastAPI, Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.api.generate_url_api import router as generate_url_router
from app.api.init_api import router as init_router
from app.api.login_api import router as login_router
from app.config import Settings
from app.domain.login_lockout import LoginLockout
from app.domain.session_store import SessionStore
from app.domain.stf_cd_cipher import JST

# 工程04 §6.2: ログへ出してよい項目（それ以外は formatter が捨てる）。
# `instance_id` / `request_id` は 05 §8.1 の運用ログ 5 項目（時刻・画面ID・結果コード・インスタンスID・
# 要求ID）を満たすために足した（v1.0.5・BUG-002）。
_LOG_EXTRA_KEYS = (
    "screen_id",
    "kgn_kbn",
    "stf_cd_masked",
    "result_code",
    "msg_id",
    "error_type",
    "instance_id",
    "request_id",
)

# プロセス識別子（起動ごとに 1 つ）。利用者の要求 ID は要求ごとに払い出す。
_INSTANCE_ID = uuid.uuid4().hex
_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class _LogContextFilter(logging.Filter):
    """全レコードへ `instance_id` と `request_id` を注入する（05 §8.1・工程04 §6.2）。

    呼出し側が毎回 `extra` で渡すと抜けが出るため、**ハンドラのフィルタで 1 箇所に固定**する。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.instance_id = _INSTANCE_ID
        record.request_id = _REQUEST_ID.get()
        return True


class JsonLineFormatter(logging.Formatter):
    """標準出力へ 1 行 1 JSON を出す（工程04 §6.2）。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, JST).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in _LOG_EXTRA_KEYS:
            if key in record.__dict__:
                payload[key] = record.__dict__[key]
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _configure_logging() -> logging.Logger:
    logger = logging.getLogger("r60login")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonLineFormatter())
        handler.addFilter(_LogContextFilter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 二重出力を避ける（出力先は標準出力の 1 本）
    return logger


logger = _configure_logging()


def _set_nls_date_format(engine: Engine) -> None:
    """接続ごとに `NLS_DATE_FORMAT='RR-MM-DD'` を固定する（規則 00 §2・工程04 §2.3）。"""

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        try:
            cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'RR-MM-DD'")
        finally:
            cursor.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # 起動時に 1 回だけ設定を読む（工程04 §3.2）。必須の環境変数が無ければ起動しない。
    settings = Settings.from_env()
    engine = create_engine(settings.database_url(), pool_pre_ping=True)
    _set_nls_date_format(engine)

    app.state.settings = settings
    app.state.engine = engine
    app.state.logger = logger
    # L-203 ステップ6・05 §8.2: 11 項目を保持するサーバ側 Session（プロセス内辞書 + TTL）。
    app.state.session_store = SessionStore(
        idle_seconds=settings.session_idle_seconds,
        absolute_seconds=settings.session_absolute_seconds,
    )
    # L-203 §2.4.1・05 v1.0.5: 試行ロックの計数（プロセス内・単一インスタンス前提）。
    app.state.login_lockout = LoginLockout()
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="R60Login API", lifespan=lifespan)


@app.middleware("http")
async def _request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """要求 ID を払い出してログの文脈に載せる（05 §8.1 の運用ログ 5 項目）。

    上流のゲートウェイが `X-Request-ID` を付ける場合はそれを**そのまま使う**（相関のため採番し直さない）。
    """
    token = _REQUEST_ID.set(request.headers.get("X-Request-ID") or uuid.uuid4().hex)
    try:
        return await call_next(request)
    finally:
        _REQUEST_ID.reset(token)

# 端点は 3 本で固定（05 §1.3）。4 本目を設けない。
app.include_router(init_router)
app.include_router(login_router)
app.include_router(generate_url_router)
