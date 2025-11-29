// Simple i18n utility for the Web UI
// Usage: await i18n.load('en'); then i18n.t('key') returns translation or key.
export const i18n = {
  lang: "en",
  dict: {},
  async load(lang) {
    this.lang = lang;
    try {
      // The UI is served with a static mount at "/static" (see index.html base href).
      // Translation files live under ``webui/i18n`` and are therefore reachable via
      // ``/static/i18n/<lang>.json``.
      const resp = await fetch(`/static/i18n/${lang}.json`);
      if (resp.ok) {
        this.dict = await resp.json();
      } else {
        console.warn(`i18n: failed to load ${lang} translations`);
        this.dict = {};
      }
    } catch (e) {
      console.error('i18n load error', e);
      this.dict = {};
    }
  },
  t(key) {
    return this.dict[key] ?? key;
  }
};
