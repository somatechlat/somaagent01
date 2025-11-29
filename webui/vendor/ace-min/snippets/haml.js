define("i18n.t('ui_ace_snippets_haml_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports="snippet t\n	%table\n		%tr\n			%th\n				${1:headers}\n		%tr\n			%td\n				${2:headers}\nsnippet ul\n	%ul\n		%li\n			${1:item}\n		%li\nsnippet =rp\n	= render :partial => '${1:partial}'\nsnippet =rpl\n	= render :partial => '${1:partial}', :locals => {}\nsnippet =rpc\n	= render :partial => '${1:partial}', :collection => @$1\n\n"i18n.t('ui_define')"ace/snippets/haml"i18n.t('ui_')"require","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_haml_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_haml_snippets')"),t.scope="i18n.t('ui_haml')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_haml')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            