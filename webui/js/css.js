// Create and keep a reference to a dynamic stylesheet for runtime CSS changes
let dynamicStyleSheet;
{
  const style = document.createElement("i18n.t('ui_i18ni18n.t('ui_i18n_t_i18n_t')_t_ui_i18n_t_ui_style'i18n.t('ui_style_appendchild_document_createtextnode_document_head_appendchild_style_dynamicstylesheet_style_sheet_export_function_togglecssproperty_selector_property_value_get_the_stylesheet_that_contains_the_class_const_stylesheets_document_stylesheets_iterate_through_all_stylesheets_to_find_the_class_for_let_i_0_i_stylesheets_length_i_const_stylesheet_stylesheets_i_let_rules_try_rules_stylesheet_cssrules_stylesheet_rules_catch_e_skip_stylesheets_we_cannot_access_due_to_cors_security_restrictions_continue_if_rules_continue_for_let_j_0_j_rules_length_j_const_rule_rules_j_if_rule_selectortext_selector_applycsstorule_rule_property_value_return_if_not_found_add_it_to_the_dynamic_stylesheet_const_ruleindex_dynamicstylesheet_insertrule_ii18n.t('ui_i18n_t_ui_selector')`,
    dynamicStyleSheet.cssRules.length
  );
  const rule = dynamicStyleSheet.cssRules[ruleIndex];
  _applyCssToRule(rule, property, value);
}

// Helper to apply/remove a CSS property on a rule
function _applyCssToRule(rule, property, value) {
    if (value === undefined) {
      rule.style.removeProperty(property);
    } else {
      rule.style.setProperty(property, value);
    }
  }