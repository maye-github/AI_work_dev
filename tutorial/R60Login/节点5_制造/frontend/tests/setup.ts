/**
 * テスト環境の下ごしらえ。
 *
 * jsdom は `window.matchMedia` を持たないが、PrimeVue の `Select` が `mounted` で参照する。
 * **製品コードではなく環境の不足を埋める**ための差し替えであり、画面の判定には影響しない。
 */

if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }),
  });
}
