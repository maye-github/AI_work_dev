/**
 * L-206 社員コード暗号化・復号の単体テスト（クライアント側）。
 *
 * TC-206（正常系）・TC-208／B-34・B-35（桁数境界）・B-33（日跨ぎ）に対応する。
 * 算式はサーバ側（`backend/app/domain/stf_cd_cipher.py`）と**同一**であるため、
 * 同じ入力に対して**同じ暗号化値**を返すことを 1 件固定する（05 §2.7「1 本の処理を両側に置く」）。
 *
 * **B-33（日跨ぎ）は「例外にならない」ことを固定する。** 暗号化時の日付と復号時の日付が異なると、
 * 例外ではなく**別の社員コード**が復号される（実測）。設計は E-205 を想定しているが、
 * 実挙動は SQL-3 0 件 → E-201 に落ちる。**試験は実測を固定する**（設計の書き換えは試験の仕事ではない）。
 */

import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createJstClock,
  decryptStfCd,
  encryptStfCd,
  jstYyyymmddFromEpochMs,
  StfCdCipherError,
} from "../common/stfCdCipher";

const KEY_DATE = "20261027";

describe("encryptStfCd", () => {
  it("7 桁は 5 桁目で分割し、ブロックを `_` で連結する（TC-206）", () => {
    // 1234567 → 各桁+1 = 2,3,4,5,6,7,8 → 前 2345／後 678
    // 前: 2 + 030405 = 2030405 → + 20261027 = 22291432
    // 後: 6 + 0708   = 60708   → + 20261027 = 20321735
    expect(encryptStfCd("1234567", KEY_DATE)).toBe("22291432_20321735");
  });

  it("サーバ側と同一の値を返す（同じ入力・同じ算式・1 本の処理）", () => {
    // backend/tests/test_stf_cd_cipher.py の同じ入力と同じ期待値である。
    expect(encryptStfCd("9999", KEY_DATE)).toBe("30362037");
  });

  it("4 桁以下は分割しない（B-34）", () => {
    const encrypted = encryptStfCd("1234", KEY_DATE);

    expect(encrypted).toBe("22291432");
    expect(encrypted).not.toContain("_");
  });

  it("各桁が 9 のとき桁上げせず 10 として扱う（B-35）", () => {
    // 99999 → 前 10,10,10,10／後 10
    expect(encryptStfCd("99999", KEY_DATE)).toBe("30362037_20261037");
  });

  it("同じ入力からは毎回同じ値が出る（冪等・規則 03 §7.1）", () => {
    expect(encryptStfCd("1234567", KEY_DATE)).toBe(encryptStfCd("1234567", KEY_DATE));
  });

  it("日付が変われば暗号化値も変わる", () => {
    expect(encryptStfCd("1234567", KEY_DATE)).not.toBe(encryptStfCd("1234567", "20261028"));
  });

  it.each([
    ["日付が 8 桁でない", "1234567", "2026-10-27"],
    ["日付が空", "1234567", ""],
    ["社員コードが数字でない", "12a4567", KEY_DATE],
    ["社員コードが空", "", KEY_DATE],
    ["社員コードに全角数字", "１２３４５６７", KEY_DATE],
  ])("%s なら StfCdCipherError（E-202／E-205 の判定材料）", (_label, plain, keyDate) => {
    expect(() => encryptStfCd(plain, keyDate)).toThrow(StfCdCipherError);
  });
});

describe("decryptStfCd", () => {
  it.each(["1234567", "1234", "9999", "99999", "1", "123456789"])(
    "%s を暗号化して復号すると元に戻る",
    (plain) => {
      expect(decryptStfCd(encryptStfCd(plain, KEY_DATE), KEY_DATE)).toBe(plain);
    },
  );

  it("B-33 日跨ぎ: 例外ではなく**別の社員コード**が復号される（実測を固定）", () => {
    const encrypted = encryptStfCd("1234567", KEY_DATE);

    const decrypted = decryptStfCd(encrypted, "20261028");

    expect(decrypted).not.toBe("1234567");
    // 設計（E-205）は日付不一致を検出できる前提だが、算式に検出手段が無い。
    // したがって実行時は SQL-3 0 件 → E-201 に落ちる。設計の改訂は環 n09 の担当である。
    expect(decrypted).toMatch(/^[0-9]+$/);
  });

  it.each([
    ["空文字", ""],
    ["区切りだけ", "_"],
    ["ブロックが 3 つ", "1_2_3"],
    ["数字以外を含む", "VAL_1"],
    ["減算できない（鍵日より小さい）", "1000"],
  ])("%s は StfCdCipherError", (_label, encrypted) => {
    expect(() => decryptStfCd(encrypted, KEY_DATE)).toThrow(StfCdCipherError);
  });

  it("日付が 8 桁でないなら StfCdCipherError", () => {
    expect(() => decryptStfCd("22291432", "2026-10-27")).toThrow(StfCdCipherError);
  });
});

describe("jstYyyymmddFromEpochMs", () => {
  it("UTC 14:30 は同日の JST 23:30", () => {
    expect(jstYyyymmddFromEpochMs(Date.UTC(2026, 9, 27, 14, 30))).toBe("20261027");
  });

  it("UTC 15:00 は翌日の JST 00:00（日跨ぎの境界）", () => {
    expect(jstYyyymmddFromEpochMs(Date.UTC(2026, 9, 27, 15, 0))).toBe("20261028");
  });
});

describe("createJstClock", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("`Date` ヘッダが無ければ端末時刻の JST を返す（差 0）", () => {
    vi.useFakeTimers();
    vi.setSystemTime(Date.UTC(2026, 9, 27, 14, 30));

    expect(createJstClock(null).yyyymmdd()).toBe("20261027");
  });

  it("解釈できない `Date` ヘッダも差 0 として扱う（例外にしない）", () => {
    vi.useFakeTimers();
    vi.setSystemTime(Date.UTC(2026, 9, 27, 14, 30));

    expect(createJstClock("not-a-date").yyyymmdd()).toBe("20261027");
  });

  it("サーバ時刻が進んでいれば、その差だけ補正した JST 日付を返す", () => {
    vi.useFakeTimers();
    vi.setSystemTime(Date.UTC(2026, 9, 27, 14, 30)); // 端末: JST 23:30（27 日）
    const serverDate = new Date(Date.UTC(2026, 9, 27, 15, 0)).toUTCString(); // サーバ: JST 00:00（28 日）

    expect(createJstClock(serverDate).yyyymmdd()).toBe("20261028");
  });
});
