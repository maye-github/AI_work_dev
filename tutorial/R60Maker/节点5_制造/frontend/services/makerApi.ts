/**
 * 接口サービス。6 端点（/init・/search・/download・/initEdit・/delete・/edit）への呼出。
 *
 * - 要求／応答は camelCase、外側は `{params:{...}}` の 1 階層（設計 §0）。
 * - 応答は HTTP 200 固定。判定は本文 errorCode を正とする（0=正常／1=業務／9=システム。2 を使わない）。
 * - 英語項目名は物理列名 snake_case から camelCase を機械導出したもの（Q-330）。
 */

export interface ApiEnvelope {
  errorCode: number;
  errorId: string;
  msgId?: string | null;
}

export interface MessageInfo {
  msgId: string;
  msgKind: string;
  msgTxt: string;
}

export interface MakerItem {
  makerCd: string;
  makerNm: string | null;
  makerKanaNm: string | null;
  sendSts: string | null;
  delFlg: string | null;
}

export interface Pager {
  pageNo: number;
  totalPages: number;
  pageSize: number;
  totalCount: number;
}

export interface InitParams {
  // L-213 は利用者入力を用いない
}

export interface SearchParams {
  makerCd?: string | null;
  makerNm?: string | null;
  includeDeleted?: boolean;
  pageSize?: number;
  shikakeMode?: boolean;
  pageNo?: number;
  sortField?: string | null;
}

export interface DownloadParams {
  makerCd?: string | null;
  makerNm?: string | null;
  includeDeleted?: boolean;
  pageSize?: number;
  shikakeMode?: boolean;
  sortField?: string | null;
}

export interface InitEditParams {
  mode: '1' | '2' | '3';
  makerCd?: string | null;
}

export interface DeleteParams {
  makerCd: string;
  makerNm?: string | null;
  makerKanaNm?: string | null;
  emergencyDispatch?: boolean;
  deleteFlg?: boolean;
  lastUpdateDatetime?: string | null;
  revNo?: number | null;
}

export interface EditParams {
  mode: '1' | '2' | '3';
  makerCd: string;
  makerNm?: string | null;
  makerKanaNm?: string | null;
  emergencyDispatch?: boolean;
  deleteFlg?: boolean;
  lastUpdateDatetime?: string | null;
  revNo?: number | null;
}

export interface InitResponse extends ApiEnvelope {
  serverTime?: string;
  companyNm?: string | null;
  deptNm?: string | null;
  userName?: string | null;
  pageSizeOptions: number[];
  pageSize: number;
  includeDeleted: boolean;
  shikakeMode: boolean;
  conditionExpanded: boolean;
  items: MakerItem[];
  totalCount: number;
  messageInfo: MessageInfo[];
}

export interface SearchResponse extends ApiEnvelope {
  items: MakerItem[];
  totalCount: number;
  pager: Pager | null;
}

export interface InitEditResponse extends ApiEnvelope {
  mode?: string;
  makerCd?: string | null;
  makerNm?: string | null;
  makerKanaNm?: string | null;
  emergencyDispatch: boolean;
  deleteFlg?: string | null;
  lastUpdateDatetime?: string | null;
  revNo?: number | null;
}

export interface EditResponse extends ApiEnvelope {
  items: MakerItem[];
  totalCount: number;
  pager: Pager | null;
}

export type DeleteResponse = EditResponse;

// 要求 §6 / 設計 §2.0: 経路は /R60Maker/<name>。前置きはコードに埋めない（CR-006・2026-11-10）
const BASE = '/R60Maker';

async function postJson<T>(path: string, params: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ params }),
  });
  return (await response.json()) as T;
}

export function init(params: InitParams = {}): Promise<InitResponse> {
  return postJson<InitResponse>('/init', params);
}

export function search(params: SearchParams): Promise<SearchResponse> {
  return postJson<SearchResponse>('/search', params);
}

export function initEdit(params: InitEditParams): Promise<InitEditResponse> {
  return postJson<InitEditResponse>('/initEdit', params);
}

export function edit(params: EditParams): Promise<EditResponse> {
  return postJson<EditResponse>('/edit', params);
}

export function remove(params: DeleteParams): Promise<DeleteResponse> {
  return postJson<DeleteResponse>('/delete', params);
}

export type DownloadResult =
  | { kind: 'file'; blob: Blob; filename: string }
  | { kind: 'error'; error: ApiEnvelope };

/** 応答が CSV ファイルかエラー JSON かの区別はクライアントで行う（設計 §2.7 手順⑤）。 */
export async function download(params: DownloadParams): Promise<DownloadResult> {
  const response = await fetch(`${BASE}/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ params }),
  });
  const contentType = response.headers.get('Content-Type') ?? '';
  if (contentType.includes('text/csv')) {
    const disposition = response.headers.get('Content-Disposition') ?? '';
    const match = /filename="([^"]+)"/.exec(disposition);
    return {
      kind: 'file',
      blob: await response.blob(),
      filename: match ? match[1] : 'maker_master.csv',
    };
  }
  return { kind: 'error', error: (await response.json()) as ApiEnvelope };
}
