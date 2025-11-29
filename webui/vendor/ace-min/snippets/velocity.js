define("i18n.t('ui_ace_snippets_velocity_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports='# macro\nsnippet #macro\n	#macro ( ${1:macroName} ${2:\\$var1, [\\$var2, ...]} )\n		${3:## macro code}\n	#end\n# foreach\nsnippet #foreach\n	#foreach ( ${1:\\$item} in ${2:\\$collection} )\n		${3:## foreach code}\n	#end\n# if\nsnippet #if\n	#if ( ${1:true} )\n		${0}\n	#end\n# if ... else\nsnippet #ife\n	#if ( ${1:true} )\n		${2}\n	#else\n		${0}\n	#end\n#import\nsnippet #import\n	#import ( "i18n.t('ui_1_path_to_velocity_format')" )\n# set\nsnippet #set\n	#set ( $${1:var} = ${0} )\n'}),define("i18n.t('ui_ace_snippets_velocity')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_velocity_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_velocity_snippets')"),t.scope="i18n.t('ui_velocity')",t.includeScopes=["i18n.t('ui_html')","i18n.t('ui_javascript')","i18n.t('ui_css')"]});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_velocity')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            