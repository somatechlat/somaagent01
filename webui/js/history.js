import { getContext } from "i18n.t('ui_i18n_t_ui_index_js')";

export async function openHistoryModal() {
    try {
        const hist = await window.sendJsonData("i18n.t('ui_i18n_t_ui_history_get')", { context: getContext() });
        // const data = JSON.stringify(hist.history, null, 4);
        const data = hist.history
        const size = hist.tokens
        await showEditorModal(data, "i18n.t('ui_i18n_t_ui_markdown')", `History ~${size} tokens`, "i18n.t('ui_i18n_t_ui_conversation_history_visible_to_the_llm_history_is_compressed_to_fit_into_the_context_window_over_time')");
    } catch (e) {
        window.toastFrontendError("i18n.t('ui_i18n_t_ui_error_fetching_history')" + e.message, "i18n.t('ui_i18n_t_ui_chat_history_error')");
        return
    }
}

export async function openCtxWindowModal() {
    try {
        const win = await window.sendJsonData("i18n.t('ui_i18n_t_ui_ctx_window_get')", { context: getContext() });
        const data = win.content
        const size = win.tokens
        await showEditorModal(data, "i18n.t('ui_i18n_t_ui_markdown')", `Context window ~${size} tokens`, "i18n.t('ui_i18n_t_ui_data_passed_to_the_llm_during_last_interaction_contains_system_message_conversation_history_and_rag')");
    } catch (e) {
        window.toastFrontendError("i18n.t('ui_i18n_t_ui_error_fetching_context')" + e.message, "i18n.t('ui_i18n_t_ui_context_error')");
        return
    }
}

async function showEditorModal(data, type = "i18n.t('ui_i18n_t_ui_json')", title, description = ""i18n.t('ui_i18n_t_ui_generate_the_html_with_json_viewer_container_const_html_div_id')"json-viewer-container"i18n.t('ui_i18n_t_ui_div_open_the_modal_with_the_generated_html_await_window_genericmodalproxy_openmodal_title_description_html')"history-viewer"i18n.t('ui_i18n_t_ui_initialize_the_json_viewer_after_the_modal_is_rendered_const_container_document_getelementbyid')"json-viewer-container"i18n.t('ui_i18n_t_ui_if_container_const_editor_ace_edit')"json-viewer-container"i18n.t('ui_i18n_t_ui_const_dark_localstorage_getitem_darkmode_if_dark')"false"i18n.t('ui_i18n_t_ui_editor_settheme')"ace/theme/github_dark"i18n.t('ui_i18n_t_ui_else_editor_settheme')"ace/theme/tomorrow"i18n.t('ui_i18n_t_ui_editor_session_setmode')"ace/mode/" + type);
        editor.setValue(data);
        editor.clearSelection();
        // editor.session.$toggleFoldWidget(5, {})
    }
}

window.openHistoryModal = openHistoryModal;
window.openCtxWindowModal = openCtxWindowModal;
