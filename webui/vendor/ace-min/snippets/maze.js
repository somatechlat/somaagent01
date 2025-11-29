define("i18n.t('ui_ace_snippets_maze_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports="snippet >\ndescription assignment\nscope maze\n	-> ${1}= ${2}\n\nsnippet >\ndescription if\nscope maze\n	-> IF ${2:**} THEN %${3:L} ELSE %${4:R}\n"i18n.t('ui_define')"ace/snippets/maze"i18n.t('ui_')"require","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_maze_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_maze_snippets')"),t.scope="i18n.t('ui_maze')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_maze')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            