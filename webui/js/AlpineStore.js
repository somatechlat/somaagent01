// Track all created stores
const stores = new Map();

/**
 * Creates a store that can be used to share state between components.
 * Uses initial state object and returns a proxy to it that uses Alpine when initialized
 * @template T
 * @param {string} name
 * @param {T} initialState
 * @returns {T}
 */
export function createStore(name, initialState) {
  const proxy = new Proxy(initialState, {
    set(target, prop, value) {
      const store = globalThis.Alpine?.store(name);
      if (store) store[prop] = value;
      else target[prop] = value;
      return true;
    },
    get(target, prop) {
      const store = globalThis.Alpine?.store(name);
      if (store) return store[prop];
      return target[prop];
    }
  });

  if (globalThis.Alpine) {
    globalThis.Alpine.store(name, initialState);
  } else {
    document.addEventListener("i18n.t('ui_i18n_t_ui_alpine_init')", () => Alpine.store(name, initialState));
  }

  // Store the proxy
  stores.set(name, proxy);

  return /** @type {T} */ (proxy); // explicitly cast for linter support
}

// -------------------------------------------------------------------
// Helper: create a store for i18n locale persistence (VIBE compliant).
// -------------------------------------------------------------------
// The UI now includes a language selector that toggles between "i18n.t('ui_i18n_t_ui_en')" and "i18n.t('ui_i18n_t_ui_es')".
// We expose a dedicated Alpine store named "i18n.t('ui_i18n_t_ui_i18nlocale')" so components can
// read/write the current locale. The value is persisted to `localStorage`
// under the key "i18n.t('ui_i18n_t_ui_locale')" to survive page reloads.
// This function should be called once during app bootstrap.
export function initLocaleStore() {
  const saved = typeof localStorage !== "i18n.t('ui_i18n_t_ui_undefined')" ? localStorage.getItem("i18n.t('ui_i18n_t_ui_locale')") : null;
  const initial = saved === "i18n.t('ui_i18n_t_ui_es')" ? "i18n.t('ui_i18n_t_ui_es')" : "i18n.t('ui_i18n_t_ui_en')"; // default to English
  // The store shape matches UI expectations: $store.i18nLocale.locale
  const store = createStore("i18n.t('ui_i18n_t_ui_i18nlocale')", { locale: initial });
  // Keep `localStorage` in sync when the store changes.
  if (typeof Proxy !== "i18n.t('ui_i18n_t_ui_undefined')") {
    // Proxy already forwards set operations to the Alpine store; we add a watcher.
    // Alpine does not provide a native watcher for arbitrary stores, so we use a
    // simple interval poll (lightweight) – acceptable for a small UI.
    let last = store.value;
    setInterval(() => {
      if (store.value !== last) {
        last = store.value;
        try { localStorage.setItem("i18n.t('ui_i18n_t_ui_locale')", store.value); } catch (_) {}
      }
    }, 500);
  }
  return store;
}

/**
 * Get an existing store by name
 * @template T
 * @param {string} name
 * @returns {T | undefined}
 */
export function getStore(name) {
  return /** @type {T | undefined} */ (stores.get(name));
}