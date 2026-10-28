/**
 * ログイン成立の保持（Pinia）と権限区分の保持領域（工程04 §1.1・§6.4・05 §2.9 ステップ2）。
 *
 * L-208 ステップ2「ログイン成立前は破棄要求を行わない」の判定材料と、
 * 画面終了時の権限区分の明示削除を固定する。
 */

import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import {
  clearKgnKbn,
  KGN_KBN_STORAGE_KEY,
  saveKgnKbn,
  useSessionStateStore,
} from "../stores/sessionState";

describe("useSessionStateStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
  });

  it("初期状態は未ログイン", () => {
    expect(useSessionStateStore().loggedIn).toBe(false);
  });

  it("markLoggedIn で成立、reset で戻る", () => {
    const store = useSessionStateStore();

    store.markLoggedIn();
    expect(store.loggedIn).toBe(true);

    store.reset();
    expect(store.loggedIn).toBe(false);
  });

  it("同じ Pinia の中では同じ状態を共有する（画面と判定が同じ値を見る）", () => {
    useSessionStateStore().markLoggedIn();

    expect(useSessionStateStore().loggedIn).toBe(true);
  });

  it("Pinia を作り直せば初期状態から始まる（前回の成立を持ち越さない）", () => {
    useSessionStateStore().markLoggedIn();

    setActivePinia(createPinia());

    expect(useSessionStateStore().loggedIn).toBe(false);
  });
});

describe("権限区分の保持領域", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("キー名は設計値 `r60login.kgnKbn` に固定（工程04 §6.4）", () => {
    expect(KGN_KBN_STORAGE_KEY).toBe("r60login.kgnKbn");
  });

  it("保存した値を読める", () => {
    saveKgnKbn("Y");

    expect(window.localStorage.getItem("r60login.kgnKbn")).toBe("Y");
  });

  it("ログイン成立時は必ず上書きする（前回の値を残さない）", () => {
    saveKgnKbn("Y");
    saveKgnKbn("N");

    expect(window.localStorage.getItem("r60login.kgnKbn")).toBe("N");
  });

  it("clearKgnKbn で削除する（画面終了時の明示削除・工程04 §6.4）", () => {
    saveKgnKbn("N");

    clearKgnKbn();

    expect(window.localStorage.getItem("r60login.kgnKbn")).toBeNull();
  });

  it("値が無い状態で削除しても例外にしない（冪等）", () => {
    expect(() => clearKgnKbn()).not.toThrow();
  });
});
