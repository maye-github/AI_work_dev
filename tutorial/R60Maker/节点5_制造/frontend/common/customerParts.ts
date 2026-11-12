/**
 * 顧客提供の共通 UI ライブラリ v3.0 への薄い境界（再実装しない）。
 *
 * - 実体は未提供（工程04 でも未確定）。取得未提供の間は**未接続で起動できる**（Q-327）。
 * - 共通部品の機能を当方で再実装してはならない（工程04 §0 末尾）。
 * - スタックは工程04 §1.1（Vue 3 + TypeScript + Vite + PrimeVue）。
 */

export interface HeaderProps {
  title: string;
  systemTime: string;
  companyNm?: string;
  deptNm?: string;
  userName?: string;
}

export interface PagerProps {
  pageNo: number;
  totalPages: number;
  pageSize: number;
  disabled: boolean;
}

export type ErrorScreenKind = 'session' | 'online' | 'system';

export interface CustomerPartsBoundary {
  renderHeader(props: HeaderProps): void;
  renderPager(props: PagerProps): void;
  replaceWithErrorScreen(kind: ErrorScreenKind): void;
}

let parts: CustomerPartsBoundary | null = null;

/** 取得後に共通部品の実体を接続する。未接続の間は各呼出しが no-op となる。 */
export function bindCustomerParts(next: CustomerPartsBoundary): void {
  parts = next;
}

export function isConnected(): boolean {
  return parts !== null;
}

export function showHeader(props: HeaderProps): void {
  parts?.renderHeader(props);
}

export function showPager(props: PagerProps): void {
  parts?.renderPager(props);
}

export function replaceWithErrorScreen(kind: ErrorScreenKind): void {
  parts?.replaceWithErrorScreen(kind);
}

/**
 * `errorCode=9` の `errorId` から、置換先の画面種別を決める（設計 §5 の E-221〜E-223）。
 *
 * **2026-11-10 追加（BUG-003）。** それまで 6 箇所すべてが `'system'` を渡しており、
 * `ErrorScreenKind` に `'session'` / `'online'` を定義した意味が失われていた。
 * 設計 §5 は E-221（Session 30 分超過）→ SessionErrorScreen、E-222（稼働不可）→
 * OnlineControlErrorScreen、E-223（DB・想定外）→ SystemErrorScreen と書き分けている。
 */
export function errorScreenKindFor(errorId: string | null | undefined): ErrorScreenKind {
  switch (errorId) {
    case '9001':
      return 'session';
    case '9002':
      return 'online';
    default:
      return 'system';
  }
}
