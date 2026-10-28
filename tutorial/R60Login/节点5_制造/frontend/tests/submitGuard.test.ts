/**
 * L-207 二度送信防止の 3 部品（05 §2.8 ステップ1・8・9・裁定 Q-221）。
 *
 * 部品は**モジュール内の 1 個のフラグ**を共有するため、テスト間で状態を持ち越さないよう
 * 毎回 `vi.resetModules()` して読み直す（規則 04 §9.2 冪等性）。
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

type Guard = typeof import("../common/submitGuard");

async function load(): Promise<Guard> {
  vi.resetModules();
  return import("../common/submitGuard");
}

describe("submitGuard", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("初期状態は送信中でない（続行可）", async () => {
    const { subCheckSubmit } = await load();

    expect(subCheckSubmit()).toBe(true);
  });

  it("ON の間は続行不可、OFF で戻る（ON→OFF の対）", async () => {
    const { subCheckSubmit, subSetSubmitFlg, subInitSubmitFlg } = await load();

    subSetSubmitFlg();
    expect(subCheckSubmit()).toBe(false);

    subInitSubmitFlg();
    expect(subCheckSubmit()).toBe(true);
  });

  it("ON を重ねても 1 回の OFF で戻る（カウンタではない）", async () => {
    const { subCheckSubmit, subSetSubmitFlg, subInitSubmitFlg } = await load();

    subSetSubmitFlg();
    subSetSubmitFlg();
    subInitSubmitFlg();

    expect(subCheckSubmit()).toBe(true);
  });

  it("例外が出ても finally で OFF にできる（二度と送れなくなる状態を作らない）", async () => {
    const { subCheckSubmit, subSetSubmitFlg, subInitSubmitFlg } = await load();

    subSetSubmitFlg();
    try {
      throw new Error("VAL_1");
    } catch {
      // 呼出元の finally を模す
    } finally {
      subInitSubmitFlg();
    }

    expect(subCheckSubmit()).toBe(true);
  });

  it("OFF を続けて呼んでも壊れない（冪等）", async () => {
    const { subCheckSubmit, subInitSubmitFlg } = await load();

    subInitSubmitFlg();
    subInitSubmitFlg();

    expect(subCheckSubmit()).toBe(true);
  });
});
