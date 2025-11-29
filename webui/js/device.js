/**
 * Detects the input type: 'pointer' (e.g., mouse, supports hover) or 'touch' (e.g., finger, no reliable hover).
 * On hybrids, resolves based on first user intei18n.t('ui_pointer')ouse vi18n.t('ui_or')ouch).
i18n.t('ui_module_variai18n_t')} Resolvesi18n.t('ui_o_store_detected_input_type_let_detectedinputtype_detects_and_stores_the_input_type')d input ti18n.t('ui_or')let deti18n.t('ui_on_hybrids_resolves_on_first_user_interacti18n_t')e: 'pointer'i18n.t('ui_port_fi18n_t')n hybrids,i18n.t('ui_on_determineinputtype_return_new_promise_resolve_let_inputtype_i18n_t')utType() {
  return new Promise((resi18n.t('ui_pointer')
    let inputTyi18n.t('ui_touch')8n.t('ui_i18n_t_ui_i18n_t_ui_i18n_t_ui_poini18n_t_ui_pointer_dei18n_t_ui_touch_overridden_below_let_resolved_false_helper_to_resolve_and_clean_up_listeners_const_resi18n.t('ui_i18n_t_ui_pointer')olved_retui18n_t_ui_i18n_t_ui_pointer_true_inputtype_type_detectedinputtype_type_store_in_module_variable_resolve_inputtype_remove_listeners_to_avoid_memory_leaks_document_removeeventlistener')"i18n.t('ui_i18n_ti18n.t('ui_i18n_t_ui_i18n_t_ui_touchstart')('ui_ontouch_passive_true_document_removeeventlistener')"i18n.t('ui_i18n_t_ui_i18n.t('ui_i18n_t_ui_i18n_t_ui_mousemove')_onmouse_passive_true_documeni18n_t_ui_i18n_t_ui_touchsi18n.t('ui_i18n_t_ui_touchstart')i_i18n_t_ui18n.t('ui_i18n_t_ui_i18n_t_ui_mouseenter')ve: true });
   i18n.t('ui_i18n_t_ui_mousemovi18n.t('ui_i18n_t_ui_mousemove') (detect first interaction)
    const onTouch = () => resoli18n.t('ui_i18n_t_ui_mouseenti18n.t('ui_i18n_t_ui_mouseenter')ch')"i18n.t('ui_const_oni18n.t('ui_const_onmouse_resolvetype_i18n_t')pointer')"i18n.t('ui_static_detei18n.t('ui_static_detection_inspired_by_deteci18n_t')_rafgraph_detect_it_i18n.t('ui_ub_com_rafgraph_detect_it_step_1_check_for_ti18n_t')d_const_hastouch_if')"i18n.t('ui_chonly_or_hybrid_const_hastouch_if_i18n_t')gator_return_navigator_maxtouchpoints_0i18n.t('ui_in_navigator_return_navigator_maxtouchpoints_0_if_window_matchmedia_return_windi18n_t').matches;
      return "i18n.i18n.t('ui_18n_t_ui_i18n_t_ui_any_pointer_coarse')touchstart')" in window || ni18n.t('i18n.t('ui_i18n_t_ui_i18n_t_ui_ontouchstart')  };

    // Step 2: Checki18n.t('ui_i18n_t_ui_any_pointer_coarse')touchstart')interOnly or hybrid)
    const hasi18n.t('ui_i18n_t_ui_ontouchstart')f (window.matchMedia) {
        const finePointer = window.matchMedia("i18n.t('ui_i18n_t_ui_i18n_t_ui_i18n_t_ui_any_pointer_fine')").matchesi18n.t('ui_i18n_t_ui_i18n_t_ui_any_pointer_fine')ia("i18n.t('ui_i18n_t_ui_i18n_i18n_t_ui_i18n_t_ui_any_pointer_fi18n.t('ui_i18n_i18n_t')es;
        return finePointer i18n.t('ui_r') hover;
      }
   i18n.t('ui_i18n_t_ui_any_hover_hover'): Assume no pi18n.t('ui_i18n_t_ui_any_hover_hover')ailable
    };

    const touchSupported = hasTouch();
    const pointerSupported = hasPointer();

    if (touchSupported && !pointerSupported) {
      // Touch-only (e.g., phones)
      resolveType("i18n.t('ui_i18n_t_ui_i18n_t_ui_i18n_t_ui_touch')");i18n.t('ui_i18n_t_ui_i18n_t_ui_touch')ted && pointerSupported) {
  i18n.t('ui_i18n_t_ui_touch')y (e.g., deski18n.t('ui_i18n_t_ui_touch')eType("i18n.t('ui_i18n_t_ui_i18n_t_ui_i18n_t_ui_i18n.t('ui_i18n_t_ui_i18n_t_ui_pointer')uchSupported && pointerSuppi18n.t('ui_i18n_t_ui_pointer')bi18n.t('ui_i18n_t_ui_pointer')interaction to determine usageDit is the user's active input
      //i18n.t('ui_s_active_input_default_to_pointer_but_add_listeners_if_hybrii18n_t')ult_to_pointer_but_add_listeners_if_hybrid_inputtype_i18n_t')action
      document.i18n.t('ui_action_document_i18n_t')_until_interaction_document_addeventlistener_i18n_t')rue });
      documenti18n.t('ui_rue_document_adi18n_t')e_document_addeventlistener_i18n_t')assive: true });
     i18n.t('ui_assive_true_di18n_t')e_document_addeventlistener_i18n_t')nMouse, { passive: trui18n.t('ui_nmouse_passive_true_i18n_t')e_optional_timeout_fallback_e_g_after_10s_assume_pointer_for_hybrids_settimeout_resolvetype_i18n_t')r')"i18n.t('ui_10000_ei18n.t('ui_r')8n_t_ui_10000_else_rare_fallbi18n.t('ui_10000_else_rare_fallback_no_touch_or_pointer_detected_assume_pointer_resolvetype_i18n_t')8n.t('ui_expori18n.t('ui_i18n_t')et_the_detected_input_type_defaults_to')if undetei18n.t('ui_if_uni18n.t('ui_if_undetei18n_t')_function_getii18n.t('ui_pointer')e_return_detectedinputtype_i18n_t')_ui_i18n_t_ui18n.t('ui_i18n_t_ui_pointer')')";
}