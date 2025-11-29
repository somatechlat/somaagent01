define("i18n.t('ui_ace_snippets_graphqlschema_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports="# Type Snippet\ntrigger type\nsnippet type\n	type ${1:type_name} {\n		${2:type_siblings}\n	}\n\n# Input Snippet\ntrigger input\nsnippet input\n	input ${1:input_name} {\n		${2:input_siblings}\n	}\n\n# Interface Snippet\ntrigger interface\nsnippet interface\n	interface ${1:interface_name} {\n		${2:interface_siblings}\n	}\n\n# Interface Snippet\ntrigger union\nsnippet union\n	union ${1:union_name} = ${2:type} | ${3: type}\n\n# Enum Snippet\ntrigger enum\nsnippet enum\n	enum ${1:enum_name} {\n		${2:enum_siblings}\n	}\n"i18n.t('ui_define')"ace/snippets/graphqlschema"i18n.t('ui_')"require","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_graphqlschema_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_graphqlschema_snippets')"),t.scope="i18n.t('ui_graphqlschema')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_graphqlschema')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            