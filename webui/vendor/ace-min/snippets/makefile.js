define("i18n.t('ui_ace_snippets_makefile_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports="snippet ifeq\n	ifeq (${1:cond0},${2:cond1})\n		${3:code}\n	endif\n"i18n.t('ui_define')"ace/snippets/makefile"i18n.t('ui_')"require","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_makefile_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_makefile_snippets')"),t.scope="i18n.t('ui_makefile')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_makefile')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            