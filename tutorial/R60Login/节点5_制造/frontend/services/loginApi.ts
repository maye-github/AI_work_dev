/**
 * 接口サービス（3 端点への呼出）。05 §2.3・§2.4・§2.6・§4.2。
 *
 * * フィールドは camelCase（接口層）。snake→camel の変換はサーバの `BaseCamelModel` が担う（規則 03 §2・§4）。
 * * 端点は 3 本で固定。本ファイルは `init` / `login` / `generateUrl` の 3 メソッドだけを持つ。
 * * Session 識別子は HttpOnly Cookie であり、クライアントは読まない。Cookie を送るため
 *   `credentials: "same-origin"` を指定する（工程04 §1.1 #6・§1.5）。
 * * 文言（`errorMessage`）はサーバが SQL-6 で取得して載せる（05 §5.7）。E-201／E-207 は載らない。
 */

export type ErrorCode = "0" | "1" | "2";

export interface OptionItem {
  value: string;
  label: string;
}

/** `POST /R60Login/init` の応答（I-314・I-315・I-318・I-319・I-321）。 */
export interface InitResponse {
  errorCode: ErrorCode;
  errorDetailCode?: string;
  errorMessage?: string;
  pageList?: OptionItem[];
  kbnList?: OptionItem[];
}

/** `POST /R60Login/login` の要求。`encryptedStfCd`（I-313）のみがサーバで使用される。 */
export interface LoginRequest {
  encryptedStfCd: string;
  stfKbn?: string | null;
  gmnId?: string | null;
  kgnKbn?: string | null;
}

/** I-316（6 項目）。 */
export interface UserInfo {
  stfCd: string;
  stfNm: string;
  cmpCd: string;
  cmpNm: string;
  jigCd: string;
  jigNm: string;
}

/** I-317（5 項目）。フラグ 2 項目は `'Y'`／`'N'` をそのまま受ける（裁定 Q-234）。 */
export interface MngInfo {
  scmpCd?: string | null;
  sjigCd?: string | null;
  jiKjoKsnFlg?: string | null;
  taKjoKsnFlg?: string | null;
  loginAcsKais: number;
}

/** `POST /R60Login/login` の応答。E-201／E-207 は `errorCode` のみ（裁定 Q-235）。 */
export interface LoginResponse {
  errorCode: ErrorCode;
  errorDetailCode?: string;
  errorMessage?: string;
  userInfo?: UserInfo;
  mngInfo?: MngInfo;
}

/** `POST /R60Login/generateUrl` の要求。`stfCd` は **平文**（I-303）。 */
export interface GenerateUrlRequest {
  stfCd: string;
  stfKbn?: string | null;
  gmnId?: string | null;
  kgnKbn?: string | null;
}

/** `POST /R60Login/generateUrl` の応答（I-310 はサーバが組み立てた表示用 URL）。 */
export interface GenerateUrlResponse {
  errorCode: ErrorCode;
  errorDetailCode?: string;
  errorMessage?: string;
  url?: string;
}

/** HTTP status と応答本文。`serverDate` は `/init` の HTTP `Date` ヘッダ（JST 補正用・05 §8.4）。 */
export interface ApiResult<T> {
  status: number;
  body: T;
  serverDate: string | null;
}

async function postJson<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  const init: RequestInit = {
    method: "POST",
    credentials: "same-origin",
  };
  if (body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }

  const response = await fetch(path, init);
  // 403（E-203／E-206）も JSON 本文を持つため、status にかかわらず本文を読む。
  const data = (await response.json()) as T;
  return {
    status: response.status,
    body: data,
    serverDate: response.headers.get("Date"),
  };
}

/** `POST /R60Login/init`（L-201 → L-202）。パラメータなし。 */
export function init(): Promise<ApiResult<InitResponse>> {
  return postJson<InitResponse>("/R60Login/init");
}

/** `POST /R60Login/login`（L-201 → L-203）。 */
export function login(request: LoginRequest): Promise<ApiResult<LoginResponse>> {
  return postJson<LoginResponse>("/R60Login/login", request);
}

/** `POST /R60Login/generateUrl`（L-201 → L-205）。 */
export function generateUrl(request: GenerateUrlRequest): Promise<ApiResult<GenerateUrlResponse>> {
  return postJson<GenerateUrlResponse>("/R60Login/generateUrl", request);
}

function readEnv(name: string): string {
  const meta = import.meta as unknown as { env?: Record<string, string | undefined> };
  return meta.env?.[name] ?? "";
}

/**
 * L-208 ステップ3: 共通基盤の Session 管理機能へ破棄を要求する（05 §2.9）。
 *
 * 接続先は設計に仕様が無いため**環境変数**（`VITE_R60_SESSION_PURGE_URL`）で与える。未設定・失敗は
 * `false` を返し、呼出元は**追加の提示を出さずに閉じる**（ステップ4・裁定 Q-228）。
 * 本画面専用の端点を追加しない（05 §2.9 ステップ3）。
 */
export async function requestSessionPurge(): Promise<boolean> {
  const url = readEnv("VITE_R60_SESSION_PURGE_URL");
  if (url === "") {
    return false;
  }
  try {
    const response = await fetch(url, { method: "POST", credentials: "include" });
    return response.ok;
  } catch {
    return false;
  }
}
