/**
 * 接口サービス（3 端点・05 §2.3・§2.4・§2.6・§4.2）と Session 破棄要求（§2.9）。
 *
 * 端点は**3 本で固定**であること、`credentials: "same-origin"` を必ず付けること（工程04 §1.1 #6）、
 * 403 でも本文を読むこと（E-203／E-206 は JSON 本文を持つ）を固定する。
 * `fetch` は差し替える（外部への通信は行わない）。
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { generateUrl, init, login, requestSessionPurge } from "../services/loginApi";

type FetchMock = ReturnType<typeof vi.fn>;

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => body,
    headers: new Headers(headers),
  } as unknown as Response;
}

let fetchMock: FetchMock;

function lastCall(): [string, RequestInit] {
  return fetchMock.mock.calls.at(-1) as [string, RequestInit];
}

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("postJson（3 端点）", () => {
  it("init は本文なしで POST し、Cookie を送る（credentials: same-origin）", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { errorCode: "0" }));

    const result = await init();
    const [path, options] = lastCall();

    expect(path).toBe("/R60Login/init");
    expect(options.method).toBe("POST");
    expect(options.credentials).toBe("same-origin");
    expect(options.body).toBeUndefined();
    expect(result.body.errorCode).toBe("0");
  });

  it("login は camelCase の JSON 本文を送る（接口層は camelCase・規則 03 §4）", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { errorCode: "0" }));

    await login({ encryptedStfCd: "VAL_1", stfKbn: "3", gmnId: "VAL_2", kgnKbn: "Y" });
    const [path, options] = lastCall();

    expect(path).toBe("/R60Login/login");
    expect(options.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(options.body))).toEqual({
      encryptedStfCd: "VAL_1",
      stfKbn: "3",
      gmnId: "VAL_2",
      kgnKbn: "Y",
    });
  });

  it("generateUrl は `/R60Login/generateUrl` へ平文の stfCd を送る（裁定 Q-231）", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { errorCode: "0", url: "VAL_1" }));

    const result = await generateUrl({ stfCd: "VAL_2" });
    const [path, options] = lastCall();

    expect(path).toBe("/R60Login/generateUrl");
    expect(JSON.parse(String(options.body))).toEqual({ stfCd: "VAL_2" });
    expect(result.body.url).toBe("VAL_1");
  });

  it("403 でも本文を読む（E-203／E-206 の文言を捨てない）", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(403, { errorCode: "2", errorDetailCode: "R60E0001", errorMessage: "MSG_1" }),
    );

    const result = await init();

    expect(result.status).toBe(403);
    expect(result.body.errorMessage).toBe("MSG_1");
  });

  it("`Date` ヘッダを serverDate として返す（JST 補正の材料・05 §8.4）", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(200, { errorCode: "0" }, { Date: "Tue, 27 Oct 2026 14:30:00 GMT" }),
    );

    expect((await init()).serverDate).toBe("Tue, 27 Oct 2026 14:30:00 GMT");
  });

  it("`Date` ヘッダが無ければ serverDate は null", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { errorCode: "0" }));

    expect((await init()).serverDate).toBeNull();
  });
});

describe("requestSessionPurge（L-208 ステップ3）", () => {
  it("設定された要求先へ POST し、Cookie を送る（credentials: include）", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, {}));

    const purged = await requestSessionPurge();
    const [path, options] = lastCall();

    expect(purged).toBe(true);
    expect(path).toBe("/api/session/purge");
    expect(options.method).toBe("POST");
    expect(options.credentials).toBe("include");
  });

  it("要求先が未設定なら false（サーバへは何も送らない）", async () => {
    vi.stubEnv("VITE_R60_SESSION_PURGE_URL", "");

    expect(await requestSessionPurge()).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("応答が成功でなければ false（例外にしない）", async () => {
    fetchMock.mockResolvedValue(jsonResponse(500, {}));

    expect(await requestSessionPurge()).toBe(false);
  });

  it("通信が例外でも false（呼出元は閉じるだけ・裁定 Q-228）", async () => {
    fetchMock.mockRejectedValue(new Error("VAL_1"));

    expect(await requestSessionPurge()).toBe(false);
  });
});
