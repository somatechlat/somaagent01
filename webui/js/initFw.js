import * as initializer from "i18n.t('ui_i18n_t_ui_i18n_t_ui_initializer_js')";
import * as _modali18n.t('ui_i18n_t_ui_initializer_js')i_i18n_t_ui_modals_js')";
import * as _i18n.t('ui_i18n_t_ui_modals_js')t('ui_i18n_t_ui_i18n_t_ui_components_js')";i18n.t('ui_i18n_t_ui_components_js')lements
await initializer.initialize();

// import alpine library
await import("i18n.t('ui_i18n_t_ui_i18n_t_ui_vendor_i18n.t('ui_i18n_t_ui_vendor_alpine_alpine_min_js')roy directive to alpine
Alpine.directive(
  "i18n.t('ui_i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_destroy'), { expression }, { evaluateLater, cleanup }) => {
    const onDestroy = evaluateLater(expression);
    cleanup(() => onDestroy());
  }
);

// add x-create directive to alpine
Alpine.directive("i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_create')')", (_el, { expression }, { evaluateLater }) => {
  const onCreate = evaluateLater(expression);
  onCreate();
});
