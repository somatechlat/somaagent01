define("i18n.t('ui_ace_snippets_lua_snippets')",["i18n.t('ui_require')","i18n.t('ui_exports')","i18n.t('ui_module')"],function(e,t,n){n.exports="snippet #!\n	#!/usr/bin/env lua\n	$1\nsnippet local\n	local ${1:x} = ${2:1}\nsnippet fun\n	function ${1:fname}(${2:...})\n		${3:-- body}\n	end\nsnippet for\n	for ${1:i}=${2:1},${3:10} do\n		${4:print(i)}\n	end\nsnippet forp\n	for ${1:i},${2:v} in pairs(${3:table_name}) do\n	   ${4:-- body}\n	end\nsnippet fori\n	for ${1:i},${2:v} in ipairs(${3:table_name}) do\n	   ${4:-- body}\n	end\n"i18n.t('ui_define')"ace/snippets/lua"i18n.t('ui_')"require","i18n.t('ui_exports')","i18n.t('ui_module')","i18n.t('ui_ace_snippets_lua_snippets')"],function(e,t,n){"i18n.t('ui_use_strict')";t.snippetText=e("i18n.t('ui_lua_snippets')"),t.scope="i18n.t('ui_lua')"});                (function() {
                    window.require(["i18n.t('ui_ace_snippets_lua')"], function(m) {
                        if (typeof module == "i18n.t('ui_object')" && typeof exports == "i18n.t('ui_object')" && module) {
                            module.exports = m;
                        }
                    });
                })();
            