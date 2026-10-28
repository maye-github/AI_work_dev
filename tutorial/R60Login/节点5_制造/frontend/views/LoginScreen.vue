<script setup lang="ts">
/**
 * ログイン画面（SCR-201）。I-301〜I-312 の表示とイベント１〜５のクライアント側。
 * 05 §2.1・§2.3〜§2.9・§4.1・§6.3。技術スタックは工程04 §1.1（Vue 3 + `<script setup>` + TS strict + PrimeVue + Pinia）。
 *
 * * 画面は 1 枚。クライアント側ルータを持たない（工程04 §1.6 #3）。
 * * 入力の正規化（trim しない・全角→半角・非 ASCII 除去）は L-207 の実装（本ファイル）に置く（05 §2.8・§8.4）。
 * * 遷移の主体はクライアント（05 §6.3）。遷移先 URL は設計・工程04 に無いものがあり、その場合は遷移しない
 *   （実装で設計を補わない＝紅线②。阻塞項として報告する）。
 */

import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Select from "primevue/select";

import { createJstClock, encryptStfCd, StfCdCipherError } from "../common/stfCdCipher";
import type { JstClock } from "../common/stfCdCipher";
import { subCheckSubmit, subInitSubmitFlg, subSetSubmitFlg } from "../common/submitGuard";
import { generateUrl, init, login, requestSessionPurge } from "../services/loginApi";
import type { InitResponse, OptionItem } from "../services/loginApi";
import { clearKgnKbn, saveKgnKbn, useSessionStateStore } from "../stores/sessionState";

// I-301: 固定値。「共通マスタ　ログイン」（全角空白を含む。値を変えない）。
const PAGE_TITLE = "共通マスタ　ログイン";

// I-305: 固定値。05 §4.1 は「文字列（固定値）」とし、値の定義は上流（節点2 承認版 §4 #5）が唯一真源である。
const FIXED_DESCRIPTION = "1：本店ユーザー、2：工場ユーザー、3：システム管理者";

// 05 §6.2: E-201／E-202／E-205／E-207 はクライアントが固定文言を表示する（v1.0.2・C）。
// E-202 の文面は E-201 と**同一**である（同節の表。相違を設けない）。
const E201_MESSAGE = "入力されたユーザーＩＤではログインできません。ユーザーＩＤをご確認ください。";
const E202_MESSAGE = E201_MESSAGE;
const E205_MESSAGE = "ログイン情報を確認できませんでした。もう一度ログインしてください。";

// I-314 が 0 件のときの表示文言（05 §2.3 ステップ6・B-22）。
const NO_CANDIDATE_MESSAGE = "利用可能な画面がありません";

function readEnv(name: string): string {
  const meta = import.meta as unknown as { env?: Record<string, string | undefined> };
  return meta.env?.[name] ?? "";
}

// 顧客の共通基盤が提供する 4 画面（05 §1.2。メニューヘッダ＋エラー 3 種）への遷移先 URL は
// 設計・工程04 に無いため**環境変数**で与える。**未設定なら遷移しない**（現在の画面に留まる）。
// 本画面はメニューヘッダを呼ばない（遷移先の画面が呼ぶ）が、4 本を対で管理する。
type CommonScreen = "sessionError" | "onlineUnavailable" | "systemError" | "menuHeader";
const COMMON_SCREEN_ROUTES: Record<CommonScreen, string> = {
  sessionError: readEnv("VITE_R60_SESSION_ERROR_URL"),
  onlineUnavailable: readEnv("VITE_R60_ONLINE_UNAVAILABLE_URL"),
  systemError: readEnv("VITE_R60_SYSTEM_ERROR_URL"),
  menuHeader: readEnv("VITE_R60_MENU_HEADER_URL"),
};

// L-204 ステップ6（メニュー）の遷移先 SCR-202 の URL も、設計に無いため環境変数で与える。
const MENU_TARGET_ROUTE = readEnv("VITE_R60_MENU_URL");

const session = useSessionStateStore();

const pageOptions = ref<OptionItem[]>([]);
const kbnOptions = ref<OptionItem[]>([]);
const stfCdInput = ref("");
const stfKbn = ref("3");
const gmnId = ref("");
const kgnKbn = ref("Y");
const urlText = ref("");
const systemDateTime = ref("");
const message = ref("");
const candidateMessage = ref("");
const confirmVisible = ref(false);
const jstClock = ref<JstClock | null>(null);

let timerId: number | undefined;

const candidatesEmpty = computed(() => pageOptions.value.length === 0);
// I-308／I-311 は候補 0 件で非活性（05 §4.1・B-22）。I-309（メニュー）は非活性の規定が無い。
const loginDisabled = computed(() => candidatesEmpty.value);
const urlOutputDisabled = computed(() => candidatesEmpty.value);

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/** I-302: `YYYY/MM/DD HH:mm:ss`。取得元は**クライアント端末の時刻**（Q-218。当日鍵の日付とは別物）。 */
function formatSystemDateTime(date: Date): string {
  return (
    `${date.getFullYear()}/${pad2(date.getMonth() + 1)}/${pad2(date.getDate())} ` +
    `${pad2(date.getHours())}:${pad2(date.getMinutes())}:${pad2(date.getSeconds())}`
  );
}

function tick(): void {
  systemDateTime.value = formatSystemDateTime(new Date());
}

/**
 * L-207 ステップ2: 前後空白は trim せず、全角・非 ASCII を半角へ変換して除去する（Q-210）。
 * 全角 ASCII（U+FF01〜U+FF5E）だけ半角へ写し、残った非 ASCII を落とす。ASCII 空白は残る（B-07）。
 */
function normalizeStfCd(raw: string): string {
  let normalized = "";
  for (const char of raw) {
    const code = char.codePointAt(0) ?? 0;
    let halfWidth = char;
    if (code >= 0xff01 && code <= 0xff5e) {
      halfWidth = String.fromCharCode(code - 0xfee0);
    }
    const halfWidthCode = halfWidth.codePointAt(0) ?? 0;
    if (halfWidthCode < 0x80) {
      normalized += halfWidth;
    }
  }
  return normalized;
}

function onStfCdInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  stfCdInput.value = normalizeStfCd(target.value);
}

function navigateToCommonScreen(screen: CommonScreen): void {
  const route = COMMON_SCREEN_ROUTES[screen];
  if (route === "") {
    // 環境変数が未設定なら遷移しない（現在の画面に留まる）。
    return;
  }
  window.location.assign(route);
}

let simulationUndeterminedLogged = false;

/**
 * L-204 ステップ2: シミュレーション版かどうかの判定。
 *
 * I-314 は `{value, label}` のみで `gmn_kbn` を返さない（05 §4.2 I-314）ため、実際に得られる入力（I-306）
 * だけでは判定できない。**判定できないときは非シミュレーション版として扱い**、1 回だけ警告を出す
 * （差異登記 `06_設計との差異.md` に記載）。
 */
function isSimulationVersion(): boolean {
  if (!simulationUndeterminedLogged) {
    simulationUndeterminedLogged = true;
    console.warn("simulation version undetermined; treated as non-simulation", {
      gmnId: gmnId.value,
    });
  }
  return false;
}

/** L-204 ステップ2〜4: 遷移先は `/R60/{gmnId}`。クエリ順は `stfKbn` → `gmnKbn`（工程04 §6.1）。 */
function buildTransitionUrl(startupKbn: string): string {
  const simulation = isSimulationVersion();
  const routeId = simulation ? gmnId.value.slice(0, -1) : gmnId.value;
  let url = `/R60/${routeId}?stfKbn=${startupKbn}`;
  if (simulation) {
    url += `&gmnKbn=${gmnId.value.slice(-1)}`;
  }
  return url;
}

// `kgnKbn`（I-307）は URL に載せない（保持領域へ・05 §2.5 ステップ4）。

/** L-204 ステップ5: 新規ウィンドウ。ブロック時は**同一ウィンドウ**（上流 §12 #11。エラーにしない）。 */
function openTransition(url: string): void {
  const opened = window.open(url, "_blank");
  if (opened === null) {
    window.location.assign(url);
  }
}

function readStartupKbn(): string | null {
  // L-207 ステップ6: 必須としない。空欄は `3` とみなす。値域 `1`/`2`/`3` 以外は不正（裁定 Q-236）。
  const value = stfKbn.value === "" ? "3" : stfKbn.value;
  return ["1", "2", "3"].includes(value) ? value : null;
}

function readKgnKbn(): "Y" | "N" | null {
  // L-207 ステップ7: 必須としない。空欄は `Y` とみなす。`Y`/`N` 以外は不正（裁定 Q-236）。
  const value = kgnKbn.value === "" ? "Y" : kgnKbn.value;
  if (value === "Y") {
    return "Y";
  }
  if (value === "N") {
    return "N";
  }
  return null;
}

async function performLogin(target: "transition" | "menu"): Promise<void> {
  message.value = "";

  // L-207 ステップ1: 送信中なら何もしない。
  if (!subCheckSubmit()) {
    return;
  }

  // L-207 ステップ2: 正規化（trim しない）。
  stfCdInput.value = normalizeStfCd(stfCdInput.value);

  // L-207 ステップ3〜4 / E-202: ログイン時は**半角数字 7 桁固定**。不正なら `/login` を呼ばない。
  if (!/^[0-9]{7}$/.test(stfCdInput.value)) {
    message.value = E202_MESSAGE;
    navigateToCommonScreen("sessionError");
    return;
  }

  const startupKbn = readStartupKbn();
  if (startupKbn === null) {
    // L-207 分岐 3: E-202 と同一文面。遷移しない（05 §2.8）。
    message.value = E202_MESSAGE;
    return;
  }

  const permissionKbn = readKgnKbn();
  if (permissionKbn === null) {
    message.value = E202_MESSAGE;
    return;
  }

  // L-207 ステップ5: L-206 で暗号化し I-313 を生成する。日付は `/init` の Date ヘッダで補正した JST。
  let encryptedStfCd: string;
  try {
    const clock = jstClock.value ?? createJstClock(null);
    encryptedStfCd = encryptStfCd(stfCdInput.value, clock.yyyymmdd());
  } catch (error) {
    if (error instanceof StfCdCipherError) {
      // L-207 分岐 4（ログイン時）: 暗号化の例外は E-205。
      message.value = E205_MESSAGE;
      navigateToCommonScreen("sessionError");
      return;
    }
    throw error;
  }

  // L-207 ステップ8〜9: API の直前に ON、`finally` で必ず OFF。
  subSetSubmitFlg();
  try {
    const result = await login({
      encryptedStfCd,
      stfKbn: startupKbn,
      gmnId: gmnId.value,
      kgnKbn: permissionKbn,
    });
    const body = result.body;

    // E-203（稼働不可・HTTP 403）→ オンライン利用エラー画面。文面はサーバが SQL-6 で取得したもの。
    if (result.status === 403) {
      message.value = body.errorMessage ?? "";
      navigateToCommonScreen("onlineUnavailable");
      return;
    }

    if (body.errorCode === "0") {
      // L-203 成功。L-208 ステップ2 の判定用にログイン成立を保持する。
      session.markLoggedIn();
      // 工程04 §6.4: ログイン成立時に**必ず上書き**する（前回の権限区分を持ち越さない）。
      saveKgnKbn(permissionKbn);

      if (target === "menu") {
        // L-204 ステップ6: 同一ウィンドウ。引継ぎは `stfKbn` のクエリのみ。
        if (MENU_TARGET_ROUTE === "") {
          return;
        }
        window.location.assign(`${MENU_TARGET_ROUTE}?stfKbn=${startupKbn}`);
        return;
      }
      openTransition(buildTransitionUrl(startupKbn));
      return;
    }

    if (body.errorCode === "1") {
      // E-201／E-207 は `errorCode` のみ（文言なし）→ クライアント固定文言。E-205 はサーバ文言。
      message.value = body.errorMessage ?? E201_MESSAGE;
      navigateToCommonScreen("sessionError");
      return;
    }

    // E-208（システムエラー）。
    message.value = body.errorMessage ?? "";
    navigateToCommonScreen("systemError");
  } finally {
    subInitSubmitFlg();
  }
}

async function handleGenerateUrl(): Promise<void> {
  message.value = "";

  if (!subCheckSubmit()) {
    return;
  }

  stfCdInput.value = normalizeStfCd(stfCdInput.value);

  const startupKbn = readStartupKbn();
  if (startupKbn === null) {
    message.value = E202_MESSAGE;
    return;
  }

  const permissionKbn = readKgnKbn();
  if (permissionKbn === null) {
    message.value = E202_MESSAGE;
    return;
  }

  subSetSubmitFlg();
  try {
    // I-303 は**平文**で送る。空文字はサーバが `"NaN"` を扱う（裁定 Q-231）。
    // URL の組立と 150 桁判定はサーバが行う。クライアントは応答を表示するだけ（裁定 Q-233）。
    const result = await generateUrl({
      stfCd: stfCdInput.value,
      stfKbn: startupKbn,
      gmnId: gmnId.value,
      kgnKbn: permissionKbn,
    });
    const body = result.body;

    if (result.status === 403) {
      message.value = body.errorMessage ?? "";
      navigateToCommonScreen("onlineUnavailable");
      return;
    }

    if (body.errorCode === "0") {
      urlText.value = body.url ?? "";
      return;
    }

    if (body.errorCode === "1") {
      // E-202（サーバ検知）・E-210: エラー通知。**遷移しない**。150 桁超を切捨てない（B-21）。
      message.value = body.errorMessage ?? "";
      return;
    }

    // E-209（システムエラー）。
    message.value = body.errorMessage ?? "";
    navigateToCommonScreen("systemError");
  } finally {
    subInitSubmitFlg();
  }
}

function openCloseDialog(): void {
  // L-208 ステップ1: 確認文言。キャンセルなら何もしない（Q-218）。
  confirmVisible.value = true;
}

async function closeScreen(): Promise<void> {
  confirmVisible.value = false;

  // L-208 ステップ2〜5: ログイン成立前は破棄要求を行わない。成立後は**閉じる前に**破棄を要求する。
  if (session.loggedIn) {
    // 要求先は共通基盤の Session 管理機能（裁定 Q-232）。本画面専用の端点は追加しない。
    const purged = await requestSessionPurge();
    if (!purged) {
      // ステップ5: 失敗は運用ログ 1 件。サーバへ記録する端点が無いため、クライアント側の出力に留める
      // （差異登記に記載）。利用者へは追加の提示を出さない（ステップ4・裁定 Q-228）。
      console.warn("session purge failed", { screenId: "R60Login" });
    }
  }

  // 工程04 §6.4: 画面終了時に権限区分を明示的に削除する。
  clearKgnKbn();

  // ステップ4: 要求の成否にかかわらず画面を閉じる（失効でも回収される・裁定 Q-228）。
  window.close();
}

async function loadInit(): Promise<void> {
  try {
    const result = await init();
    // 05 §8.4: `/init` 応答の HTTP `Date` ヘッダとの差分で補正した JST を以後の暗号化に使う。
    jstClock.value = createJstClock(result.serverDate);

    const body: InitResponse = result.body;

    // E-206（稼働不可・HTTP 403）→ オンライン利用エラー画面。
    if (result.status === 403) {
      message.value = body.errorMessage ?? "";
      navigateToCommonScreen("onlineUnavailable");
      return;
    }

    // E-204（システムエラー）。
    if (body.errorCode === "2") {
      message.value = body.errorMessage ?? "";
      navigateToCommonScreen("systemError");
      return;
    }

    if (body.errorCode !== "0") {
      message.value = body.errorMessage ?? "";
      return;
    }

    pageOptions.value = body.pageList ?? [];
    kbnOptions.value = body.kbnList ?? [];

    // L-202 ステップ7: 1 件以上のとき I-306＝先頭候補・I-307＝`Y`・I-304＝`3`。
    gmnId.value = pageOptions.value.length > 0 ? (pageOptions.value[0]?.value ?? "") : "";
    kgnKbn.value = "Y";
    stfKbn.value = "3";

    // L-202 ステップ6 / B-22: 0 件はエラーではない。文言表示と I-308／I-311 の非活性。
    candidateMessage.value = pageOptions.value.length === 0 ? NO_CANDIDATE_MESSAGE : "";

    // 05 §2.3 ステップ8〜9（同一クライアントで連続 3 回の E-204 を運用ログ 1 件）は**サーバが数える**
    // （Cookie `r60login.cid` による計数。`init_api.py`。差異登記 #6）。
  } catch (error) {
    // 通信失敗時の扱いは設計に規定が無い（E-204 は応答を受けた場合の区分）。運用側の出力のみ残す。
    console.error("init request failed", error);
  }
}

onMounted(() => {
  tick();
  timerId = window.setInterval(tick, 1000);
  void loadInit();
});

onBeforeUnmount(() => {
  if (timerId !== undefined) {
    window.clearInterval(timerId);
  }
});
</script>

<template>
  <!-- I-301 の背景色は設計が「本節点の決定（C）」とするのみで値が無いため #FFFFFF とした（差異登記に記載）。 -->
  <div class="login-screen">
    <h1 class="login-screen__title">{{ PAGE_TITLE }}</h1>

    <!-- I-302 システム日時（1 秒ごとにクライアント端末時刻へ更新） -->
    <div class="login-screen__datetime">{{ systemDateTime }}</div>

    <!-- I-305 説明文（固定値。値の定義は節点2 承認版 §4 #5） -->
    <p class="login-screen__description">{{ FIXED_DESCRIPTION }}</p>

    <div class="login-screen__field">
      <label for="stfCd">ユーザーＩＤ</label>
      <!-- I-303: 半角数字 7 桁固定。入力時に正規化する（trim しない・全角除去）。 -->
      <!-- 桁数を入力段で切らない: 6 桁・8 桁・前後空白付きは E-202 として判定させる（B-01・B-03・B-07）。 -->
      <InputText id="stfCd" v-model="stfCdInput" @input="onStfCdInput" />
    </div>

    <div class="login-screen__field">
      <label for="stfKbn">起動区分</label>
      <!-- I-304: 必須としない。空欄は 3 とみなす。遷移用の値でありログイン可否に用いない。 -->
      <InputText id="stfKbn" v-model="stfKbn" />
    </div>

    <div class="login-screen__field">
      <label for="gmnId">画面</label>
      <!-- I-306: 候補 0 件では選択不可。初期値は先頭候補。 -->
      <Select
        id="gmnId"
        v-model="gmnId"
        :options="pageOptions"
        option-label="label"
        option-value="value"
        :disabled="candidatesEmpty"
      />
    </div>

    <div class="login-screen__field">
      <label for="kgnKbn">権限区分</label>
      <!-- I-307: 画面値 Y/N（内部値 1/0）。遷移時は URL に載せず保持領域へ。 -->
      <Select
        id="kgnKbn"
        v-model="kgnKbn"
        :options="kbnOptions"
        option-label="label"
        option-value="value"
      />
    </div>

    <div v-if="candidateMessage" class="login-screen__message">{{ candidateMessage }}</div>
    <div v-if="message" class="login-screen__message">{{ message }}</div>

    <div class="login-screen__buttons">
      <!-- I-308 ログイン（候補 0 件で非活性） -->
      <Button label="ログイン" :disabled="loginDisabled" @click="performLogin('transition')" />
      <!-- I-309 メニュー（/login を共用し、同一ウィンドウで遷移） -->
      <Button label="メニュー" @click="performLogin('menu')" />
      <!-- I-311 URL出力（候補 0 件で非活性） -->
      <Button label="URL出力" :disabled="urlOutputDisabled" @click="handleGenerateUrl" />
      <!-- I-312 閉じる -->
      <Button label="閉じる" @click="openCloseDialog" />
    </div>

    <div class="login-screen__field">
      <label for="urlText">URL</label>
      <!-- I-310: 受付 150 桁／表示 120 桁。編集値は表示のみで、遷移には使用しない（Q-213）。 -->
      <InputText id="urlText" v-model="urlText" class="login-screen__url" />
    </div>

    <Dialog v-model:visible="confirmVisible" header="確認" :modal="true">
      <p>画面を終了してよろしいですか？</p>
      <div class="login-screen__buttons">
        <Button label="はい" @click="closeScreen" />
        <Button label="キャンセル" @click="confirmVisible = false" />
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
/* I-301 の背景色（値は設計に無い。C 裁定として #FFFFFF）。 */
.login-screen {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 640px;
  padding: 1.5rem;
  /* I-301 の背景色は設計が「本節点の決定（C）」とするのみで値が無いため #FFFFFF とした（差異登記に記載）。 */
  background-color: #ffffff;
}

.login-screen__title {
  margin: 0;
  font-size: 1.5rem;
}

.login-screen__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.login-screen__buttons {
  display: flex;
  gap: 0.5rem;
}

/* I-310: 表示幅 120 桁。超える分は表示上スクロールする（05 §2.6 ステップ8）。 */
.login-screen__url {
  width: 120ch;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.login-screen__message {
  color: #b00020;
}
</style>
