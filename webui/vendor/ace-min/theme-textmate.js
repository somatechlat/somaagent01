define("i18n.t('ui_ace_theme_textmate')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_theme_textmate_css')","i18n.t('ui_ace_lib_dom')"],function(e,t,n){"i18n.t('ui_use_strict')";t.isDark=!1,t.cssClass="i18n.t('ui_ace_tm')",t.cssText=e("i18n.t('ui_textmate_css')"),t.$id="i18n.t('ui_ace_theme_textmate')";var r=e("i18n.t('ui_lib_dom')");r.importCssString(t.cssText,t.cssClass,!1)});                (function() {
                    window.require(["i18n.t('ui_ace_theme_textmate')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            