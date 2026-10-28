/**
 * ログイン成立の有無の保持（Pinia）。05 §2.9 ステップ2・工程04 §1.1。
 *
 * L-208 ステップ2「ログイン成立前なら破棄要求を行わない」の判定にのみ用いる。
 * Session 識別子は HttpOnly Cookie であり、**クライアントは読まない**（工程04 §1.1 #6）ため本ストアに持たない。
 *
 * `kgnKbn`（権限区分）は Pinia ではなく **同一オリジンの localStorage** に保持する（工程04 §6.4）。
 * キー名は `r60login.kgnKbn`、値は `Y`／`N`。ログイン成立時に上書きし、画面終了時に削除する。
 */

import { defineStore } from "pinia";
import { ref } from "vue";

/** 保持領域のキー名（工程04 §6.4。値を変えない）。 */
export const KGN_KBN_STORAGE_KEY = "r60login.kgnKbn";

export const useSessionStateStore = defineStore("sessionState", () => {
  /** ログイン成立の有無（`/login` が `errorCode="0"` を返した時点で `true`）。 */
  const loggedIn = ref(false);

  /** `/login` 成功時に呼ぶ（05 §2.9 ステップ2）。 */
  function markLoggedIn(): void {
    loggedIn.value = true;
  }

  /** 状態を初期化する。 */
  function reset(): void {
    loggedIn.value = false;
  }

  return { loggedIn, markLoggedIn, reset };
});

/** 権限区分を保持領域へ上書き保存する（ログイン成立時に必ず上書き・工程04 §6.4）。 */
export function saveKgnKbn(value: "Y" | "N"): void {
  window.localStorage.setItem(KGN_KBN_STORAGE_KEY, value);
}

/** 権限区分を保持領域から削除する（画面終了時に明示的に削除・工程04 §6.4）。 */
export function clearKgnKbn(): void {
  window.localStorage.removeItem(KGN_KBN_STORAGE_KEY);
}
