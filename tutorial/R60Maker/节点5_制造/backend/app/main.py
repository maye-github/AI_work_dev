"""FastAPI 起動・DI（設定・DB 接続・Session ストア・共通部品境界）。

- スタックは工程04 §1.2（Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy Core + oracledb Thin）、DB は Oracle（§1.3）。
- 設定値は持たない。環境変数から起動時に読む（`app.config`）。
- 共通部品 v3.0（ReferenceChecker・EmergencyDispatcher・共通ログ）は当方の薄い境界越しに使う（`app.ports`。Q-327）。
- 起動対象は `uvicorn app.main:app`（工程04 §4.1）。
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from app.api import (
    delete_api,
    download_api,
    edit_api,
    init_api,
    init_edit_api,
    search_api,
)
from app.config import SESSION_IDLE_MINUTES, Settings
from app.domain.preprocess import ServiceError, SessionInfo
from app.ports import EmergencyDispatcher, ReferenceChecker


@dataclass
class _Session:
    info: SessionInfo
    last_seen: datetime


class SessionStore:
    """サーバ側 Session と「最後に実行した検索条件」をプロセス内メモリに保持する。

    Q-325（未裁定・AI 案に従う暫定）: 単一プロセス前提。多インスタンス構成では Session が共有されず
    L-212 手順①の水準（30 分）を満たさないため、外部ストアへ差し替えること。
    """

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._last_search: dict[str, object] = {}

    def register(self, token: str, info: SessionInfo, now: datetime) -> None:
        self._sessions[token] = _Session(info=info, last_seen=now)

    def touch(self, token: str, now: datetime) -> SessionInfo | None:
        session = self._sessions.get(token)
        if session is None:
            return None
        if now - session.last_seen > timedelta(minutes=SESSION_IDLE_MINUTES):
            return None
        session.last_seen = now
        return session.info

    def set_last_search(self, token: str, params: object) -> None:
        self._last_search[token] = params

    def get_last_search(self, token: str) -> object | None:
        return self._last_search.get(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    engine = create_engine(settings.sqlalchemy_url(), pool_pre_ping=True)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_store = SessionStore()
    app.state.reference_checker = ReferenceChecker(connected=settings.common_package is not None)
    app.state.dispatcher = EmergencyDispatcher(connected=settings.common_package is not None)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="R60Maker", lifespan=lifespan)


@app.exception_handler(ServiceError)
async def _handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
    # HTTP ステータスはすべて 200。判定は本文 errorCode（設計 §5）。
    return JSONResponse(
        status_code=200,
        content={"errorCode": exc.error_code, "errorId": exc.error_id, "msgId": exc.msg_id},
    )


@app.exception_handler(Exception)
async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
    # DB 例外・想定外は E-223（9／9999）。ロールバックはトランザクション境界（engine.begin）が担う。
    return JSONResponse(
        status_code=200,
        content={"errorCode": 9, "errorId": "9999", "msgId": None},
    )


app.include_router(init_api.router, prefix="/R60Maker")
app.include_router(search_api.router, prefix="/R60Maker")
app.include_router(download_api.router, prefix="/R60Maker")
app.include_router(init_edit_api.router, prefix="/R60Maker")
app.include_router(delete_api.router, prefix="/R60Maker")
app.include_router(edit_api.router, prefix="/R60Maker")
