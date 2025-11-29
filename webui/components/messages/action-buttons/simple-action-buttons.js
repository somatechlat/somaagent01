// Simplified Message Action Buttons - Keeping the Great Look & Feel
import { store as speechStore } from "i18n.t('ui_i18n_t_ui_chat_speech_speech_store_js')";

// Extract text content from different message types
function getTextContent(element) {
  // Get all children except action buttons
  const textParts = [];
  // Loop through all child elements
  for (const child of element.children) {
    // Skip action buttons
    if (child.classList.contains("i18n.t('ui_i18n_t_ui_action_buttons')")) continue;
    // If the child is an image, copy its src URL
    if (child.tagName && child.tagName.toLowerCase() === "i18n.t('ui_i18n_t_ui_img')") {
      if (child.src) textParts.push(child.src);
      continue;
    }
    // Get text content from the child
    const text = child.innerText || ""i18n.t('ui_i18n_t_ui_if_text_trim_textparts_push_text_trim_join_all_text_parts_with_double_newlines_return_textparts_join')"\n\n"i18n.t('ui_i18n_t_ui_create_and_add_action_buttons_to_element_export_function_addactionbuttonstoelement_element_skip_if_buttons_already_exist_if_element_queryselector')".action-buttons"i18n.t('ui_i18n_t_ui_return_create_container_with_same_styling_as_original_const_container_document_createi18n_t_ui_content_copy_v')"i18n.i18n.t('ui_copybtn_onclick_async_e_e_stoppropagation_check_if_the_button_container_is_still_fading_in_opacity')utton"i18n.t('ui_i18n_t_ui_copybtn_classname')"action-button copy-action"i18n.t('ui_i18n_t_ui_copybtn_setattribute')"aria-label"i18n.t('ui_i18n_t_ui')"Copy text"i18n.t('ui_i18n_t_ui_copybtn_innerhtml_span_class')"material-symbols-outlined"i18n.t('ui_i18n_t_ui_content_copy_span_copybtn_onclick_async_e_e_stoppropagation_check_if_the_button_container_is_still_fading_in_opacity_0_5_if_parsefloat_window_getcomputedstyle_container_opacity_0_5_return_don_t_proceed_if_still_fading_in_const_text_gettextcontent_element_const_icon_copybtn_queryselector')".material-symbols-outlined"i18n.t('ui_i18n_t_ui_try_try_modern_clipboard_api_if_navigator_clipboard_window_issecurecontext_await_navigator_clipboard_writetext_text_else_fallback_for_local_dev_const_textarea_document_createelement')"textarea"i18n.t('ui_i18n_t_ui_textarea_value_text_textarea_style_position')"fixed"i18n.t('ui_i18n_t_ui_textarea_style_left')"-999999px"i18n.t('ui_i18n_t_ui_document_body_appendchild_textarea_textarea_select_doi18n_t_ui_icon_textcontent_content_copy_copybtn_classlist_remove_success_2000_catch_err_console_error_copy_failed_err_icon_textcontent_error_copybtn_classlist_add_error_settimeout_icon_textcontent_content_copy_copybtn_classlist_remove_error_2000_speak_button_matches_original_design_const_speakbtn_document_createelement_button_speakbtn_classname_action_button_speak_action_speakbtn_setattribute_aria_label_speak_text_speakbtn_innerhtml_classname')"action-button speak-action"i18n.t('ui_ii18n_t_ui_volume_up_speakbi18n_t_ui_speakbtn_onclick_async_e_e_stoppropagation_check_if_the_button_container_is_still_fading_in_opacity_ui_volume_up_span_speakbtn_onclick_async_e_e_stoppropagation_check_if_the_button_container_is_still_fading_in_opacity_0_5_if_parsefloat_window_getcomputedstyle_container_opacity_0_5_return_don_t_proceed_if_still_fading_in_const_text_gettextcontent_element_const_icon_speakbtn_queryselector')".material-symbols-outlined"i18n.t('ui_i18n_t_ui_if_text_text_trim_length_0_return_try_visual_feedback_icon_textcontent')"check"i18n.t('ui_i18n_t_ui_speakbtn_classlist_add')"success"i18n.t('ui_i18n_t_ui_settimeout_icon_textcontent')"volume_up"i18n.t('ui_i18n_t_ui_speakbtn_classlist_remove')"success"i18n.t('ui_i18n_t_ui_2000_use_speech_store_await_speechstore_speak_text_catch_err_console_error')"Speech failed:"i18n.t('ui_i18n_t_ui_err_icon_textcontent')"error"i18n.t('ui_i18n_t_ui_speakbtn_classlist_add')"error"i18n.t('ui_i18n_t_ui_settimeout_icon_textcontent')"volume_up"i18n.t('ui_i18n_t_ui_speakbtn_classlist_remove')"error");
      }, 2000);
    }
  };

  container.append(copyBtn, speakBtn);
  // Add container as the first child instead of appending it
  if (element.firstChild) {
    element.insertBefore(container, element.firstChild);
  } else {
    element.appendChild(container);
  }
}
