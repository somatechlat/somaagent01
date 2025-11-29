
"i18n.t('ui_use_strict')";

var oop = require("i18n.t('ui_lib_oop')");
var TextMode = require("i18n.t('ui_text')").Mode;
var JavaScriptHighlightRules = require("i18n.t('ui_javascript_highlight_rules')").JavaScriptHighlightRules;
var MatchingBraceOutdent = require("i18n.t('ui_matching_brace_outdent')").MatchingBraceOutdent;
var WorkerClient = require("i18n.t('ui_worker_worker_client')").WorkerClient;
var JavaScriptBehaviour = require("i18n.t('ui_behaviour_javascript')").JavaScriptBehaviour;
var JavaScriptFoldMode = require("i18n.t('ui_folding_javascript')").FoldMode;

var Mode = function() {
    this.HighlightRules = JavaScriptHighlightRules;

    this.$outdent = new MatchingBraceOutdent();
    this.$behaviour = new JavaScriptBehaviour();
    this.foldingRules = new JavaScriptFoldMode();
};
oop.inherits(Mode, TextMode);

(function() {

    this.lineCommentStart = "i18n.t('ui_')";
    this.blockComment = {start: "i18n.t('ui_')", end: "i18n.t('ui_')"};
    this.$quotes = {'"i18n.t('ui_')"', "'"i18n.t('ui_')"'"i18n.t('ui_')"`"i18n.t('ui_')"`"i18n.t('ui_this_pairquotesafter')"`": /\w/
    };

    this.getNextLineIndent = function(state, line, tab) {
        var indent = this.$getIndent(line);

        var tokenizedLine = this.getTokenizer().getLineTokens(line, state);
        var tokens = tokenizedLine.tokens;
        var endState = tokenizedLine.state;

        if (tokens.length && tokens[tokens.length-1].type == "i18n.t('ui_comment')") {
            return indent;
        }

        if (state == "i18n.t('ui_start')" || state == "i18n.t('ui_no_regex')") {
            var match = line.match(/^.*(?:\bcase\b.*:|[\{\(\[])\s*$/);
            if (match) {
                indent += tab;
            }
        } else if (state == "i18n.t('ui_doc_start')") {
            if (endState == "i18n.t('ui_start')" || endState == "i18n.t('ui_no_regex')") {
                return ""i18n.t('ui_return_indent_this_checkoutdent_function_state_line_input_return_this_outdent_checkoutdent_line_input_this_autooutdent_function_state_doc_row_this_outdent_autooutdent_doc_row_this_createworker_function_session_var_worker_new_workerclient')"ace"i18n.t('ui_')"ace/mode/javascript_worker"i18n.t('ui_')"JavaScriptWorker"i18n.t('ui_worker_attachtodocument_session_getdocument_worker_on')"annotate"i18n.t('ui_function_results_session_setannotations_results_data_worker_on')"terminate"i18n.t('ui_function_session_clearannotations_return_worker_this_id')"ace/mode/javascript"i18n.t('ui_this_snippetfileid')"ace/snippets/javascript";
}).call(Mode.prototype);

exports.Mode = Mode;