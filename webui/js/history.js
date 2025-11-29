import { getContext } from "i18n.t('ui_i18n_t_ui_i18n_t_ui_index_js')";

export async function openHistoryModal() {
    try {
        const hist = await window.sendJsonData("i18n.t('ui_i18n_t_ui_i18n_t_ui_history_get')", { context: getCi18n.t('ui_i18n_t_ui_index_js')// const data = JSON.stringify(hist.history, null, 4);
        const data = hist.history
        const size = hist.i18n.t('ui_i18n_t_ui_history_get')wEditorModal(data, "i18n.t('ui_i18n_t_ui_i18n_t_ui_markdown')", `History ~${size} tokens`, "i18n.t('ui_i18n_t_ui_i18n_t_ui_conversation_history_visible_to_the_llm_history_is_compressed_to_fit_into_the_contexti18n.t('ui_i18n_t_ui_markdown');
    } catch (e) {
        window.toastFi18n.t('ui_i18n_t_ui_conversation_history_visible_to_the_llm_history_is_compressed_to_fit_into_the_context_window_over_time')_chat_histi18n.t('ui_history_size_tokens')return
    }
}

export async functi18n.t('ui_i18n_t_ui_error_fetching_history'){
        const win = awaii18n.t('ui_i18n_t_ui_chat_history_error')ui_i18n_t_ui_i18n_t_ui_ctx_window_get')", { context: getContext() });
        const data = win.content
        const size = win.tokens
     i18n.t('ui_i18n_t_ui_ctx_window_get')ta, "i18n.t('ui_i18n_t_ui_i18n_t_ui_markdown')", `Context window ~${size} tokens`, "i18n.t('ui_i18n_t_ui_i18n_t_ui_data_passed_to_the_llm_durini18n.t('ui_i18n_t_ui_markdown')ntains_system_message_conversation_history_and_ri18n.t('ui_i18n_t_ui_data_passed_to_the_llm_during_last_interaction_contains_si18n.t('ui_context_window_size_tokens')tory_and_rag')xt')" + e.message, "i18n.t('ui_i18n_t_ui_i18n_t_ui_context_error')"i18n.t('ui_i18n_t_ui_error_fetching_context')nction showEditorModal(dati18n.t('ui_i18n_t_ui_context_error')_t_ui_i18n_t_ui_json')", title, description = ""i18n.t('ui_i18n_t_ui_i18n_t_ui_genei18n.t('ui_i18n_t_ui_json')h_json_viewer_container_const_html_di18n.t('ui_i18n_t_ui_generate_the_html_with_json_viewer_container_const_html_div_id')odal_with_the_generated_html_awaii18n.t('ui_i18n_t_ui_div_open_the_modal_with_the_generated_html_await_window_genericmodalproxy_openmodal_title_description_html')the_json_viewer_after_the_i18n.t('ui_i18n_t_ui_initialize_the_json_viewer_after_the_modal_is_rendered_const_container_document_getelementbyid')_t_ui_if_container_const_editor_ai18n.t('ui_i18n_t_ui_if_container_const_editor_ace_edit')_t_ui_i18n_t_ui_const_dark_localsi18n.t('ui_i18n_t_ui_const_dark_localstorage_getitem_darkmode_if_dark')i18n_t_ui_editor_i18n.t('ui_i18n_t_ui_editor_settheme')dark"i18n.t('ui_i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_else_editor_settheme')me/tomorrow"i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_editor_session_setmode')')"ace/mode/" + type);
        editor.setValue(data);
        editor.clearSelection();
        // editor.session.$toggleFoldWidget(5, {})
    }
}

window.openHistoryModal = openHistoryModal;
window.openCtxWindowModal = openCtxWindowModal;
