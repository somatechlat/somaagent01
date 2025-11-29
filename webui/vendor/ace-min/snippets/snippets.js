define("i18n.t('ui_ace_snippets_snippets_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports="# snippets for making snippets :)\nsnippet snip\n	snippet ${1:trigger}\n		${2}\nsnippet msnip\n	snippet ${1:trigger} ${2:description}\n		${3}\nsnippet v\n	{VISUAL}\n"i18n.t('ui_define')"ace/snippets/snippets"i18n.t('ui_')"require","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_snippets_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_snippets_snippets')"),t.scope="i18n.t('ui_snippets')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_snippets')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            