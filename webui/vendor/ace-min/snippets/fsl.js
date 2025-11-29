define("i18n.t('ui_ace_snippets_fsl_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports='snippet header\n	machine_name     : "";\n	machine_author   : "";\n	machine_license  : MIT;\n	machine_comment  : "";\n	machine_language : en;\n	machine_version  : 1.0.0;\n	fsl_version      : 1.0.0;\n	start_states     : [];\n'}),define("i18n.t('ui_ace_snippets_fsl')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_fsl_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_fsl_snippets')"),t.scope="i18n.t('ui_fsl')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_fsl')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            