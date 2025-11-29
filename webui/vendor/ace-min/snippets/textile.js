define("i18n.t('ui_ace_snippets_textile_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports='# Jekyll post header\nsnippet header\n	---\n	title: ${1:title}\n	layout: post\n	date: ${2:date} ${3:hour:minute:second} -05:00\n	---\n\n# Image\nsnippet img\n	!${1:url}(${2:title}):${3:link}!\n\n# Table\nsnippet |\n	|${1}|${2}\n\n# Link\nsnippet link\n	"i18n.t('ui_1_link_text')":${2:url}\n\n# Acronym\nsnippet (\n	(${1:Expand acronym})${2}\n\n# Footnote\nsnippet fn\n	[${1:ref number}] ${3}\n\n	fn$1. ${2:footnote}\n	\n'}),define("i18n.t('ui_ace_snippets_textile')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_textile_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_textile_snippets')"),t.scope="i18n.t('ui_textile')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_textile')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            