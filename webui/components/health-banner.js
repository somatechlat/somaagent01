/**
 * Phase 3: Health Banner Component
 * Displays memory WAL lag and system health alerts
 */

class HealthBanner {
    constructor(container) {
        this.container = container;
        this.currentHealth = {};
        this.lastCheck = 0;
        
        // Health thresholds
        this.thresholds = {
            wal_lag_warning: 10,      // seconds
            wal_lag_critical: 30,     // seconds
            outbox_warning: 50,       // pending messages
            outbox_critical: 100      // pending messages
        };
        
        this.init();
    }
    
    init() {
        this.createBanner();
        this.startHealthCheck();
        
        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) i18n.t('ui_visibilitychange')  // no-op; no polli18n.t('ui_if_document_hidden_no_op_no_polling_to_stop_else_i18n_t_ui18n.t('ui_if_document_hidden_no_op_no_polling_to_stop_else_i18n_t_ui_if_document_hidden_no_op_no_polling_to_stop_else_trigger_a_one_shot_refresh_when_tab_becomes_visible_this_performhealthcheck_createbanner_const_banner_document_createelement_div_banner_id_memory_health_banner_banner_classname_memory_health_banner_hidden_banner_innerhtml')_ui_i18n_t_ui_health_message')">
                  i18n.t('ui_i18n_t_ui_health_message')18n_t_ui_i18n_t_ui_health_text')"></span>
    i18n.t('ui_i18n_t_ui_health_text')ass="i18n.t('ui_i18n_t_ui_i18n_t_ui_health_details')"i18n.t('ui_i18n_t_ui_health_details')div>
                <div class="i18n.t('ui_i18n_t_ui_i18n_t_ui_health_i18n.t('ui_i18n_t_ui_health_actions')     <button class="i18n.t('ui_i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_health_refresh')h</bi18n.t('ui_refreshi18n.t('ui_refresh')efri18n.t('ui_document_body_appendchild_banner_this_bannerelement_banner_event_listeners_banner_queryselector_health_refresh_addeventlistener_click_this_performhealthcheck_banner_queryselector_health_dismiss_addeventlistener_click_this_hidebanner_async_starthealthcheck_one_shot_initial_check_no_periodic_polling_sse_only_directive_await_this_performhealthcheck_async_performhealthcheck_try_const_response_await_fetch_v1_health_const_health_await_response_json_this_currenthealth_health_this_lastcheck_date_now_const_memoryissues_this_analyzememoryhealth_health_if_memoryissues_length_0_this_showbanner_memoryissues_0_show_most_severe_else_this_hidebanner_catch_error_console_error_health_check_failed_error_this_showbanner_level_error_message_health_check_unavailable_details')    }
        } catch (error) {
    i18n.t('ui_analyzememoryhealth_health_const_issues_check_wal_lag_if_health_components_memory_wal_lag_const_lag_health_components_memory_wal_lag_lag_seconds_if_lag_this_thresholds_wal_lag_critical_issues_push_level_critical_message_memory_sync_critical_details')const lag = health.components.memory_wal_lag.lag_seconds;
            if (lai18n.t('ui_else_if_lag_this_thresholds_wal_lag_warning_issues_push_level_warning_message_memory_sync_delayed_details')oFixed(1)}s (exceeds ${this.ti18n.t('ui_check_outbox_backlog_if_health_components_memory_write_outbox_const_pending_health_components_memory_write_outbox_pending_if_pending_this_thresholds_outbox_critical_issues_push_level_critical_message_memory_backlog_critical_details')ents?.memory_write_outbox) i18n.t('ui_else_if_pending_this_thresholds_outbox_warning_issues_push_level_warning_message_memory_backlog_elevated_details')essage: 'i18n.t('ui_memory_i18n.t('ui_check_component_health_const_memorycomponents_memory_write_outbox_memory_replicator_memory_dlq_memorycomponents_foreach_component_if_health_components_component_status_down_issues_push_level_error_message')            }
        }
  i18n.t('ui_details_health_components_component_detail_service_down_else_if_health_components_component_status_degraded_issues_push_level_warning_message')18n.t('ui_down')') {
  i18n.t('ui_details_health_components_component_detail_performance_issues_return_issues_sort_a_b_const_severity_critical_3_error_2_warning_1_return_severity_b_level_0_severity_a_level_0_showbanner_issue_if_this_bannerelement_return_const_banner_this_bannerelement_const_icon_banner_queryselector_icon_indicator_const_message_banner_queryselector_health_text_const_details_banner_queryselector_health_details_set_content_message_textcontent_issue_message_details_textcontent_issue_details_set_styling_based_on_level_banner_classname')r(issue) {
        if (!this.bannerEli18n.t('ui_icon_textcontent_this_geticon_issue_level_show_banner_banner_classlist_remove_hidden_hidebanner_if_this_bannerelement_this_bannerelement_classlist_add_hidden_geticon_level_const_icons_critical_error_warning_return_icons_level_api_for_other_components_getcurrenthealth_return_this_currenthealth_forcehealthcheck_return_this_performhealthcheck_css_for_health_banner_const_healthstyles')
    hideBanner() {
        if (this.bannerElement) {
            this.bannerElement.classList.add('i18n.t('ui_hidden')');
        }
    }
    
    getIcon(level) {
        const icons = {
            critical: 'i18n.t('ui_')',
            error: '❌'i18n.t('ui_warning')'⚠️'i18n.t('ui_return_icons_level')'ℹ️'i18n.t('ui_api_for_other_components_getcurrenthealth_return_this_currenthealth_forcehealthcheck_return_this_performhealthcheck_css_for_health_banner_const_healthstyles_memory_health_banner_position_fixed_top_0_left_0_right_0_z_index_1000_padding_12px_16px_font_size_14px_box_shadow_0_2px_8px_rgba_0_0_0_0_1_transition_all_0_3s_ease_memory_health_banner_hidden_transform_translatey_100_opacity_0_memory_health_banner_critical_background_fee_color_c53030_border_bottom_2px_solid_e53e3e_memory_health_banner_error_backi18n.t('ui_if_document_hidden_no_op_no_polli18n_t_ui_if_document_hidden_no_op_no_polling_to_stop_else_i18n_t_ui_if_document_hidden_no_op_no_polling_to_stop_else_trigger_a_one_shot_refresh_when_tab_becomes_visible_this_performhealthcheck_createbanner_const_banner_document_createelement_div_banner_id_memory_health_banner_banner_classname_memory_health_banner_hidden_banner_innerhtml')nt_border_1px_solid_currentcolor_color_inherit_padding_4px_8px_border_radius_4px_cursor_pointer_font_size_12px_health_actions_button_hover_background_rgba_0_0_0_0_1_media_max_width_768px_memory_health_banner_padding_8px_12px_font_size_12px_health_content_flex_direction_column_align_items_flex_start_gap_4px_inject_styles_if_document_getelementbyid')'memory-healti18n.t('ui_refresh')s'i18n.t('ui_const_stylesheet_document_createelement')'style'i18n.t('ui_stylesheet_id')'memory-health-styles'i18n.t('ui_stylesheet_textcontent_healthstyles_document_head_appendchild_stylesheet_initialize_on_page_load_document_addeventlistener')'DOMContentLoaded'i18n.t('ui_initialize_health_banner_if_ui_is_loaded_if_typeof_window')'undefined'i18n.t('ui_window_memoryhealthbanner_new_healthbanner_document_body_export_for_modules_if_typeof_module')'undefined' && module.exports) {
    module.exports = { HealthBanner };
}