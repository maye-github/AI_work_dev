/**
 * 検索画面の状態保持（Pinia。工程04 §1.1）。
 *
 * - 検索条件・頁番号・仕掛表示・活性状態を保持する。
 * - L-215 ページャは「画面が保持する検索条件で /search へ委譲する」ため、条件の出所は本ストア。
 * - L-216 条件部切替はサーバ通信しない。状態は画面内（本ストア）で保持する。
 * - L-221 表示制御は権限・検索結果・行選択・モードで活性を決める。
 */
import { defineStore } from 'pinia';

import type { SearchParams } from '../services/makerApi';

export interface SearchCondition {
  makerCd: string;
  makerNm: string;
  includeDeleted: boolean;
  pageSize: number;
  shikakeMode: boolean;
  pageNo: number;
  sortField: string | null;
}

interface SearchState {
  condition: SearchCondition;
  lastSearchSuccess: boolean;
  totalCount: number;
  conditionExpanded: boolean;
  selectedMakerCd: string | null;
}

export const useSearchState = defineStore('searchState', {
  state: (): SearchState => ({
    condition: {
      makerCd: '',
      makerNm: '',
      includeDeleted: false,
      pageSize: 20,
      shikakeMode: false,
      pageNo: 1,
      sortField: null,
    },
    lastSearchSuccess: false,
    totalCount: 0,
    conditionExpanded: true,
    selectedMakerCd: null,
  }),

  getters: {
    // I-337／I-338: 総件数 0 件でページャ非活性
    pagerDisabled: (state): boolean => state.totalCount === 0,
    // I-351／I-353／I-354: 検索成功後に活性（0 件も検索成功）
    canOperateAfterSearch: (state): boolean => state.lastSearchSuccess,
    // I-350: 検索成功後かつ行選択時のみ活性
    canDuplicate: (state): boolean =>
      state.lastSearchSuccess && state.selectedMakerCd !== null,
    // I-331: メーカー日本語名が空白でないとき活性
    canClearName: (state): boolean => state.condition.makerNm !== '',
  },

  actions: {
    toSearchParams(): SearchParams {
      return {
        makerCd: this.condition.makerCd,
        makerNm: this.condition.makerNm,
        includeDeleted: this.condition.includeDeleted,
        pageSize: this.condition.pageSize,
        shikakeMode: this.condition.shikakeMode,
        pageNo: this.condition.pageNo,
        sortField: this.condition.sortField,
      };
    },
    resetPageToFirst(): void {
      this.condition.pageNo = 1;
    },
    markSearched(totalCount: number): void {
      this.lastSearchSuccess = true;
      this.totalCount = totalCount;
    },
    toggleCondition(): void {
      // L-216: サーバ通信なし
      this.conditionExpanded = !this.conditionExpanded;
    },
    toggleShikake(): void {
      this.condition.shikakeMode = !this.condition.shikakeMode;
    },
    selectRow(makerCd: string | null): void {
      this.selectedMakerCd = makerCd;
    },
  },
});
