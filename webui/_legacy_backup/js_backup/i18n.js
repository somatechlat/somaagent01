// Lightweight i18n runtime used across the Web UI.
// Exposes a global ``i18n`` object and an Alpine store (when Alpine is present)
// so components can reactively re-render when the locale changes.
export const i18n = {
  lang: "en",
  dict: {},
  async load(lang) {
    this.lang = lang;
    try {
      const resp = await fetch(`/static/i18n/${lang}.json`);
      if (resp.ok) {
        this.dict = await resp.json();
      } else {
        console.warn(`i18n: failed to load ${lang} translations (HTTP ${resp.status})`);
        this.dict = {};
      }
    } catch (e) {
      console.error('i18n load error', e);
      this.dict = {};
    }
    try {
      localStorage.setItem('locale', lang);
      document.documentElement.setAttribute('lang', lang);
    } catch (_) { /* ignore storage errors */ }
    this._notify();
  },
  t(key) {
    return this.dict[key] ?? key;
  },
  applyTranslations(root = document) {
    if (!root) return;
    // text replacements
    root.querySelectorAll('[data-i18n-key]').forEach(el => {
      const key = el.getAttribute('data-i18n-key');
      if (!key) return;
      const val = this.t(key);
      // Preserve child structure only if element is leaf; skip if it has element children
      if (el.children.length === 0) {
        el.textContent = val;
      }
    });
    // placeholder
    root.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (!key) return;
      el.setAttribute('placeholder', this.t(key));
    });
    // aria-label
    root.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
      const key = el.getAttribute('data-i18n-aria-label');
      if (!key) return;
      el.setAttribute('aria-label', this.t(key));
    });
    // title
    root.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      if (!key) return;
      el.setAttribute('title', this.t(key));
    });
  },
  _notify() {
    if (globalThis.Alpine?.store) {
      const store = globalThis.Alpine.store('i18n');
      if (store) store.locale = this.lang;
    }
    this.applyTranslations();
  }
};

export async function initI18n(defaultLang = null) {
  const saved = (() => {
    try { return localStorage.getItem('locale'); } catch (_) { return null; }
  })();
  const lang = defaultLang || saved || (navigator?.language?.split('-')[0] ?? 'en');
  // Create Alpine store lazily when Alpine boots.
  document.addEventListener('alpine:init', () => {
    if (!globalThis.Alpine) return;
    globalThis.Alpine.store('i18n', {
      locale: i18n.lang,
      t: (k) => i18n.t(k),
      setLocale: async (langCode) => {
        await i18n.load(langCode);
      }
    });
  });
  await i18n.load(lang);
  globalThis.i18n = i18n;
  globalThis.setLocale = async (langCode) => i18n.load(langCode);
}

// Auto-init when this module is loaded directly via <script type="module" src="js/i18n.js">
if (typeof window !== 'undefined' && !globalThis.__i18nInitialized) {
  globalThis.__i18nInitialized = true;
  initI18n();
}
