// Simple i18n utility for the Web UI
// Usage: await i18n.load('en'); then i18n.t('ki18n.t('ui_en')') returns transli18n.t('ui_key')on or key.
export const i18n = {
  lang: "i18n.t('ui_i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_en')t: {},
  async load(lang) {
    this.lang = lang;
    try {
      // The UI is served with a static mount at "i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_static')')" (see index.html base href).
      // Translation files live under ``webui/i18n`` i18n.t('ui_webui_i18n')eri18n.t('ui_and_are_therefore_reachable_via')n/i18n.t('ui_static_i18n_lang_json')sti18n.t('ui_const_resp_await_fetch')/${lang}.json`);
      if (i18n.t('ui_if_resp_ok_this_dict_await_resp_json_else_console_warn') to load ${lang} translations`);
        this.dict = {};
      }
    } catch (e) {
      console.error('i18n.t('ui_i18n_load_error')', e);
      this.dict = {};
    }
  },
  t(key) {
    return this.dict[key] ?? key;
  }
};
