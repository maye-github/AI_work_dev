/**
 * ログイン画面（SCR-201）の単体テスト。TC-201・TC-203・TC-205・TC-209・TC-212 に対応する。
 *
 * 方針:
 * * 接口（`services/loginApi`）は差し替える。**画面の判定と遷移だけ**を対象にする。
 * * PrimeVue の `Button` / `InputText` / `Select` は**実物**を使う（利用者が触る要素そのものを見る）。
 *   `Dialog` だけは Teleport を避けるため差し替える（判定対象は L-208 の順序であり、Dialog の描画ではない）。
 * * 遷移先は環境変数（`vitest.config.ts` の `test.env`）。**実 URL は書かない**（禁⑤）。
 */

import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import PrimeVue from "primevue/config";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  init: vi.fn(),
  login: vi.fn(),
  generateUrl: vi.fn(),
  purge: vi.fn(),
}));

vi.mock("../services/loginApi", () => ({
  init: mocks.init,
  login: mocks.login,
  generateUrl: mocks.generateUrl,
  requestSessionPurge: mocks.purge,
}));

import { decryptStfCd, jstYyyymmddFromEpochMs } from "../common/stfCdCipher";
import { subInitSubmitFlg, subSetSubmitFlg } from "../common/submitGuard";
import { useSessionStateStore } from "../stores/sessionState";
import LoginScreen from "../views/LoginScreen.vue";

const E201_MESSAGE = "入力されたユーザーＩＤではログインできません。ユーザーＩＤをご確認ください。";

const INIT_OK = {
  status: 200,
  body: {
    errorCode: "0",
    pageList: [{ value: "VAL_1", label: "LABEL_1" }],
    kbnList: [
      { value: "Y", label: "LABEL_2" },
      { value: "N", label: "LABEL_3" },
    ],
  },
  serverDate: null,
};

const INIT_NO_PAGE = { status: 200, body: { errorCode: "0", pageList: [], kbnList: [] }, serverDate: null };

const LOGIN_OK = {
  status: 200,
  body: {
    errorCode: "0",
    userInfo: {
      stfCd: "VAL_1",
      stfNm: "VAL_2",
      cmpCd: "VAL_3",
      cmpNm: "VAL_4",
      jigCd: "VAL_5",
      jigNm: "VAL_6",
    },
    mngInfo: { loginAcsKais: 1 },
  },
  serverDate: null,
};

const DialogStub = {
  name: "Dialog",
  props: { visible: { type: Boolean, default: false } },
  emits: ["update:visible"],
  template: '<div v-if="visible" class="dialog-stub"><slot /></div>',
};

let assignSpy: ReturnType<typeof vi.fn>;
let closeSpy: ReturnType<typeof vi.spyOn>;
let order: string[];
let mounted: Array<{ unmount: () => void }> = [];

async function mountNow() {
  const pinia = createPinia();
  setActivePinia(pinia);
  const wrapper = mount(LoginScreen, {
    // PrimeVue は部品が `$primevue.config` を参照するため、設定だけは実物を入れる
    global: { plugins: [pinia, [PrimeVue, {}]], stubs: { Dialog: DialogStub } },
  });
  mounted.push(wrapper);
  await flushPromises();
  return wrapper;
}

async function mountScreen(initResult: unknown = INIT_OK) {
  mocks.init.mockResolvedValue(initResult);
  return mountNow();
}

function buttonByText(wrapper: ReturnType<typeof mount>, text: string) {
  const button = wrapper.findAll("button").find((candidate) => candidate.text() === text);
  if (!button) {
    throw new Error(`button not found: ${text}`);
  }
  return button;
}

beforeEach(() => {
  vi.clearAllMocks();
  // 二度送信フラグはモジュール内の 1 個の状態であり、テスト間に持ち越さない
  subInitSubmitFlg();
  window.localStorage.clear();
  order = [];
  assignSpy = vi.fn();
  Object.defineProperty(window, "location", {
    configurable: true,
    writable: true,
    value: { assign: assignSpy, href: "http://localhost/", origin: "http://localhost" },
  });
  vi.spyOn(window, "open").mockImplementation(() => ({}) as Window);
  closeSpy = vi.spyOn(window, "close").mockImplementation(() => {
    order.push("close");
  });
  mocks.purge.mockImplementation(async () => {
    order.push("purge");
    return true;
  });
  mocks.login.mockResolvedValue(LOGIN_OK);
  mocks.generateUrl.mockResolvedValue({ status: 200, body: { errorCode: "0", url: "VAL_1" }, serverDate: null });
});

afterEach(() => {
  for (const wrapper of mounted) {
    wrapper.unmount();
  }
  mounted = [];
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("初期表示（TC-201）", () => {
  it("画面名・説明文は固定値（全角空白を含む）", async () => {
    const wrapper = await mountScreen();

    expect(wrapper.find("h1").text()).toBe("共通マスタ　ログイン");
    expect(wrapper.text()).toContain("1：本店ユーザー、2：工場ユーザー、3：システム管理者");
  });

  it("1 件以上なら先頭候補を初期選択し、起動区分は `3`・権限区分は `Y`（L-202 ステップ7）", async () => {
    const wrapper = await mountScreen();

    expect((wrapper.find("#stfKbn").element as HTMLInputElement).value).toBe("3");
    // I-306 の選択値は選択部品の表示ラベルで確認する（先頭候補が選ばれている）
    expect(wrapper.text()).toContain("LABEL_1");
    expect(wrapper.text()).toContain("LABEL_2");
    expect(wrapper.text()).not.toContain("利用可能な画面がありません");
  });

  it("0 件はエラーではない（文言表示のみ・B-22）", async () => {
    const wrapper = await mountScreen(INIT_NO_PAGE);

    expect(wrapper.text()).toContain("利用可能な画面がありません");
    // エラー区分の文言（E-201 等）は出さない
    expect(wrapper.text()).not.toContain(E201_MESSAGE);
  });

  it("0 件では I-308（ログイン）と I-311（URL出力）を非活性にする（TC-209）", async () => {
    const wrapper = await mountScreen(INIT_NO_PAGE);

    expect(buttonByText(wrapper, "ログイン").attributes("disabled")).toBeDefined();
    expect(buttonByText(wrapper, "URL出力").attributes("disabled")).toBeDefined();
    // I-309（メニュー）は非活性の規定が無い
    expect(buttonByText(wrapper, "メニュー").attributes("disabled")).toBeUndefined();
  });

  it("1 件以上なら I-308／I-311 は活性", async () => {
    const wrapper = await mountScreen();

    expect(buttonByText(wrapper, "ログイン").attributes("disabled")).toBeUndefined();
    expect(buttonByText(wrapper, "URL出力").attributes("disabled")).toBeUndefined();
  });

  it("初期化が E-204（errorCode `2`）ならシステムエラー画面へ遷移する", async () => {
    await mountScreen({ status: 200, body: { errorCode: "2", errorMessage: "MSG_1" }, serverDate: null });

    expect(assignSpy).toHaveBeenCalledWith("/R60/system-error");
  });

  it("初期化が 403（E-206）ならオンライン利用エラー画面へ遷移する", async () => {
    await mountScreen({ status: 403, body: { errorCode: "2", errorMessage: "MSG_1" }, serverDate: null });

    expect(assignSpy).toHaveBeenCalledWith("/R60/online-unavailable");
  });

  it("初期化が `0`／`2` 以外なら文言のみ表示し、遷移しない", async () => {
    const wrapper = await mountScreen({
      status: 200,
      body: { errorCode: "1", errorMessage: "MSG_1" },
      serverDate: null,
    });

    expect(wrapper.text()).toContain("MSG_1");
    expect(assignSpy).not.toHaveBeenCalled();
  });

  it("初期化の通信が失敗しても画面は落ちない（運用側の出力に留める）", async () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    mocks.init.mockRejectedValue(new Error("VAL_1"));

    const wrapper = await mountNow();

    expect(errorSpy).toHaveBeenCalled();
    expect(wrapper.find("h1").exists()).toBe(true);
    expect(assignSpy).not.toHaveBeenCalled();
  });
});

describe("入力の正規化（L-207 ステップ2・裁定 Q-210）", () => {
  it("全角数字は半角へ写す（trim しない）", async () => {
    const wrapper = await mountScreen();

    await wrapper.find("#stfCd").setValue("１２３４５６７");

    expect((wrapper.find("#stfCd").element as HTMLInputElement).value).toBe("1234567");
  });

  it("前後の半角空白は残す（B-07。除去は判定側の仕事）", async () => {
    const wrapper = await mountScreen();

    await wrapper.find("#stfCd").setValue(" 1234567 ");

    expect((wrapper.find("#stfCd").element as HTMLInputElement).value).toBe(" 1234567 ");
  });

  it("全角数字で入力してもログインは通る（正規化してから判定する）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("１２３４５６７");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(mocks.login).toHaveBeenCalledTimes(1);
  });
});

describe("E-202（ログイン時の桁数・文字種・空欄・TC-212）", () => {
  it.each([
    ["6 桁", "123456"],
    ["8 桁", "12345678"],
    ["数字でない", "12a4567"],
    ["空欄", ""],
    ["前後に空白", " 1234567"],
  ])("%s は E-202 を表示し、`/login` を呼ばない", async (_label, value) => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue(value);

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain(E201_MESSAGE);
    expect(mocks.login).not.toHaveBeenCalled();
    expect(assignSpy).toHaveBeenCalledWith("/R60/session-error");
  });

  it("起動区分が値域外なら E-202（遷移しない）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");
    await wrapper.find("#stfKbn").setValue("9");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain(E201_MESSAGE);
    expect(mocks.login).not.toHaveBeenCalled();
  });

  it("送信中は二度目を受け付けない（L-207 ステップ1）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");
    mocks.login.mockImplementation(() => new Promise(() => undefined)); // 応答しない

    await buttonByText(wrapper, "ログイン").trigger("click");
    await wrapper.find("#stfCd").setValue("1234567");
    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(mocks.login).toHaveBeenCalledTimes(1);
  });
});

describe("ログイン成立（L-203・L-204）", () => {
  it("暗号化した I-313 を送り、起動区分・権限区分を添える", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    const request = mocks.login.mock.calls[0][0] as {
      encryptedStfCd: string;
      stfKbn: string;
      gmnId: string;
      kgnKbn: string;
    };
    expect(request.stfKbn).toBe("3");
    expect(request.gmnId).toBe("VAL_1");
    expect(request.kgnKbn).toBe("Y");
    // 暗号化値は当日の JST で復号して元に戻る（日付を引数で受ける設計の裏取り）
    expect(decryptStfCd(request.encryptedStfCd, jstYyyymmddFromEpochMs(Date.now()))).toBe("1234567");
  });

  it("成立するとログイン状態と権限区分を保持する", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(useSessionStateStore().loggedIn).toBe(true);
    expect(window.localStorage.getItem("r60login.kgnKbn")).toBe("Y");
  });

  it("遷移先は `/R60/{gmnId}?stfKbn=…` で、権限区分は URL に載せない（TC-203）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    const opened = vi.mocked(window.open).mock.calls[0][0] as string;
    expect(opened).toBe("/R60/VAL_1?stfKbn=3");
    expect(opened).not.toContain("kgnKbn");
  });

  it("新しいウィンドウが開けないときは同一ウィンドウで遷移する（上流 §12 #11。エラーにしない）", async () => {
    vi.mocked(window.open).mockReturnValue(null);
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(assignSpy).toHaveBeenCalledWith("/R60/VAL_1?stfKbn=3");
  });

  it("メニューは `/login` を共用し、同一ウィンドウで `stfKbn` のみを渡す（TC-203）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "メニュー").trigger("click");
    await flushPromises();

    expect(mocks.login).toHaveBeenCalledTimes(1);
    expect(assignSpy).toHaveBeenCalledWith("/R60/menu?stfKbn=3");
    expect(window.open).not.toHaveBeenCalled();
  });

  it("E-201（errorCode `1`）は固定文言を表示し、ログイン成立として扱わない", async () => {
    mocks.login.mockResolvedValue({ status: 200, body: { errorCode: "1" }, serverDate: null });
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain(E201_MESSAGE);
    expect(useSessionStateStore().loggedIn).toBe(false);
    expect(assignSpy).toHaveBeenCalledWith("/R60/session-error");
  });

  it("403（E-203）はオンライン利用エラー画面へ遷移する", async () => {
    mocks.login.mockResolvedValue({ status: 403, body: { errorCode: "2", errorMessage: "MSG_1" }, serverDate: null });
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(assignSpy).toHaveBeenCalledWith("/R60/online-unavailable");
    expect(useSessionStateStore().loggedIn).toBe(false);
  });

  it("E-208（errorCode `2`）はシステムエラー画面へ遷移する", async () => {
    mocks.login.mockResolvedValue({
      status: 200,
      body: { errorCode: "2", errorMessage: "MSG_1" },
      serverDate: null,
    });
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(assignSpy).toHaveBeenCalledWith("/R60/system-error");
    expect(useSessionStateStore().loggedIn).toBe(false);
  });

  // E-205（暗号化の例外）は**画面から到達できない**。7 桁の ASCII 数字を判定済みで
  // 日付源は常に 8 桁を返すため、`encryptStfCd` は例外を投げない。分岐は防御として残し、
  // 未実行であることをカバレッジレポートに記す（規則 02 §10・規則 04 §9）。
});

describe("URL出力（L-205）", () => {
  it("応答の URL を表示する（組立と桁数判定はサーバ・裁定 Q-233）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(mocks.generateUrl).toHaveBeenCalledWith({
      stfCd: "1234567",
      stfKbn: "3",
      gmnId: "VAL_1",
      kgnKbn: "Y",
    });
    expect((wrapper.find("#urlText").element as HTMLInputElement).value).toBe("VAL_1");
  });

  it("E-202 は遷移せず文言のみ（遷移先へ飛ばさない）", async () => {
    mocks.generateUrl.mockResolvedValue({
      status: 200,
      body: { errorCode: "1", errorMessage: "MSG_1" },
      serverDate: null,
    });
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("MSG_1");
    expect(assignSpy).not.toHaveBeenCalled();
  });

  it("起動区分が値域外なら E-202 を表示し、`/generateUrl` を呼ばない", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");
    await wrapper.find("#stfKbn").setValue("9");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain(E201_MESSAGE);
    expect(mocks.generateUrl).not.toHaveBeenCalled();
  });

  it("403（E-206）はオンライン利用エラー画面へ遷移する", async () => {
    mocks.generateUrl.mockResolvedValue({
      status: 403,
      body: { errorCode: "2", errorMessage: "MSG_1" },
      serverDate: null,
    });
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(assignSpy).toHaveBeenCalledWith("/R60/online-unavailable");
  });

  it("E-209（errorCode `2`）はシステムエラー画面へ遷移する", async () => {
    mocks.generateUrl.mockResolvedValue({
      status: 200,
      body: { errorCode: "2", errorMessage: "MSG_1" },
      serverDate: null,
    });
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(assignSpy).toHaveBeenCalledWith("/R60/system-error");
  });

  it("表示した URL は編集できるが、編集値は遷移に使わない（裁定 Q-213）", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");
    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    await wrapper.find("#urlText").setValue("VAL_9");

    expect((wrapper.find("#urlText").element as HTMLInputElement).value).toBe("VAL_9");
    expect(assignSpy).not.toHaveBeenCalled();
  });
});

describe("画面終了（L-208・TC-205）", () => {
  it("ログイン成立前は破棄要求を行わず、そのまま閉じる", async () => {
    const wrapper = await mountScreen();

    await buttonByText(wrapper, "閉じる").trigger("click");
    await buttonByText(wrapper, "はい").trigger("click");
    await flushPromises();

    expect(mocks.purge).not.toHaveBeenCalled();
    expect(order).toEqual(["close"]);
  });

  it("ログイン成立後は**閉じる前に**破棄を要求し、権限区分を削除する", async () => {
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");
    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    await buttonByText(wrapper, "閉じる").trigger("click");
    await buttonByText(wrapper, "はい").trigger("click");
    await flushPromises();

    expect(order).toEqual(["purge", "close"]);
    expect(window.localStorage.getItem("r60login.kgnKbn")).toBeNull();
  });

  it("破棄要求が失敗しても閉じる（失効でも回収される・裁定 Q-228）", async () => {
    mocks.purge.mockResolvedValue(false);
    const wrapper = await mountScreen();
    await wrapper.find("#stfCd").setValue("1234567");
    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    await buttonByText(wrapper, "閉じる").trigger("click");
    await buttonByText(wrapper, "はい").trigger("click");
    await flushPromises();

    expect(closeSpy).toHaveBeenCalledTimes(1);
    expect(window.localStorage.getItem("r60login.kgnKbn")).toBeNull();
  });

  it("キャンセルなら何もしない（閉じない・破棄しない）", async () => {
    const wrapper = await mountScreen();

    await buttonByText(wrapper, "閉じる").trigger("click");
    await buttonByText(wrapper, "キャンセル").trigger("click");
    await flushPromises();

    expect(order).toEqual([]);
    expect(wrapper.find(".dialog-stub").exists()).toBe(false);
  });
});

describe("画面部品からの入力と二度押し（I-307・L-205）", () => {
  /** 画面のフォームは `stfCd` / `stfKbn`（InputText）と `gmnId` / `kgnKbn`（Select）で構成される。 */
  function selects(wrapper: ReturnType<typeof mount>) {
    return wrapper.findAllComponents({ name: "Select" });
  }

  it("権限区分に N を選ぶと、N のまま送信し保持する（L-207 ステップ7）", async () => {
    const wrapper = await mountScreen();
    const found = selects(wrapper);
    expect(found).toHaveLength(2);
    found[1].vm.$emit("update:modelValue", "N");
    await flushPromises();

    await wrapper.find("#stfCd").setValue("1234567");
    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(mocks.login.mock.calls[0][0]).toMatchObject({ kgnKbn: "N" });
    expect(window.localStorage.getItem("r60login.kgnKbn")).toBe("N");
  });

  it("権限区分が Y/N 以外なら E-202 で止まり、送信しない（L-207 ステップ7）", async () => {
    const wrapper = await mountScreen();
    selects(wrapper)[1].vm.$emit("update:modelValue", "X");
    await flushPromises();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain(E201_MESSAGE);
    expect(mocks.login).not.toHaveBeenCalled();
    expect(assignSpy).not.toHaveBeenCalled();
  });

  it("一覧の選択がそのまま I-306 として送信に載る（L-204 ステップ4）", async () => {
    const wrapper = await mountScreen({
      status: 200,
      body: {
        errorCode: "0",
        pageList: [
          { value: "VAL_1", label: "LABEL_1" },
          { value: "VAL_2", label: "LABEL_2" },
        ],
        kbnList: [{ value: "Y", label: "LABEL_3" }],
      },
      serverDate: null,
    });
    selects(wrapper)[0].vm.$emit("update:modelValue", "VAL_2");
    await flushPromises();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "ログイン").trigger("click");
    await flushPromises();

    expect(mocks.login.mock.calls[0][0]).toMatchObject({ gmnId: "VAL_2" });
  });

  it("URL 出力でも権限区分が値域外なら E-202 で止まり、送信しない（L-205）", async () => {
    const wrapper = await mountScreen();
    selects(wrapper)[1].vm.$emit("update:modelValue", "X");
    await flushPromises();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain(E201_MESSAGE);
    expect(mocks.generateUrl).not.toHaveBeenCalled();
  });

  it("二度押し中は URL 出力を実行しない（L-205 冒頭の subCheckSubmit）", async () => {
    const wrapper = await mountScreen();
    // 送信中を模す（フラグはモジュール内の 1 個の状態。beforeEach で必ず戻す）
    subSetSubmitFlg();
    await wrapper.find("#stfCd").setValue("1234567");

    await buttonByText(wrapper, "URL出力").trigger("click");
    await flushPromises();

    expect(mocks.generateUrl).not.toHaveBeenCalled();
  });
});
