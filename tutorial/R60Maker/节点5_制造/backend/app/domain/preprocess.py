"""L-212 前処理（セッション → オンライン可否 → 権限 → 入力チェック）と共通エラー型。

- 手順①〜④のいずれか 1 つでも失敗したら後続を実行しない（設計 §2.1）。
- 例外（DB 例外・想定外）は E-223（9／9999）へ寄せる（各端点の汎用 except）。
- 権限: MKR01=参照／MKR02=参照＋登録・更新／MKR03=全操作。上位は下位を含む（設計 §2.1）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time

from sqlalchemy.engine import Connection

from app.config import ONLINE_END, ONLINE_START, TZ_TOKYO
from app.repository import queries


class ServiceError(Exception):
    """業務エラー／システムエラーを表す共通型。errorCode は 0／1／9（2 を使わない。設計 §5）。"""

    def __init__(self, error_code: int, error_id: str, msg_id: str | None = None) -> None:
        super().__init__(f"{error_code}/{error_id}")
        self.error_code = error_code
        self.error_id = error_id
        self.msg_id = msg_id


@dataclass(frozen=True)
class SessionInfo:
    user_id: str
    company_nm: str | None = None
    dept_nm: str | None = None
    user_name: str | None = None


# 端点別の必要権限レベル（設計 §2.1。上位は下位を含む）
AUTH_LEVEL = {"MKR01": 1, "MKR02": 2, "MKR03": 3}
REQUIRED_LEVEL = {
    "init": 1,
    "search": 1,
    "download": 3,
    "init_edit": 1,
    "delete": 3,
    "edit": 2,
}

# 境界値（設計 §6）
CODE_RE = re.compile(r"^[0-9A-Za-z]{1,5}$")
KANA_RE = re.compile(r"^[｡-ﾟ]+$")
NAME_FORBIDDEN = {",", "'", '"', "|"}
KANA_FORBIDDEN = {"'", ",", "¥", " "}
ALLOWED_PAGE_SIZES = {10, 20, 50, 100}
MAX_NAME_BYTES = 30
MAX_KANA_CHARS = 15


def _fail_input() -> None:
    # サーバ側入力チェック違反は E-224（1／2005）。文面は MSG-E-007/008 をクライアントが保持する（Q-329）。
    raise ServiceError(1, "2005", None)


def _check_code(value: str | None, required: bool) -> None:
    if value is None or value == "":
        if required:
            _fail_input()
        return
    if not CODE_RE.match(value):
        _fail_input()


def _check_name(value: str | None, required: bool) -> None:
    if value is None or value == "":
        if required:
            _fail_input()
        return
    if len(value.encode("utf-8")) > MAX_NAME_BYTES:
        _fail_input()
    if any(ch in NAME_FORBIDDEN for ch in value):
        _fail_input()


def _check_kana(value: str | None, required: bool) -> None:
    if value is None or value == "":
        if required:
            _fail_input()
        return
    if len(value) > MAX_KANA_CHARS:
        _fail_input()
    if not KANA_RE.match(value):
        _fail_input()
    if any(ch in KANA_FORBIDDEN for ch in value):
        _fail_input()


def _check_page_size(page_size: int) -> None:
    if page_size not in ALLOWED_PAGE_SIZES:
        _fail_input()


# ---------------------------------------------------------------------------
# 入力チェック（画面側と同一条件。設計 §6）
# ---------------------------------------------------------------------------
def validate_search(params) -> None:  # noqa: ANN001 - schemas.SearchParams
    _check_code(params.maker_cd, required=False)
    _check_name(params.maker_nm, required=False)
    _check_page_size(params.page_size)
    if params.page_no < 1:
        _fail_input()


def validate_download(params) -> None:  # noqa: ANN001 - schemas.DownloadParams
    _check_code(params.maker_cd, required=False)
    _check_name(params.maker_nm, required=False)
    _check_page_size(params.page_size)


def validate_init_edit(params) -> None:  # noqa: ANN001 - schemas.InitEditParams
    if params.mode not in ("1", "2", "3"):
        _fail_input()
    if params.mode == "3":
        _check_code(params.maker_cd, required=True)


def validate_delete(params) -> None:  # noqa: ANN001 - schemas.DeleteParams
    # 削除は緊急配信のオン・オフにかかわらず日本語名・カナ名必須（L-219 手順①）
    _check_code(params.maker_cd, required=True)
    _check_name(params.maker_nm, required=True)
    _check_kana(params.maker_kana_nm, required=True)


def validate_edit(params) -> None:  # noqa: ANN001 - schemas.EditParams
    _check_code(params.maker_cd, required=True)
    if params.mode in ("1", "2"):
        # 新規・複製: 緊急配信オンのとき名称必須、それ以外は任意（境界は 0〜30Byte／0〜15文字）
        _check_name(params.maker_nm, required=params.emergency_dispatch)
        _check_kana(params.maker_kana_nm, required=params.emergency_dispatch)
    elif params.mode == "3":
        # 修正: 緊急配信オン、または削除オンのとき名称必須
        names_required = params.emergency_dispatch or params.delete_flg
        _check_name(params.maker_nm, required=names_required)
        _check_kana(params.maker_kana_nm, required=names_required)
    else:
        _fail_input()


# ---------------------------------------------------------------------------
# 手順① セッション（存在し、最終操作から 30 分以内）
# ---------------------------------------------------------------------------
def _check_session(session_store, session_token: str | None, now: datetime) -> SessionInfo:
    info = session_store.touch(session_token, now) if session_token else None
    if info is None:
        # E-221（9／9001）。SessionErrorScreen へ置換。
        raise ServiceError(9, "9001", None)
    return info


# ---------------------------------------------------------------------------
# 手順② オンライン稼働の可否（平日 7:00–22:00 JST）
# ---------------------------------------------------------------------------
def _check_online(now: datetime) -> None:
    local = now.astimezone(TZ_TOKYO)
    weekday = local.weekday()  # 0=月曜
    if weekday >= 5 or not (ONLINE_START <= time(local.hour, local.minute) < ONLINE_END):
        # E-222（9／9002）。OnlineControlErrorScreen へ置換。
        raise ServiceError(9, "9002", None)


# ---------------------------------------------------------------------------
# 手順③ 権限（利用者 1 名につき 1 コード。上位は下位を含む）
# ---------------------------------------------------------------------------
def _check_permission(conn: Connection, user_id: str, required_level: int) -> None:
    auth_cd = queries.fetch_auth_cd(conn, user_id)
    level = AUTH_LEVEL.get(auth_cd) if auth_cd is not None else None
    if level is None or level < required_level:
        # E-220（1／2004）。処理中断・画面遷移しない。
        raise ServiceError(1, "2004", "MSG-E-006")


def preprocess(
    *,
    session_store,
    session_token: str | None,
    conn: Connection,
    endpoint: str,
    now: datetime,
    validate,
) -> SessionInfo:  # noqa: ANN001
    """①〜④を固定順で実行する。1 つ失敗したら後続を実行しない（設計 §2.1）。"""
    info = _check_session(session_store, session_token, now)  # ①
    _check_online(now)  # ②
    _check_permission(conn, info.user_id, REQUIRED_LEVEL[endpoint])  # ③
    validate()  # ④
    return info
