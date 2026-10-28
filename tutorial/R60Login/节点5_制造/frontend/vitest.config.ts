import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vitest/config";

/**
 * フロント単体テストの実行設定（工程06）。
 *
 * * `environment: "jsdom"` — 画面（`.vue`）を実 DOM で組み立てるため。
 * * `test.env` — 画面とサービスが読む遷移先は**環境変数**で与える設計である（05 §1.2・§2.9）。
 *   値は**占位**（社外秘の実 URL を書かない。禁⑤）。未設定時の挙動（遷移しない）は
 *   テスト内で `vi.stubEnv` により明示的に作る。
 * * `coverage.reportsDirectory` — `docs/**` ではなく `reports/` 配下へ出す（規則 00 §12・§12.1）。
 */
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.ts"],
    setupFiles: ["tests/setup.ts"],
    env: {
      VITE_R60_MENU_URL: "/R60/menu",
      VITE_R60_SESSION_ERROR_URL: "/R60/session-error",
      VITE_R60_ONLINE_UNAVAILABLE_URL: "/R60/online-unavailable",
      VITE_R60_SYSTEM_ERROR_URL: "/R60/system-error",
      VITE_R60_MENU_HEADER_URL: "/R60/menu-header",
      VITE_R60_SESSION_PURGE_URL: "/api/session/purge",
    },
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "json-summary"],
      reportsDirectory: "../../../../reports/unit/R60Login/frontend-coverage",
      include: ["common/**/*.ts", "services/**/*.ts", "stores/**/*.ts", "views/**/*.vue"],
    },
  },
});
