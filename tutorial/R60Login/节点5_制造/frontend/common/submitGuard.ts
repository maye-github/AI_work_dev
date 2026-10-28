/**
 * L-207 二度送信防止の 3 部品。05 §2.8 ステップ1・8・9・§8.5・裁定 Q-221。
 *
 * 本案件で**新規定義**する（greenfield。既存の共通部品は無い。定義後はこれが唯一真源）。
 * 呼出し順は `subCheckSubmit` → `subSetSubmitFlg` → API → **`finally` で `subInitSubmitFlg`**。
 * フラグは呼出しごとに ON→OFF の対で閉じる（例外時も `finally` で必ず解放する）。
 */

/** 送信中フラグ。モジュール内に閉じ、外部から直接書き換えない。 */
let submitting = false;

/**
 * 二度送信を判定する。
 *
 * @returns `true`＝続行可（送信中でない）／`false`＝続行不可（送信中。何もしない）
 */
export function subCheckSubmit(): boolean {
  return !submitting;
}

/** API 呼出の直前にフラグを ON にする（05 §2.8 ステップ8）。 */
export function subSetSubmitFlg(): void {
  submitting = true;
}

/** フラグを OFF にする。**`finally` で必ず実行する**（05 §2.8 ステップ9）。 */
export function subInitSubmitFlg(): void {
  submitting = false;
}
