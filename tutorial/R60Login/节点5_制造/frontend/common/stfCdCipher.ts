/**
 * L-206 社員コード暗号化・復号（クライアント側）。05 §2.7。
 *
 * 算式はサーバ側（`backend/app/domain/stf_cd_cipher.py`）と同一であり、1 本の処理を両側に置く
 * （05 §2.7「共通処理・1 本に統合」）。**AES-256-ECB ではない。**
 * 順序: ①各桁 +1（桁上げしない・`9` は `10`）→ ②5 桁目で分割 → ③先頭はゼロ埋めなし・
 * 2 桁目以降は 2 桁ゼロ埋めで連結 → ④`yyyymmdd` を整数加算 → ⑤複数ブロックは `_` で連結。
 *
 * **日付は引数で受け取る**（05 §2.7・規則 03 §7.1）。乱数・UUID・現在時刻を出力へ埋め込まない。
 * 日付の供給元は `/init` 応答の HTTP `Date` ヘッダで補正した JST（05 §8.4・§0.5 ①）。
 */

export class StfCdCipherError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "StfCdCipherError";
  }
}

/** 05 §2.7 境界規則: 分割境界は 5 桁目で固定（1〜4 桁目＝前、5 桁目以降＝後）。 */
const SPLIT_INDEX = 4;

const JST_OFFSET_MS = 9 * 60 * 60 * 1000;

function assertKeyDate(keyDate: string): void {
  if (!/^[0-9]{8}$/.test(keyDate)) {
    throw new StfCdCipherError("keyDate must be yyyymmdd");
  }
}

/** 平文社員コードを暗号化する。`keyDate` は JST の `yyyymmdd`（引数注入）。 */
export function encryptStfCd(plainStfCd: string, keyDate: string): string {
  assertKeyDate(keyDate);
  if (!/^[0-9]+$/.test(plainStfCd)) {
    throw new StfCdCipherError("plainStfCd must be ASCII digits");
  }

  // ① 各桁を +1（9 → "10"。次の桁へ桁上げしない）
  const incremented = Array.from(plainStfCd, (char) => String(Number(char) + 1));

  // ② 5 桁目で固定分割。4 桁以下は分割しない（B-34）
  const blocks: string[][] =
    incremented.length <= SPLIT_INDEX
      ? [incremented]
      : [incremented.slice(0, SPLIT_INDEX), incremented.slice(SPLIT_INDEX)];

  return blocks
    .map((block) => {
      // ③ 先頭桁はゼロ埋めなし、2 桁目以降は 2 桁ゼロ埋めで連結
      const first = block[0];
      const rest = block.slice(1).map((value) => value.padStart(2, "0")).join("");
      // ④ 当日の yyyymmdd を整数加算
      return String(Number(first + rest) + Number(keyDate));
    })
    .join("_"); // ⑤ 複数ブロックのみ `_` で連結
}

/** 暗号化社員コードを復号する。`keyDate` は JST の `yyyymmdd`（引数注入）。 */
export function decryptStfCd(encryptedStfCd: string, keyDate: string): string {
  assertKeyDate(keyDate);
  if (encryptedStfCd === "") {
    throw new StfCdCipherError("encryptedStfCd is empty");
  }

  const parts = encryptedStfCd.split("_");
  if (parts.length > 2) {
    throw new StfCdCipherError("too many blocks");
  }
  for (const part of parts) {
    if (!/^[0-9]+$/.test(part)) {
      throw new StfCdCipherError("encryptedStfCd must be ASCII digits and underscores");
    }
  }
  return parts.map((part) => decryptBlock(part, keyDate)).join("");
}

function decryptBlock(block: string, keyDate: string): string {
  // ④ の逆: 整数減算（引けない＝不正な暗号化値／日付の不一致）
  const value = Number(block) - Number(keyDate);
  if (!Number.isFinite(value) || value < 0) {
    throw new StfCdCipherError("cannot subtract keyDate");
  }
  const text = String(value);

  // ③ の逆: 先頭要素はゼロ埋めなし（1〜2 文字）。残余は 2 文字ずつ。
  // 先頭を 1 文字とすると残余長が奇数になる場合に限り、先頭は 2 文字（`10`）。
  const firstLength = (text.length - 1) % 2 === 0 ? 1 : 2;
  const first = text.slice(0, firstLength);
  const rest = text.slice(firstLength);
  if (rest.length % 2 !== 0) {
    throw new StfCdCipherError("invalid block layout");
  }

  const elements = [first];
  for (let index = 0; index < rest.length; index += 2) {
    elements.push(rest.slice(index, index + 2));
  }

  const digits = elements.map((element) => {
    const incremented = Number(element);
    // ① の逆: `1`〜`10` のみ許される（`10` は元の `9`）
    if (!Number.isFinite(incremented) || incremented < 1 || incremented > 10) {
      throw new StfCdCipherError("digit out of range");
    }
    return String(incremented - 1);
  });
  return digits.join("");
}

/** JST の日付（`yyyymmdd`）を返す時刻源。暗号化の直前に呼ぶ（05 §8.4）。 */
export interface JstClock {
  yyyymmdd(): string;
}

export function jstYyyymmddFromEpochMs(epochMs: number): string {
  const jst = new Date(epochMs + JST_OFFSET_MS);
  const year = jst.getUTCFullYear();
  const month = String(jst.getUTCMonth() + 1).padStart(2, "0");
  const day = String(jst.getUTCDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

/**
 * `/init` 応答の HTTP `Date` ヘッダ（サーバ時刻）と端末の UTC エポックとの差を保持し、
 * 補正した JST 日付を返す時刻源を作る（05 §2.7・§8.4）。
 * `Date` ヘッダが無い／解釈できない場合は端末の UTC エポックから換算する（差 0）。
 */
export function createJstClock(serverDateHeader: string | null, deviceNowMs: number = Date.now()): JstClock {
  const serverMs = serverDateHeader === null ? Number.NaN : Date.parse(serverDateHeader);
  const offsetMs = Number.isFinite(serverMs) ? serverMs - deviceNowMs : 0;
  return {
    yyyymmdd: (): string => jstYyyymmddFromEpochMs(Date.now() + offsetMs),
  };
}
