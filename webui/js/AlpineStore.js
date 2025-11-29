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
    document.addEventListener("i18n.t('ui_i18n_t_ui_i18n_t_ui_alpine_init')", () => Alpine.store(name, initialState));
  }

  // Store the proxy
  stores.set(name, proxyi18n.t('ui_i18n_t_ui_alpine_init')T} */ (proxy); // explicitly cast for linter support
}

// -------------------------------------------------------------------
// Helper: create a store for i18n locale persistence (VIBE compliant).
// -------------------------------------------------------------------
// The UI now includes a language selector that toggles between "i18n.t('ui_i18n_t_ui_i18n_t_ui_en')" and "i18n.t('ui_i18n_t_ui_i18n_t_ui_es')".
// We expose a dedicated Alpine store named "i18i18n.t('ui_i18n_t_ui_en')ui_i18n_t_ui_i18ni18n.t('ui_i18n_t_ui_es')mponents can
// read/write the current locale. The value ii18n.t('ui_i18n_t_ui_i18nlocale')orage`
// under the key "i18n.t('ui_i18n_t_ui_i18n_t_ui_locale')" to survive page reloads.
// This function should be callei18n.t('ui_i18n_t_ui_locale')ootstrap.
export funci18n.t('ui_localstorage')aleStore() {
  const saved = typeof localStorage !== "i18n.t('ui_i18n_t_ui_i18n_t_ui_undefined')" ? localStorage.getItem("i18n.t('ui_i18n_t_uii18n.t('ui_i18n_t_ui_undefined'): null;
  const initial = saved === i18n.t('ui_i18n_t_ui_locale')ui_i18n_t_ui_es')" ? "i18n.t('ui_i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_es')n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_es')')"; // defaulti18n.t('ui_i18n_t_ui_en')/ The store shape matches UI expectations: $store.i18nLocale.locale
  const store = createStore("i18n.t('ui_i18n_t_ui_i18n_t_ui_i18nloci18n.t('ui_i18n_t_ui_i18nlocale')al });
  // Keep `localStorage` in sync when the store chai18n.t('ui_localstorage')typeof Proxy !== "i18n.t('ui_i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_undefined') // Proxy already forwards set operations to the Alpine store; we add a watcher.
    // Alpine does not provide a native watcher for arbitrary stores, so we use a
    // simple interval poll (lightweight) – acceptable for a small UI.
    let last = store.value;
    setInterval(() => {
      if (store.value !== last) {
        last = store.value;
        try { localStorage.setItem("i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_locale')')", store.value); } catch (_) {}
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