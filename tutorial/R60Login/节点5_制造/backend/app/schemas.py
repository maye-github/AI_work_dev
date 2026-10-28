"""入出力モデル（05 §4.1・§4.2 の端点フィールド。接口層は camelCase）。

`BaseCamelModel` を本案件で新規定義する（工程04 §4・規則 03 §2）。`model_config` の 4 行は固定であり、
派生モデルで再定義しない（禁② の趣旨。本案件は greenfield のため改変対象の既存基底は無く、
ここで定義したものが以後の唯一真源となる）。

3 系統の符号を混同しない（05 §4.4）:
* 画面・URL は `Y`/`N`、内部値 `1`/`0`（I-307）
* 物理フラグ列は `del_flg`/`valid_flg` が `0`/`1`、`ji_kjo_ksn_flg`/`ta_kjo_ksn_flg` が `'Y'`/`'N'`
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseCamelModel(BaseModel):
    """snake_case（定義層）⇄ camelCase（接口層）の唯一の変換点。4 行固定（規則 03 §2）。"""

    model_config = ConfigDict(
        alias_generator=to_camel,  # snake_case → camelCase を自動別名生成
        populate_by_name=True,  # 別名(camel)/原名(snake)どちらでも受入可
        serialize_by_alias=True,  # 応答は別名(camel)で出力（TS 接口層期待形に一致）
        extra="forbid",  # 未定義項目は 422 で拒否（余剰入力の混入防止）
    )


class OptionItem(BaseCamelModel):
    """I-314・I-315 の配列要素（`{value, label}`）。"""

    value: str
    label: str


class InitResponse(BaseCamelModel):
    """`POST /R60Login/init` の応答（I-314・I-315・I-318・I-319・I-321）。"""

    error_code: Literal["0", "1", "2"] = "0"  # I-318 正常0／業務1／システム2（05 §4.2）
    error_detail_code: str | None = None  # I-319 エラー時のみ（8 桁）
    error_message: str | None = None  # I-321（発番待ち）利用者向け文言。サーバが SQL-6 で取得
    # I-314／I-315 は正常時のみ載せる（異常応答に空配列を足さない・05 §4.2）。
    page_list: list[OptionItem] | None = None
    kbn_list: list[OptionItem] | None = None


class LoginRequest(BaseCamelModel):
    """`POST /R60Login/login` の要求。

    `encryptedStfCd`（I-313）**のみを使用する**。`stfKbn`（I-304）・`gmnId`（I-306）・
    `kgnKbn`（I-307）は同じ要求に載るが、**受信するだけで検証も保存もせず無視する**
    （否定の限定句。`受け取らない` と読み替えない。05 §4.2・Q-212）。
    """

    encrypted_stf_cd: str  # I-313（必須）
    stf_kbn: str | None = None  # I-304 受信のみ・無視
    gmn_id: str | None = None  # I-306 受信のみ・無視
    kgn_kbn: str | None = None  # I-307 受信のみ・無視


class UserInfo(BaseCamelModel):
    """I-316（6 項目）。SQL-4 の 1 行から生成する。"""

    stf_cd: str
    stf_nm: str
    cmp_cd: str
    cmp_nm: str
    jig_cd: str
    jig_nm: str


class MngInfo(BaseCamelModel):
    """I-317（5 項目）。SQL-5 の 1 行から生成する（供給元は社員マスタ・裁定 Q-229）。"""

    scmp_cd: str | None = None
    sjig_cd: str | None = None
    ji_kjo_ksn_flg: str | None = None  # 格納値は 'Y'/'N'（裁定 Q-234。変換しない）
    ta_kjo_ksn_flg: str | None = None
    login_acs_kais: int  # 0 以上の整数


class LoginResponse(BaseCamelModel):
    """`POST /R60Login/login` の応答（I-316・I-317・I-318・I-319・I-321）。

    E-201／E-207（該当なし）は **`errorCode` のみ**を返し、`errorDetailCode` も文言も載せない
    （裁定 Q-235・05 §5.7）。文言はクライアントが固定表示する。
    """

    error_code: Literal["0", "1", "2"] = "0"
    error_detail_code: str | None = None
    error_message: str | None = None
    user_info: UserInfo | None = None
    mng_info: MngInfo | None = None


class GenerateUrlRequest(BaseCamelModel):
    """`POST /R60Login/generateUrl` の要求（I-303 平文・I-304・I-306・I-307）。"""

    stf_cd: str = ""  # I-303 平文。未入力（空文字）は許容し、サーバが "NaN" を扱う（裁定 Q-231）
    stf_kbn: str | None = None  # I-304
    gmn_id: str | None = None  # I-306
    kgn_kbn: str | None = None  # I-307


class GenerateUrlResponse(BaseCamelModel):
    """`POST /R60Login/generateUrl` の応答（I-310・I-318・I-319・I-321）。"""

    error_code: Literal["0", "1", "2"] = "0"
    error_detail_code: str | None = None
    error_message: str | None = None
    url: str | None = None  # I-310（サーバが組み立てる。クライアントは表示のみ）
