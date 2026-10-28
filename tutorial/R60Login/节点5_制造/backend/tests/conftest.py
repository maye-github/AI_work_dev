"""単体テストの共通フィクスチャ（節点6。TC-201〜TC-221 のサーバ側）。

* **実 DB を使わない。** `Engine` を差し替え、SQL 本文の目印（表名）で応答を返す偽装を使う。
  これにより、Oracle を持たない環境でも端点の**分岐**を検証できる。
  差し替えているのは境界（Engine）だけであり、検証対象の logic は本物を通す。
* **現在時刻は注入する**（規則 03 §7.1）。暗号化の日付は呼出元と同じ `today_jst_yyyymmdd()` から取る。
* `app.state` を直接組み立てるため **lifespan を通さない**（設定の env 読込と実 Engine の生成を避ける）。
  したがって `TestClient` は `with` で包まない。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import SESSION_ABSOLUTE_SECONDS, SESSION_IDLE_SECONDS, Settings  # noqa: E402
from app.domain.login_lockout import LoginLockout  # noqa: E402
from app.domain.session_store import SessionStore  # noqa: E402
from app.domain.stf_cd_cipher import encrypt_stf_cd, today_jst_yyyymmdd  # noqa: E402
from app.main import app  # noqa: E402

# --- SQL の識別子（テストの断言で「どの SQL が走ったか」を数えるために使う） -------------------
SQL_OPERATION = "SQL-1"
SQL_PAGES = "SQL-2"
SQL_EMPLOYEE = "SQL-3"
SQL_USER_INFO = "SQL-4"
SQL_MNG_INFO = "SQL-5"
SQL_MESSAGE = "SQL-6"


class _Result:
    """SQLAlchemy `Result` のうち、本コードが使う 2 メソッドだけを持つ偽物。"""

    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self._rows = rows

    def first(self) -> tuple[Any, ...] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[tuple[Any, ...]]:
        return list(self._rows)


class _Connection:
    """`with engine.connect() as conn:` に応えるための最小の Connection。"""

    def __init__(self, db: "FakeDb") -> None:
        self._db = db

    def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> _Result:
        return self._db.execute(str(stmt), dict(params or {}))

    def __enter__(self) -> "_Connection":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


class FakeDb:
    """散文的な偽装 Engine。`connect()` と `execute()` だけを持つ。

    オプションは「その SQL が何を返すか／例外するか」を名前で与える。既定は**すべて正常**。
    """

    def __init__(self, **options: Any) -> None:
        self.operation_flg: Any = options.get("operation_flg", "1")
        self.operation_raises: bool = options.get("operation_raises", False)
        self.pages: list[tuple[Any, ...]] = list(options.get("pages", [("VAL_1", "VAL_2")]))
        self.pages_raises: bool = options.get("pages_raises", False)
        # 社員検証（SQL-3）の応答。bool を渡せば毎回同じ、list を渡せば先頭から順に消費する。
        self._employee = options.get("employee", True)
        self.user_row: tuple[Any, ...] | None = options.get(
            "user_row", ("EMP_1", "NAME_1", "CMP_1", "CMPNAME_1", "JIG_1", "JIGNAME_1")
        )
        self.mng_row: tuple[Any, ...] | None = options.get("mng_row", ("SCMP_1", "SJIG_1", "Y", "N", 3))
        self.user_raises: bool = options.get("user_raises", False)
        self.mng_raises: bool = options.get("mng_raises", False)
        self.messages: dict[str, str] = dict(options.get("messages") or {})
        self.messages_raises: bool = options.get("messages_raises", False)
        # 走った SQL の履歴（順序つき）。「実行していないこと」の断言に使う。
        self.calls: list[str] = []

    # --- Engine の顔 ---------------------------------------------------------------
    def connect(self) -> _Connection:
        return _Connection(self)

    def execute(self, sql: str, params: dict[str, Any]) -> _Result:
        identifier = self.identify(sql)
        self.calls.append(identifier)
        if identifier == SQL_OPERATION:
            if self.operation_raises:
                raise RuntimeError("SQL-1 failed")
            return _Result([] if self.operation_flg is None else [(self.operation_flg,)])
        if identifier == SQL_PAGES:
            if self.pages_raises:
                raise RuntimeError("SQL-2 failed")
            return _Result(self.pages)
        if identifier == SQL_EMPLOYEE:
            return _Result([(1,)] if self._next_employee() else [])
        if identifier == SQL_USER_INFO:
            if self.user_raises:
                raise RuntimeError("SQL-4 failed")
            return _Result([] if self.user_row is None else [self.user_row])
        if identifier == SQL_MNG_INFO:
            if self.mng_raises:
                raise RuntimeError("SQL-5 failed")
            return _Result([] if self.mng_row is None else [self.mng_row])
        if identifier == SQL_MESSAGE:
            if self.messages_raises:
                raise RuntimeError("SQL-6 failed")
            message = self.messages.get(str(params.get("error_detail_code")))
            return _Result([] if message is None else [(message,)])
        raise AssertionError(f"未知の SQL が発行された: {sql[:80]!r}")

    # --- SQL 本文から識別子を起こす（順序が意味を持つ: SQL-4/5 を SQL-3 より先に見る） ------
    @staticmethod
    def identify(sql: str) -> str:
        compact = " ".join(sql.split())
        if "SYS_CMN_TBL" in compact:
            return SQL_OPERATION
        if "GMN_MST" in compact:
            return SQL_PAGES
        if "ORG_JIG_MST" in compact:
            return SQL_USER_INFO
        if "login_acs_kais" in compact:
            return SQL_MNG_INFO
        if "CD_MSG_MST" in compact:
            return SQL_MESSAGE
        if "SELECT 1" in compact:
            return SQL_EMPLOYEE
        raise AssertionError(f"未知の SQL 本文: {compact[:80]!r}")

    def count(self, identifier: str) -> int:
        return self.calls.count(identifier)

    def _next_employee(self) -> bool:
        if isinstance(self._employee, list):
            return bool(self._employee.pop(0)) if self._employee else False
        return bool(self._employee)


class FakeClock:
    """ログイン試行ロックの時計（§2.4.1 の窓・解除を固定するため注入する）。"""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class LogCapture(logging.Handler):
    """運用ログの記録を集める（標準出力へ出さないため、専用 logger にだけ付ける）。"""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    def events(self, event: str) -> list[logging.LogRecord]:
        return [record for record in self.records if record.getMessage() == event]

    def result_codes(self, event: str) -> list[Any]:
        return [record.__dict__.get("result_code") for record in self.events(event)]


def make_settings(**overrides: Any) -> Settings:
    """`Settings` を env を経由せず組み立てる。値はすべて占位（禁⑤）。"""
    values: dict[str, Any] = {
        "db_user": "TBL_1",
        "db_password": "PWD_1",
        "db_host": "IP_1",
        "db_port": 1521,
        "db_service_name": "SID_1",
        "operation_key": "VAL_1",
        "url_scheme": "http",
        "url_host": "IP_1",
        "url_port": 8080,
        "url_context": "ctx",
        "url_route": "login",
        "session_purge_url": None,
    }
    values.update(overrides)
    return Settings(**values)


def encrypted_stf_cd(plain: str = "1234567") -> str:
    """当日（JST）の鍵で暗号化する。端点が使う日付と同じ関数から取る（B-33 を踏まない）。"""
    return encrypt_stf_cd(plain, today_jst_yyyymmdd())


@pytest.fixture(autouse=True)
def _reset_module_state() -> Iterator[None]:
    """`init_api` の連続失敗カウンタは module 変数なので、テスト間に持ち越さない。"""
    from app.api import init_api

    init_api._init_failure_counts.clear()
    yield
    init_api._init_failure_counts.clear()


@pytest.fixture
def harness():
    """`(client, capture, db)` を返す工場。`db` は引数で渡したものをそのまま返す。"""

    def _build(
        db: FakeDb,
        *,
        clock: FakeClock | None = None,
        settings: Settings | None = None,
    ) -> tuple[TestClient, LogCapture, FakeDb]:
        capture = LogCapture()
        logger = logging.getLogger("r60login.test")
        logger.handlers = [capture]
        logger.setLevel(logging.INFO)
        logger.propagate = False

        app.state.settings = settings or make_settings()
        app.state.engine = db
        app.state.logger = logger
        app.state.session_store = SessionStore(
            idle_seconds=SESSION_IDLE_SECONDS,
            absolute_seconds=SESSION_ABSOLUTE_SECONDS,
        )
        app.state.login_lockout = LoginLockout(clock=clock) if clock is not None else LoginLockout()
        return TestClient(app), capture, db

    return _build
