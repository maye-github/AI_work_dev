"""Pydantic v2 モデル。接口（TS）は camelCase、定義層（Python）は snake_case。

- `BaseCamelModel` を本案件で**新規定義**し、`model_config` の 4 行を固定する（規則 03 §2・工程04 §1.2）。
- 派生モデルで `model_config` を**再定義しない**（継承で 4 行を引き継ぐ）。
- 英語項目名は物理列名 snake_case から `alias_generator=to_camel` で機械導出する（Q-330）。
  変換点はこの 1 箇所だけ。手書きの snake↔camel 変換を散在させない（規則 03 §4）。
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseCamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )


# ---------------------------------------------------------------------------
# 要求モデル（`{params:{...}}` の 1 階層・camelCase）
# ---------------------------------------------------------------------------
class InitParams(BaseCamelModel):
    """L-213 は要求項目を定義しない（利用者入力を用いない）。"""


class InitRequest(BaseCamelModel):
    params: InitParams = Field(default_factory=InitParams)


class SearchParams(BaseCamelModel):
    maker_cd: str | None = None
    maker_nm: str | None = None
    include_deleted: bool = False
    page_size: int = 20
    shikake_mode: bool = False
    page_no: int = 1
    sort_field: str | None = None


class SearchRequest(BaseCamelModel):
    params: SearchParams = Field(default_factory=SearchParams)


class DownloadParams(BaseCamelModel):
    maker_cd: str | None = None
    maker_nm: str | None = None
    include_deleted: bool = False
    page_size: int = 20
    shikake_mode: bool = False
    sort_field: str | None = None


class DownloadRequest(BaseCamelModel):
    params: DownloadParams = Field(default_factory=DownloadParams)


class InitEditParams(BaseCamelModel):
    mode: str
    maker_cd: str | None = None


class InitEditRequest(BaseCamelModel):
    params: InitEditParams


class DeleteParams(BaseCamelModel):
    maker_cd: str
    maker_nm: str | None = None
    maker_kana_nm: str | None = None
    emergency_dispatch: bool = False
    delete_flg: bool = False
    last_update_datetime: datetime | None = None
    rev_no: int | None = None


class DeleteRequest(BaseCamelModel):
    params: DeleteParams


class EditParams(BaseCamelModel):
    mode: str
    maker_cd: str
    maker_nm: str | None = None
    maker_kana_nm: str | None = None
    emergency_dispatch: bool = False
    delete_flg: bool = False
    last_update_datetime: datetime | None = None
    rev_no: int | None = None


class EditRequest(BaseCamelModel):
    params: EditParams


# ---------------------------------------------------------------------------
# 応答モデル（共通規則: HTTP 200 固定、判定は本文 errorCode。errorId は 4 桁・正常 0000）
# ---------------------------------------------------------------------------
class ApiResponse(BaseCamelModel):
    error_code: int = 0
    error_id: str = "0000"
    msg_id: str | None = None


class MessageInfo(BaseCamelModel):
    msg_id: str
    msg_kind: str
    msg_txt: str


class MakerItem(BaseCamelModel):
    """一覧 5 列。送信状態・削除は名称（D-210 cd_nm）を返し、コードを直接返さない（I-347／I-349）。"""

    maker_cd: str
    maker_nm: str | None = None
    maker_kana_nm: str | None = None
    send_sts: str | None = None
    del_flg: str | None = None


class Pager(BaseCamelModel):
    page_no: int
    total_pages: int
    page_size: int
    total_count: int


class InitResponse(ApiResponse):
    server_time: str | None = None
    company_nm: str | None = None
    dept_nm: str | None = None
    user_name: str | None = None
    page_size_options: list[int] = Field(default_factory=lambda: [10, 20, 50, 100])
    page_size: int = 20
    include_deleted: bool = False
    shikake_mode: bool = False
    condition_expanded: bool = True
    items: list[MakerItem] = Field(default_factory=list)
    total_count: int = 0
    message_info: list[MessageInfo] = Field(default_factory=list)


class SearchResponse(ApiResponse):
    items: list[MakerItem] = Field(default_factory=list)
    total_count: int = 0
    pager: Pager | None = None


class InitEditResponse(ApiResponse):
    """マスタ画面（SCR-202）の 9 項目の初期値と、mode=3 の排他情報。

    ボタン活性など表示制御は L-221（クライアント）がデータから導く。サーバは値を返すのみ。
    """

    mode: str | None = None
    maker_cd: str | None = None
    maker_nm: str | None = None
    maker_kana_nm: str | None = None
    emergency_dispatch: bool = False
    delete_flg: str | None = None
    last_update_datetime: datetime | None = None
    rev_no: int | None = None


class EditResponse(ApiResponse):
    """完了時: マスタ画面を閉じ、最後の検索条件で 1 頁目を再検索した一覧を返す（L-220／L-219 手順⑧）。"""

    items: list[MakerItem] = Field(default_factory=list)
    total_count: int = 0
    pager: Pager | None = None


class DeleteResponse(ApiResponse):
    items: list[MakerItem] = Field(default_factory=list)
    total_count: int = 0
    pager: Pager | None = None
