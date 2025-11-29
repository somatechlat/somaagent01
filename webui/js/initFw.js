import * as initializer from "i18n.t('ui_i18n_t_ui_initializer_js')";
import * as _modals from "i18n.t('ui_i18n_t_ui_modals_js')";
import * as _components from "i18n.t('ui_i18n_t_ui_components_js')";

// initialize required elements
await initializer.initialize();

// import alpine library
await import("i18n.t('ui_i18n_t_ui_vendor_alpine_alpine_min_js')");

// add x-destroy directive to alpine
Alpine.directive(
  "i18n.t('ui_i18n_t_ui_destroy')",
  (el, { expression }, { evaluateLater, cleanup }) => {
    const onDestroy = evaluateLater(expression);
    cleanup(() => onDestroy());
  }
);

// add x-create directive to alpine
Alpine.directive("i18n.t('ui_i18n_t_ui_create')", (_el, { expression }, { evaluateLater }) => {
  const onCreate = evaluateLater(expression);
  onCreate();
});
