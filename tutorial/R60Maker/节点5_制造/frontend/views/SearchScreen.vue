<script setup lang="ts">
/**
 * 検索画面 SCR-201（I-322〜I-354）。
 *
 * - 初期表示は /init（L-213）。検索は /search（L-214）。ページャは同条件で /search へ委譲（L-215）。
 * - 条件部切替（L-216）はサーバ通信なし。活性制御は L-221。遷移は要求のみを emit する（L-222）。
 * - 画面側入力チェック違反は E-219（該当項目を強調し、API を呼ばない）。
 * - スタックは工程04 §1.1（Vue 3 `<script setup>` + TypeScript + PrimeVue）。
 */
import { computed, onMounted, ref } from 'vue';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import InputText from 'primevue/inputtext';

import {
  errorScreenKindFor,
  replaceWithErrorScreen,
  showHeader,
  showPager,
} from '../common/customerParts';
import * as api from '../services/makerApi';
import { useSearchState } from '../stores/searchState';

const TITLE = 'メーカーマスタメンテ';
const SORT_FIELDS = new Set(['MAKER_CD', 'MAKER_NM']);

const emit = defineEmits<{
  (e: 'navigate', payload: { mode: '1' | '2' | '3'; makerCd?: string }): void;
  (e: 'back'): void;
  (e: 'end'): void;
}>();

const store = useSearchState();

const items = ref<api.MakerItem[]>([]);
const pager = ref<api.Pager | null>(null);
const messageInfo = ref<api.MessageInfo[]>([]);
const pageSizeOptions = ref<number[]>([10, 20, 50, 100]);
const serverTime = ref<string>('');
const messageId = ref<string>('');
const fieldErrors = ref<Record<string, boolean>>({});

const makerCd = computed({
  get: () => store.condition.makerCd,
  set: (value: string) => {
    store.condition.makerCd = value;
  },
});
const makerNm = computed({
  get: () => store.condition.makerNm,
  set: (value: string) => {
    store.condition.makerNm = value;
  },
});
const shikakeLabel = computed(() =>
  store.condition.shikakeMode ? '仕掛表示: 仕掛' : '仕掛表示: 通常',
);
const currentMessage = computed(() => messageText(messageId.value));

onMounted(async () => {
  const response = await api.init({});
  if (response.errorCode === 9) {
    replaceWithErrorScreen(errorScreenKindFor(response.errorId));
    return;
  }
  serverTime.value = response.serverTime ?? '';
  messageInfo.value = response.messageInfo;
  pageSizeOptions.value = response.pageSizeOptions;
  store.condition.pageSize = response.pageSize;
  store.condition.includeDeleted = response.includeDeleted;
  store.conditionExpanded = response.conditionExpanded;
  // I-322〜I-326 は CommonHeader（共通部品）が描画する
  showHeader({
    title: TITLE,
    systemTime: serverTime.value,
    companyNm: response.companyNm ?? undefined,
    deptNm: response.deptNm ?? undefined,
    userName: response.userName ?? undefined,
  });
});

function messageText(id: string): string {
  if (!id) {
    return '';
  }
  return messageInfo.value.find((m) => m.msgId === id)?.msgTxt ?? '';
}

// L-214 手順①: 画面側入力チェック（サーバへ送らない）
function clientValidate(): boolean {
  const errors: Record<string, boolean> = {};
  const code = store.condition.makerCd;
  if (code !== '' && !/^[0-9A-Za-z]{1,5}$/.test(code)) {
    errors.makerCd = true;
  }
  const name = store.condition.makerNm;
  if (
    name !== '' &&
    (new TextEncoder().encode(name).length > 30 || /[,"'|]/.test(name))
  ) {
    errors.makerNm = true;
  }
  fieldErrors.value = errors;
  return Object.keys(errors).length === 0;
}

async function execSearch(): Promise<void> {
  const response = await api.search(store.toSearchParams());
  if (response.errorCode === 9) {
    replaceWithErrorScreen(errorScreenKindFor(response.errorId));
    return;
  }
  if (response.errorCode === 1) {
    messageId.value = response.msgId ?? '';
    if (response.errorId === '1001') {
      // E-213: 0 件。検索成功として扱い、操作ボタンを活性に保つ
      items.value = [];
      pager.value = response.pager;
      store.markSearched(0);
      syncPager();
      return;
    }
    // E-214 等: 失敗時に一覧・総件数を更新しない
    return;
  }
  items.value = response.items;
  pager.value = response.pager;
  store.markSearched(response.totalCount);
  syncPager();
}

// I-335 表示: 頁番号を先頭へ戻して検索
async function runSearch(): Promise<void> {
  if (!clientValidate()) {
    return;
  }
  store.resetPageToFirst();
  await execSearch();
}

// L-215: 画面が保持する検索条件で /search へ委譲
async function gotoPage(pageNo: number): Promise<void> {
  store.condition.pageNo = pageNo;
  await execSearch();
}

function sortBy(field: 'MAKER_CD' | 'MAKER_NM'): void {
  if (!SORT_FIELDS.has(field)) {
    return;
  }
  store.condition.sortField = field;
  void runSearch();
}

function syncPager(): void {
  showPager({
    pageNo: pager.value?.pageNo ?? 1,
    totalPages: pager.value?.totalPages ?? 0,
    pageSize: pager.value?.pageSize ?? store.condition.pageSize,
    disabled: store.pagerDisabled,
  });
}

// I-331 クリア: 自動再検索しない
function clearName(): void {
  store.condition.makerNm = '';
}

function onPageSizeChange(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value);
  store.condition.pageSize = value;
  // L-215: 1 頁件数の変更では自動再検索しない
}

function selectRow(makerCdValue: string): void {
  store.selectRow(makerCdValue);
}

function openEdit(makerCdValue: string): void {
  store.selectRow(makerCdValue);
  emit('navigate', { mode: '3', makerCd: makerCdValue });
}

function openDuplicate(): void {
  if (store.selectedMakerCd !== null) {
    emit('navigate', { mode: '2', makerCd: store.selectedMakerCd });
  }
}

function openNew(): void {
  emit('navigate', { mode: '1' });
}

function goBack(): void {
  emit('back');
}

function endBusiness(): void {
  // L-222 手順④: 確認（MSG-C-004）のうえ業務終了
  messageId.value = 'MSG-C-004';
  if (window.confirm(messageText('MSG-C-004'))) {
    emit('end');
  }
}

async function doDownload(): Promise<void> {
  const result = await api.download(store.toSearchParams());
  if (result.kind === 'error') {
    if (result.error.errorCode === 9) {
      replaceWithErrorScreen(errorScreenKindFor(result.error.errorId));
      return;
    }
    messageId.value = result.error.msgId ?? '';
    return;
  }
  saveBlob(result.blob, result.filename);
}

function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="search-screen">
    <div id="common-header"></div>
    <h1 class="screen-title">{{ TITLE }}</h1>
    <div class="system-time">{{ serverTime }}</div>

    <div class="message-area" role="status">{{ currentMessage }}</div>

    <section v-show="store.conditionExpanded" class="condition">
      <label>
        メーカーコード
        <InputText v-model="makerCd" :class="{ 'p-invalid': fieldErrors.makerCd }" maxlength="5" />
      </label>
      <label>
        メーカー日本語名
        <InputText v-model="makerNm" :class="{ 'p-invalid': fieldErrors.makerNm }" />
      </label>
      <Button label="クリア" :disabled="!store.canClearName" @click="clearName" />

      <label>
        <Checkbox v-model="store.condition.includeDeleted" :binary="true" />
        削除含む
      </label>

      <label>
        1頁件数
        <select :value="store.condition.pageSize" @change="onPageSizeChange">
          <option v-for="opt in pageSizeOptions" :key="opt" :value="opt">{{ opt }}</option>
        </select>
      </label>

      <Button :label="shikakeLabel" @click="store.toggleShikake()" />
      <Button label="表示" @click="runSearch" />
      <Button label="検索条件(非)表示" @click="store.toggleCondition()" />
    </section>

    <section class="result">
      <!-- I-337 ページャ（上部） -->
      <div class="pager pager-top">
        <button class="link" :disabled="store.pagerDisabled" @click="gotoPage(1)">先頭</button>
        <span>{{ pager?.pageNo ?? 1 }} / {{ pager?.totalPages ?? 0 }}</span>
        <button
          class="link"
          :disabled="!pager || pager.pageNo >= pager.totalPages"
          @click="gotoPage((pager?.pageNo ?? 1) + 1)"
        >
          次
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>
              <!-- I-340 ソート可 -->
              <button class="link" @click="sortBy('MAKER_CD')">メーカーコード</button>
            </th>
            <th>
              <!-- I-342 ソート可 -->
              <button class="link" @click="sortBy('MAKER_NM')">メーカー日本語名</button>
            </th>
            <th>メーカーカナ名</th>
            <th>送信状態</th>
            <th>削除</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in items"
            :key="row.makerCd"
            :class="{ selected: row.makerCd === store.selectedMakerCd }"
            @click="selectRow(row.makerCd)"
          >
            <!-- I-341 -->
            <td>
              <button class="link" @click.stop="openEdit(row.makerCd)">{{ row.makerCd }}</button>
            </td>
            <!-- I-343 -->
            <td>
              <button class="link" @click.stop="openEdit(row.makerCd)">{{ row.makerNm }}</button>
            </td>
            <!-- I-345 -->
            <td>{{ row.makerKanaNm }}</td>
            <!-- I-347 -->
            <td>{{ row.sendSts }}</td>
            <!-- I-349 -->
            <td>{{ row.delFlg }}</td>
          </tr>
        </tbody>
      </table>

      <div class="total">総件数: {{ store.totalCount }}</div>

      <!-- I-338 ページャ（下部） -->
      <div class="pager pager-bottom">
        <button class="link" :disabled="store.pagerDisabled" @click="gotoPage(1)">先頭</button>
        <span>{{ pager?.pageNo ?? 1 }} / {{ pager?.totalPages ?? 0 }}</span>
        <button
          class="link"
          :disabled="!pager || pager.pageNo >= pager.totalPages"
          @click="gotoPage((pager?.pageNo ?? 1) + 1)"
        >
          次
        </button>
      </div>
    </section>

    <footer class="actions">
      <!-- I-350 複製 -->
      <Button label="複製" :disabled="!store.canDuplicate" @click="openDuplicate" />
      <!-- I-351 戻る -->
      <Button label="戻る" :disabled="!store.canOperateAfterSearch" @click="goBack" />
      <!-- I-352 業務終了（常時活性） -->
      <Button label="業務終了" @click="endBusiness" />
      <!-- I-353 ダウンロード -->
      <Button label="ダウンロード" :disabled="!store.canOperateAfterSearch" @click="doDownload" />
      <!-- I-354 新規 -->
      <Button label="新規" :disabled="!store.canOperateAfterSearch" @click="openNew" />
    </footer>
  </div>
</template>
