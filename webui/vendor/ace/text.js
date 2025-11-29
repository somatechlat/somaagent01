
"i18n.t('ui_use_strict')";
/**
 * @typedef {import("i18n.t('ui_ace_internal')").Ace.SyntaxMode} SyntaxMode
 */

var config = require("i18n.t('ui_config')");

var Tokenizer = require("i18n.t('ui_tokenizer')").Tokenizer;

var TextHighlightRules = require("i18n.t('ui_text_highlight_rules')").TextHighlightRules;
var CstyleBehaviour = require("i18n.t('ui_behaviour_cstyle')").CstyleBehaviour;
var unicode = require("i18n.t('ui_unicode')");
var lang = require("i18n.t('ui_lib_lang')");
var TokenIterator = require("i18n.t('ui_token_iterator')").TokenIterator;
var Range = require("i18n.t('ui_range')").Range;

var Mode;
Mode = function() {
    this.HighlightRules = TextHighlightRules;
};

(function() {
    this.$defaultBehaviour = new CstyleBehaviour();

    this.tokenRe = new RegExp("i18n.t('ui_')" + unicode.wordChars + "\\$_]+"i18n.t('ui_')"g"i18n.t('ui_this_nontokenre_new_regexp')"^(?:[^"i18n.t('ui_unicode_wordchars')"\\$_]|\\s])+"i18n.t('ui_')"g"i18n.t('ui_this_syntaxmode_this_gettokenizer_function_if_this_tokenizer_this_highlightrules_this_highlightrules_new_this_highlightrules_this_highlightruleconfig_this_tokenizer_new_tokenizer_this_highlightrules_getrules_return_this_tokenizer_this_linecommentstart')""i18n.t('ui_this_blockcomment')""i18n.t('ui_this_syntaxmode_this_togglecommentlines_function_state_session_startrow_endrow_var_doc_session_doc_var_ignoreblanklines_true_var_shouldremove_true_var_minindent_infinity_var_tabsize_session_gettabsize_var_insertattabstop_false_if_this_linecommentstart_if_this_blockcomment_return_false_type_any_var_linecommentstart_this_blockcomment_start_var_linecommentend_this_blockcomment_end_type_any_var_regexpstart_new_regexp')"^(\\s*)(?:"i18n.t('ui_lang_escaperegexp_linecommentstart')")"i18n.t('ui_var_regexpend_new_regexp')"(?:"i18n.t('ui_lang_escaperegexp_linecommentend')")\\s*$");

            var comment = function(line, i) {
                if (testRemove(line, i))
                    return;
                if (!ignoreBlankLines || /\S/.test(line)) {
                    doc.insertInLine({row: i, column: line.length}, lineCommentEnd);
                    doc.insertInLine({row: i, column: minIndent}, lineCommentStart);
                }
            };

            var uncomment = function(line, i) {
                var m;
                if (m = line.match(regexpEnd))
                    doc.removeInLine(i, line.length - m[0].length, line.length);
                if (m = line.match(regexpStart))
                    doc.removeInLine(i, m[1].length, m[0].length);
            };

            /**@type {any}*/
            var testRemove = function(line, row) {
                if (regexpStart.test(line))
                    return true;
                var tokens = session.getTokens(row);
                for (var i = 0; i < tokens.length; i++) {
                    if (tokens[i].type === "i18n.t('ui_comment')")
                        return true;
                }
            };
        } else {
            if (Array.isArray(this.lineCommentStart)) {
                /**@type {any}*/
                var regexpStart = this.lineCommentStart.map(lang.escapeRegExp).join("|"i18n.t('ui_type_any_var_linecommentstart_this_linecommentstart_0_else_var_regexpstart_lang_escaperegexp_this_linecommentstart_type_any_var_linecommentstart_this_linecommentstart_regexpstart_new_regexp')"^(\\s*)(?:"i18n.t('ui_regexpstart')") ?"i18n.t('ui_insertattabstop_session_getusesofttabs_var_uncomment_function_line_i_var_m_line_match_regexpstart_if_m_return_var_start_m_1_length_end_m_0_length_if_shouldinsertspace_line_start_end_m_0_end_1')" "i18n.t('ui_end_doc_removeinline_i_start_end_var_commentwithspace_linecommentstart')" ";
            var comment = function(line, i) {
                if (!ignoreBlankLines || /\S/.test(line)) {
                    if (shouldInsertSpace(line, minIndent, minIndent))
                        doc.insertInLine({row: i, column: minIndent}, commentWithSpace);
                    else
                        doc.insertInLine({row: i, column: minIndent}, lineCommentStart);
                }
            };
            /**@type {any}*/
            var testRemove = function(line, i) {
                return regexpStart.test(line);
            };

            var shouldInsertSpace = function(line, before, after) {
                var spaces = 0;
                while (before-- && line.charAt(before) == " "i18n.t('ui_spaces_if_spaces_tabsize_0_return_false_var_spaces_0_while_line_charat_after')" ")
                    spaces++;
                if (tabSize > 2)
                    return spaces % tabSize != tabSize - 1;
                else
                    return spaces % tabSize == 0;
            };
        }

        function iter(fun) {
            fi18n.t('ui_2_return_spaces_tabsize_tabsize_1_else_return_spaces_tabsize_0_function_iter_fun_for_var_i_startrow_i')dent !== -1) {
                if (indent < minIndent)
                    minIndent = indent;
                if (shouldRemove && !testRemove(line, i))
                    shouldRemove = false;
            } else if (minEmptyLength > line.length) {
                minEmptyLength = line.length;
            }
        });

        if (minIndent == Infinity) {
            minIndent = minEmptyLength;
            ignoreBlankLines = false;i18n.t('ui_line_length_minemptylength_line_length_if_minindent_infinity_minindent_minemptylength_ignoreblanklines_false_shouldremove_false_if_insertattabstop_minindent_tabsize_0_minindent_math_floor_minindent_tabsize_tabsize_iter_shouldremove_uncomment_comment_this_syntaxmode_this_toggleblockcomment_function_state_session_range_cursor_var_comment_this_blockcomment_if_comment_return_if_comment_start_comment_0_comment_comment_0_var_iterator_new_tokeniterator_session_cursor_row_cursor_column_var_token_iterator_getcurrenttoken_var_sel_session_selection_var_initialrange_session_selection_toorientedrange_var_startrow_coldiff_if_token_comment_test_token_type_var_startrange_endrange_while_token_comment_test_token_type_var_i_token_value_indexof_comment_start_if_i_1_var_row_iterator_getcurrenttokenrow_var_column_iterator_getcurrenttokencolumn_i_startrange_new_range_row_column_row_column_comment_start_length_break_token_iterator_stepbackward_var_iterator_new_tokeniterator_session_cursor_row_cursor_column_var_token_iterator_getcurrenttoken_while_token_comment_test_token_type_var_i_token_value_indexof_comment_end_if_i_1_var_row_iterator_getcurrenttokenrow_var_column_iterator_getcurrenttokencolumn_i_endrange_new_range_row_column_row_column_comment_end_length_break_token_iterator_stepforward_if_endrange_session_remove_endrange_if_startrange_session_remove_startrange_startrow_startrange_start_row_coldiff_comment_start_length_else_coldiff_comment_start_length_startrow_range_start_row_session_insert_range_end_comment_end_session_insert_range_start_comment_start_todo_selection_should_have_ended_up_in_the_right_place_automatically_if_initialrange_start_row_startrow_initialrange_start_column_coldiff_if_initialrange_end_row_startrow_initialrange_end_column_coldiff_session_selection_fromorientedrange_initialrange_this_getnextlineindent_function_state_line_tab_return_this_getindent_line_this_checkoutdent_function_state_line_input_return_false_this_autooutdent_function_state_doc_row_this_getindent_function_line_return_line_match_s_0_this_createworker_function_session_return_null_this_createmodedelegates_function_mapping_this_embeds_this_modes_for_let_i_in_mapping_if_mapping_i_var_mode_mapping_i_var_id_mode_prototype_id_var_mode_config_modes_id_if_mode_config_modes_id_mode_new_mode_if_config_modes_i_config_modes_i_mode_this_embeds_push_i_this_modes_i_mode_var_delegations_toggleblockcomment_togglecommentlines_getnextlineindent_checkoutdent_autooutdent_transformaction_getcompletions_for_let_i_0_i')            var defaultHandler = scope[functionName];
              scope[delegations[i]] =
                  /** @this {import("i18n.t('ui_ace_internal')").Ace.SyntaxMode} */
                  function () {
                      return this.$delegator(functionName, arguments, defaultHandler);
                  };
            }(this));
        }
    };

    /**
     * @this {SyntaxMode}
     */
    this.$delegator = function(method, args, defaultHandler) {
        var state = args[0] || "i18n.t('ui_start')";
        if (typeof state != "i18n.t('ui_string')") {
            if (Array.isArray(state[2])) {
                var language = state[2][state[2].length - 1];
                var mode = this.$modes[language];
                if (mode)
                    return mode[method].apply(mode, [state[1]].concat([].slice.call(args, 1)));
            }
            state = state[0] || "i18n.t('ui_start')";
        }

        for (var i = 0; i < this.$embeds.length; i++) {
            if (!this.$modes[this.$embeds[i]]) continue;

            var split = state.split(this.$embeds[i]);
            if (!split[0] && split[1]) {
                args[0] = split[1];
                var mode = this.$modes[this.$embeds[i]];
                return mode[method].apply(mode, args);
            }
        }
        var ret = defaultHandler.apply(this, args);
        return defaultHandler ? ret : undefined;
    };

    /**
     * @this {SyntaxMode}
     */
    this.transformAction = function(state, action, editor, session, param) {
        if (this.$behaviour) {
            var behaviours = this.$behaviour.getBehaviours();
            for (var key in behaviours) {
                if (behaviours[key][action]) {
                    var ret = behaviours[key][action].apply(this, arguments);
                    if (ret) {
                        return ret;
                    }
                }
            }
        }
    };

    /**
     * @this {SyntaxMode}
     */
    this.getKeywords = function(append) {
        // this is for autocompletion to pick up regexp'ed keywords
        if (!this.completionKeywords) {
            var rules = this.$tokenizer["i18n.t('ui_rules')"];
            var completionKeywords = [];
            for (var rule in rules) {
                var ruleItr = rules[rule];
                for (var r = 0, l = ruleItr.length; r < l; r++) {
                    if (typeof ruleItr[r].token === "i18n.t('ui_string')") {
                        if (/keyword|support|storage/.test(ruleItr[r].token))
                            completionKeywords.push(ruleItr[r].regex);
                    }
                    else if (typeof ruleItr[r].token === "i18n.t('ui_object')") {
                        for (var a = 0, aLength = ruleItr[r].token.length; a < aLength; a++) {
                            if (/keyword|support|storage/.test(ruleItr[r].token[a])) {
                                // drop surrounding parens
                                var rule = ruleItr[r].regex.match(/\(.+?\)/g)[a];
                                completionKeywords.push(rule.substr(1, rule.length - 2));
                            }
                        }
                    }
                }
            }
            this.completionKeywords = completionKeywords;
        }
        // this is for highlighting embed rules, like HAML/Ruby or Obj-C/C
        if (!append)
            return this.$keywordList;
        return completionKeywords.concat(this.$keywordList || []);
    };

    /**
     * @this {SyntaxMode}
     */
    this.$createKeywordList = function() {
        if (!this.$highlightRules)
            this.getTokenizer();
        return this.$keywordList = this.$highlightRules.$keywordList || [];
    };

    /**
     * @this {SyntaxMode}
     */
    this.getCompletions = function(state, session, pos, prefix) {
        var keywords = this.$keywordList || this.$createKeywordList();
        return keywords.map(function(word) {
            return {
                name: word,
                value: word,
                score: 0,
                meta: "i18n.t('ui_keyword')"
            };
        });
    };

    this.$id = "i18n.t('ui_ace_mode_text')";
}).call(Mode.prototype);

exports.Mode = Mode;