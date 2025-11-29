define("i18n.t('ui_ace_snippets_diff_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports='# DEP-3 (http://dep.debian.net/deps/dep3/) style patch header\nsnippet header DEP-3 style header\n	Description: ${1}\n	Origin: ${2:vendor|upstream|other}, ${3:url of the original patch}\n	Bug: ${4:url in upstream bugtracker}\n	Forwarded: ${5:no|not-needed|url}\n	Author: ${6:`g:snips_author`}\n	Reviewed-by: ${7:name and email}\n	Last-Update: ${8:`strftime("i18n.t('ui_y_m_d')")`}\n	Applied-Upstream: ${9:upstream version|url|commit}\n\n'}),define("i18n.t('ui_ace_snippets_diff')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_diff_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_diff_snippets')"),t.scope="i18n.t('ui_diff')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_diff')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            