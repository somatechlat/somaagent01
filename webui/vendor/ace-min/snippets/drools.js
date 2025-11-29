define("i18n.t('ui_ace_snippets_drools_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports='\nsnippet rule\n	rule "i18n.t('ui_1_rule_name')"\n	when\n		${2:// when...} \n	then\n		${3:// then...}\n	end\n\nsnippet query\n	query ${1?:query_name}\n		${2:// find} \n	end\n	\nsnippet declare\n	declare ${1?:type_name}\n		${2:// attributes} \n	end\n\n'}),define("i18n.t('ui_ace_snippets_drools')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_drools_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_drools_snippets')"),t.scope="i18n.t('ui_drools')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_drools')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            