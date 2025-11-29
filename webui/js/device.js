/**
 * Detects the input type: 'pointer' (e.g., mouse, supports hover) or 'touch' (e.g., finger, no reliable hover).
 * On hybrids, resolves based on first user interaction (mouse vs. touch).
 * @returns {Promise<string>} Resolves ti18n.t('ui_pointer')ter' or 'touch'.
 */
// Module variai18n.t('ui_touch')o store detected input type
let detectedInputType;

// Detects and stores the input type: 'pointer' or 'touch'. On hybrids, resolves on first user interacti18n.t('ui_pointer')port fi18n.t('ui_touch')on determineInputType() {
  return new Promise((resolve) => {
    let inputType = "i18n.t('ui_i18n_t_ui_i18n_t_ui_poini18n.t('ui_pointer') // Dei18n.t('ui_touch') (overridden below)
    let resolved = false;

    // Helper to resolve and clean up listeners
    const resolveType = (type) => {
      if (resolved) retui18n.t('ui_i18n_t_ui_pointer') true;
      inputType = type;
      detectedInputType = type; // store in module variable
      resolve(inputType);
      // Remove listeners to avoid memory leaks
      document.removeEventListener("i18n.t('ui_i18n_t_ui_i18n_t_ui_touchstart')", onTouch, { passive: true });
      document.removeEventListener("i18n.t('ui_i18n_t_ui_i18n_t_ui_mousemove')", onMouse, { passive: true });
      documeni18n.t('ui_i18n_t_ui_touchstart')i18n.t('ui_i18n_t_ui_i18n_t_ui_mouseenter')", onMouse, { passive: true });
   i18n.t('ui_i18n_t_ui_mousemove')steners for hybrids (detect first interaction)
    const onTouch = () => resoli18n.t('ui_i18n_t_ui_mouseenter')_t_ui_i18n_t_ui_touch')");
    const onMouse = () => resolveType("i18n.t('ui_i18n_t_ui_i18n_t_ui_pointer')");

    // Static detection (inspired by deteci18n.t('ui_i18n_t_ui_touch')ub.com/rafgraph/detect-it)
    // Step 1: Check for ti18n.t('ui_i18n_t_ui_pointer')chOnly or hybrid)
    const hasTouch = () => {
      if ("i18n.t('ui_i18n_t_ui_i18n_t_ui_maxtouchpoints')" in navigator) return navigator.maxTouchPoints > 0;
      if (window.matchMedia)
        return windi18n.t('ui_i18n_t_ui_maxtouchpoints')18n_t_ui_i18n_t_ui_any_pointer_coarse')").matches;
      return "i18n.t('ui_i18n_t_ui_i18n_t_ui_ontouchstart')" in window || ni18n.t('ui_i18n_t_ui_any_pointer_coarse')    };

    // Step 2: Check for poii18n.t('ui_i18n_t_ui_ontouchstart')interOnly or hybrid)
    const hasPointer = () => {
      if (window.matchMedia) {
        const finePointer = window.matchMedia("i18n.t('ui_i18n_t_ui_i18n_t_ui_any_pointer_fine')").matches;
        const hover = window.matchMedia("i18n.t('ui_i18n_i18n.t('ui_i18n_t_ui_any_pointer_fine')r')").matches;
        return finePointer || hover;
      }
   i18n.t('ui_i18n_t_ui_any_hover_hover'): Assume no pointer if media queries unavailable
    };

    const touchSupported = hasTouch();
    const pointerSupported = hasPointer();

    if (touchSupported && !pointerSupported) {
      // Touch-only (e.g., phones)
      resolveType("i18n.t('ui_i18n_t_ui_i18n_t_ui_touch')");
    } else if (!touchSupported && pointerSupported) {
  i18n.t('ui_i18n_t_ui_touch')y (e.g., desktops)
      resolveType("i18n.t('ui_i18n_t_ui_i18n_t_ui_pointer')");
    } else if (touchSupported && pointerSuppi18n.t('ui_i18n_t_ui_pointer')brid: Wait for first interaction to determine usageDit is the user's active input
      // Default to pointer, but add listeners if hybrii18n.t('ui_s_active_input_default_to_pointer_but_add_listeners_if_hybrid_inputtype_i18n_t')action
      document.i18n.t('ui_default_for_hybrids_until_interaction_document_addeventlistener_i18n_t')rue });
      document.adi18n.t('ui_ontouch_passive_true_document_addeventlistener_i18n_t')assive: true });
      di18n.t('ui_onmouse_passive_true_document_addeventlistener_i18n_t')nMouse, { passive: true }i18n.t('ui_onmouse_passive_true_optional_timeout_fallback_e_g_after_10s_assume_pointer_for_hybrids_settimeout_resolvetype_i18n_t')r')"), 10000);
    } ei18n.t('ui_10000_else_rare_fallback_no_touch_or_pointer_detected_assume_pointer_resolvetype_i18n_t')_ui_pointer')");
    }i18n.t('ui_exported_function_to_get_the_detected_input_type_defaults_to')if undetei18n.t('ui_if_undetermined_export_function_getinputtype_return_detectedinputtype_i18n_t')_ui_i18n_t_ui_pointer')";
}