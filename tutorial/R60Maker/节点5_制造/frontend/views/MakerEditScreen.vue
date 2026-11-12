<script setup lang="ts">
/**
 * マスタ画面 SCR-202（9 項目・I-ID 未付与。設計 §3.2）。
 *
 * 項目: 操作モード／メーカーコード／メーカー日本語名／メーカーカナ名／緊急配信／削除／
 *       戻る／削除ボタン／登録ボタン。
 *
 * - 初期値は /initEdit（L-217）。登録・更新は /edit（L-220）、削除は /delete（L-219）。
 * - 活性制御は L-221。遷移は要求のみを emit する（L-222）。
 * - 画面側入力チェック違反は E-219（該当項目を強調し、API を呼ばない）。
 */
import { computed, onMounted, ref } from 'vue';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import InputText from 'primevue/inputtext';

import { errorScreenKindFor, replaceWithErrorScreen } from '../common/customerParts';
import * as api from '../services/makerApi';

/** 二度押し防止（BUG-004）。要求 §5-2 の送信中ロック。設計 L-220／L-219 の前提。 */
const submitting = ref(false);

const props = defineProps<{
  mode: '1' | '2' | '3';
  makerCd?: string;
  messages?: api.MessageInfo[];
}>();

const emit = defineEmits<{
  (e: 'saved', payload: api.EditResponse): void;
  (e: 'deleted', payload: api.DeleteResponse): void;
  (e: 'back'): void;
}>();

const CODE_RE = /^[0-9A-Za-z]{1,5}$/;
const KANA_RE = /^[｡-ﾟ]+$/;
const NAME_FORBIDDEN = /[,"'|]/;

const makerCd = ref<string>(props.makerCd ?? '');
const makerNm = ref<string>('');
const makerKanaNm = ref<string>('');
const emergencyDispatch = ref<boolean>(false);
const deleteFlg = ref<boolean>(false);
const lastUpdateDatetime = ref<string | null>(null);
const revNo = ref<number | null>(null);
const messageId = ref<string>('');
const fieldErrors = ref<Record<string, boolean>>({});

const modeLabel = computed(() =>
  props.mode === '1' ? '新規' : props.mode === '2' ? '複製' : '修正',
);
const makerCdDisabled = computed(() => props.mode === '3');
const isDeleted = computed(() => deleteFlg.value === true);
const deleteButtonEnabled = computed(() => props.mode === '3' && !isDeleted.value);
const currentMessage = computed(() => messageText(messageId.value));

onMounted(async () => {
  const response = await api.initEdit({ mode: props.mode, makerCd: props.makerCd ?? null });
  if (response.errorCode === 9) {
    replaceWithErrorScreen(errorScreenKindFor(response.errorId));
    return;
  }
  if (response.errorCode === 1) {
    messageId.value = response.msgId ?? '';
    return;
  }
  makerCd.value = response.makerCd ?? (props.makerCd ?? '');
  makerNm.value = response.makerNm ?? '';
  makerKanaNm.value = response.makerKanaNm ?? '';
  emergencyDispatch.value = response.emergencyDispatch;
  deleteFlg.value = response.deleteFlg === '1';
  lastUpdateDatetime.value = response.lastUpdateDatetime ?? null;
  revNo.value = response.revNo ?? null;
});

function messageText(id: string): string {
  if (!id) {
    return '';
  }
  return props.messages?.find((m) => m.msgId === id)?.msgTxt ?? '';
}

function namesRequired(): boolean {
  if (props.mode === '1' || props.mode === '2') {
    return emergencyDispatch.value;
  }
  return emergencyDispatch.value || deleteFlg.value;
}

function validate(): boolean {
  const errors: Record<string, boolean> = {};
  if (props.mode !== '3' && !CODE_RE.test(makerCd.value)) {
    errors.makerCd = true;
  }
  if (namesRequired()) {
    if (makerNm.value === '') {
      errors.makerNm = true;
    }
    if (makerKanaNm.value === '') {
      errors.kanaNm = true;
    }
  }
  if (
    makerNm.value !== '' &&
    (new TextEncoder().encode(makerNm.value).length > 30 ||
      NAME_FORBIDDEN.test(makerNm.value))
  ) {
    errors.makerNm = true;
  }
  if (
    makerKanaNm.value !== '' &&
    (makerKanaNm.value.length > 15 || !KANA_RE.test(makerKanaNm.value))
  ) {
    errors.kanaNm = true;
  }
  fieldErrors.value = errors;
  return Object.keys(errors).length === 0;
}

async function onRegister(): Promise<void> {
  if (submitting.value) {
    return;
  }
  if (!validate()) {
    return;
  }
  submitting.value = true;
  try {
    const params: api.EditParams = {
      mode: props.mode,
      makerCd: makerCd.value,
      makerNm: makerNm.value,
      makerKanaNm: makerKanaNm.value,
      emergencyDispatch: emergencyDispatch.value,
      deleteFlg: deleteFlg.value,
      lastUpdateDatetime: props.mode === '3' ? lastUpdateDatetime.value : null,
      revNo: props.mode === '3' ? revNo.value : null,
    };
    const response = await api.edit(params);
    if (response.errorCode === 9) {
      replaceWithErrorScreen(errorScreenKindFor(response.errorId));
      return;
    }
    if (response.errorCode === 1) {
      messageId.value = response.msgId ?? '';
      return;
    }
    if (response.msgId === 'MSG-I-003') {
      // 変更なし。登録せず、画面を閉じない（L-220）
      messageId.value = response.msgId;
      return;
    }
    emit('saved', response);
  } finally {
    submitting.value = false;
  }
}

async function onDelete(): Promise<void> {
  if (submitting.value) {
    return;
  }
  if (!validate()) {
    return;
  }
  // L-219 手順②: 削除確認（MSG-C-002）
  if (!window.confirm(messageText('MSG-C-002'))) {
    return;
  }
  submitting.value = true;
  try {
    const params: api.DeleteParams = {
      makerCd: makerCd.value,
      makerNm: makerNm.value,
      makerKanaNm: makerKanaNm.value,
      emergencyDispatch: emergencyDispatch.value,
      deleteFlg: true,
      lastUpdateDatetime: lastUpdateDatetime.value,
      revNo: revNo.value,
    };
    const response = await api.remove(params);
    if (response.errorCode === 9) {
      replaceWithErrorScreen(errorScreenKindFor(response.errorId));
      return;
    }
    if (response.errorCode === 1) {
      messageId.value = response.msgId ?? '';
      return;
    }
    emit('deleted', response);
  } finally {
    submitting.value = false;
  }
}

function onBack(): void {
  // L-222 手順②: 確認（MSG-C-003）のうえ検索画面へ戻る
  if (window.confirm(messageText('MSG-C-003'))) {
    emit('back');
  }
}
</script>

<template>
  <div class="maker-edit-screen">
    <h1 class="mode-label">{{ modeLabel }}</h1>
    <div class="message-area" role="status">{{ currentMessage }}</div>

    <section class="fields">
      <label>
        メーカーコード
        <InputText
          v-model="makerCd"
          :disabled="makerCdDisabled"
          :class="{ 'p-invalid': fieldErrors.makerCd }"
          maxlength="5"
        />
      </label>
      <label>
        メーカー日本語名
        <InputText v-model="makerNm" :class="{ 'p-invalid': fieldErrors.makerNm }" />
      </label>
      <label>
        メーカーカナ名
        <InputText v-model="makerKanaNm" :class="{ 'p-invalid': fieldErrors.kanaNm }" />
      </label>

      <label>
        <Checkbox v-model="emergencyDispatch" :binary="true" />
        緊急配信
      </label>

      <label>
        <!-- 削除済みは外せない（L-221 手順⑤） -->
        <Checkbox v-model="deleteFlg" :binary="true" :disabled="isDeleted" />
        削除
      </label>
    </section>

    <footer class="actions">
      <Button label="戻る" @click="onBack" />
      <Button label="削除" :disabled="!deleteButtonEnabled || submitting" @click="onDelete" />
      <!-- 登録ボタンは常時活性。押下時に検査する（L-221 手順⑤） -->
      <Button label="登録" :disabled="submitting" @click="onRegister" />
    </footer>
  </div>
</template>
