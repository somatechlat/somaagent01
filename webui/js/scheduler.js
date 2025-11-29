/**
 * Task Scheduler Component for Settings Modal
 * Manages scheduled and ad-hoc tasks through a dedicated settings tab
 */

import { formatDateTime, getUserTimezone } from './time-utils.js';
import { switchFromContext } from '../index.js';
import * as bus from "i18n.t('ui_i18n_t_ui_event_bus_js')";

// Ensure the showToast function is available
// if (typeof window.showToast !== 'function') {
//     window.showToast = function(message, type = 'info') {
//         console.log(`[Toast ${type}]: ${message}`);
//         // Create toast element if not already present
//         let toastContainer = document.getElementById('toast-container');
//         if (!toastContainer) {
//             toastContainer = document.createElement('div');
//             toastContainer.id = 'toast-container';
//             toastContainer.style.position = 'fixed';
//             toastContainer.style.bottom = '20px';
//             toastContainer.style.right = '20px';
//             toastContainer.style.zIndex = '9999';
//             document.body.appendChild(toastContainer);
//         }

//         // Create the toast
//         const toast = document.createElement('div');
//         toast.className = `toast toast-${type}`;
//         toast.style.padding = '10px 15px';
//         toast.style.margin = '5px 0';
//         toast.style.backgroundColor = type === 'error' ? '#f44336' :
//                                     type === 'success' ? '#4CAF50' :
//                                     type === 'warning' ? '#ff9800' : '#2196F3';
//         toast.style.color = 'white';
//         toast.style.borderRadius = '4px';
//         toast.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
//         toast.style.width = 'auto';
//         toast.style.maxWidth = '300px';
//         toast.style.wordWrap = 'break-word';

//         toast.innerHTML = message;

//         // Add to container
//         toastContainer.appendChild(toast);

//         // Auto remove after 3 seconds
//         setTimeout(() => {
//             if (toast.parentNode) {
//                 toast.style.opacity = '0';
//                 toast.style.transition = 'opacity 0.5s ease';
//                 setTimeout(() => {
//    i18n.t('ui_if_toast_parentnode_toast_style_opacity_0_toast_style_transition_opacity_0_5s_ease_settimeout_if_toast_parentnode_toast_parentnode_removechild_toast_500_3000_add_this_near_the_top_of_the_scheduler_js_file_outside_of_any_function_const_showtoast_function_message_type_info_use_new_frontend_notification_system_if_window_alpine_window_alpine_store_window_alpine_store_notificationstore_const_store_window_alpine_store_notificationstore_switch_type_tolowercase_case_error_return_store_frontenderror_message_scheduler_5_case_success_return_store_frontendinfo_message_scheduler_3_case_warning_return_store_frontendwarning_message_scheduler_4_case_info_default_return_store_frontendinfo_message_scheduler_3_else_fallback_to_global_toast_function_or_console_if_typeof_window_toast_function_window_toast_message_type_else_console_log_scheduler_type_touppercase_message_define_the_full_component_implementation_const_fullcomponentimplementation_function_return_tasks_isloading_true_selectedtask_null_expandedtaskid_null_sortfield_name_sortdirection_asc_filtertype_all_all_scheduled_adhoc_planned_filterstate_all_all_idle_running_disabled_error_polling_removed_rely_on_sse_driven_invalidations_editingtask_name_type_scheduled_state_idle_schedule_minute_hour_day_month_weekday_timezone_getusertimezone_token_plan_todo_in_progress_null_done_system_prompt_prompt_attachments_iscreating_false_isediting_false_showloadingstate_false_viewmode_list_controls_whether_to_show_list_or_detail_view_selectedtaskfordetail_null_task_object_for_detail_view_attachmentstext_filteredtasks_hasnotasks_true_add_explicit_reactive_property_initialize_the_component_init_initialize_component_data_this_tasks_this_isloading_true_this_hasnotasks_true_add_explicit_reactive_property_this_filtertype_all_this_filterstate_all_this_sortfield_name_this_sortdirection_asc_no_polling_state_polling_removed_rely_on_sse_bus_invalidations_only_refresh_initial_data_this_fetchtasks_set_up_event_handler_for_tab_selection_to_ensure_view_is_refreshed_when_tab_becomes_visible_document_addeventlistener_click_event_check_if_a_tab_was_clicked_const_clickedtab_event_target_closest_settings_tab_if_clickedtab_clickedtab_getattribute_data_tab_scheduler_settimeout_this_fetchtasks_100_watch_for_changes_to_the_tasks_array_to_update_ui_this_watch_tasks_newtasks_this_updatetasksui_this_watch_filtertype_this_updatetasksui_this_watch_filterstate_this_updatetasksui_set_up_default_configuration_this_viewmode_localstorage_getitem_scheduler_view_mode_list_this_selectedtask_null_this_expandedtaskid_null_this_editingtask_name_type_scheduled_state_idle_schedule_minute_hour_day_month_weekday_timezone_getusertimezone_token_this_generaterandomtoken_this_generaterandomtoken_plan_todo_in_progress_null_done_system_prompt_prompt_attachments_initialize_flatpickr_for_date_time_pickers_after_alpine_is_fully_initialized_this_nexttick_wait_until_dom_is_updated_settimeout_if_this_iscreating_this_initflatpickr_create_else_if_this_isediting_this_initflatpickr_edit_100_subscribe_to_sse_bus_for_task_updates_this_busunsubs_this_busunsubs_push_bus_on_task_list_update_this_fetchtasks_this_busunsubs_push_bus_on_sse_event_ev_try_const_t_ev_type_tolowercase_if_t_startswith_task_t_tool_result_t_assistant_final_this_fetchtasks_catch_cleanup_on_component_destruction_this_cleanup_console_log_cleaning_up_schedulersettings_component_if_array_isarray_this_busunsubs_this_busunsubs_foreach_u_try_u_catch_this_busunsubs_clean_up_any_flatpickr_instances_const_createinput_document_getelementbyid_newplannedtime_create_if_createinput_createinput_flatpickr_createinput_flatpickr_destroy_const_editinput_document_getelementbyid_newplannedtime_edit_if_editinput_editinput_flatpickr_editinput_flatpickr_destroy_polling_removed_no_periodic_network_calls_fetch_tasks_from_api_async_fetchtasks_don_t_fetch_while_creating_editing_a_task_if_this_iscreating_this_isediting_return_this_isloading_true_try_const_response_await_fetchapi_scheduler_tasks_list_method_post_headers_content_type_application_json_body_json_stringify_timezone_getusertimezone_if_response_ok_throw_new_error_failed_to_fetch_tasks_const_data_await_response_json_check_if_data_tasks_exists_and_is_an_array_if_data_data_tasks_console_error_invalid_response_data_tasks_is_missing_data_this_tasks_else_if_array_isarray_data_tasks_console_error_invalid_response_data_tasks_is_not_an_array_data_tasks_this_tasks_else_verify_each_task_has_necessary_properties_const_validtasks_data_tasks_filter_task_if_task_typeof_task_object_console_error_invalid_task_not_an_object_task_return_false_if_task_uuid_console_error_task_missing_uuid_task_return_false_if_task_name_console_error_task_missing_name_task_return_false_if_task_type_console_error_task_missing_type_task_return_false_return_true_if_validtasks_length_data_tasks_length_console_warn_filtered_out_data_tasks_length_validtasks_length_invalid_tasks_this_tasks_validtasks_update_ui_using_the_shared_function_this_updatetasksui_catch_error_console_error_error_fetching_tasks_error_showtoast_failed_to_fetch_tasks_error_message_error_reset_tasks_to_empty_array_on_error_this_tasks_finally_this_isloading_false_change_sort_field_direction_changesort_field_if_this_sortfield_field_toggle_direction_if_already_sorting_by_this_field_this_sortdirection_this_sortdirection_asc_desc_asc_else_set_new_sort_field_and_default_to_ascending_this_sortfield_field_this_sortdirection_asc_toggle_expanded_task_row_toggletaskexpand_taskid_if_this_expandedtaskid_taskid_this_expandedtaskid_null_else_this_expandedtaskid_taskid_show_task_detail_view_showtaskdetail_taskid_const_task_this_tasks_find_t_t_uuid_taskid_if_task_showtoast_task_not_found_error_return_create_a_copy_of_the_task_to_avoid_modifying_the_original_this_selectedtaskfordetail_json_parse_json_stringify_task_ensure_attachments_is_always_an_array_if_this_selectedtaskfordetail_attachments_this_selectedtaskfordetail_attachments_this_viewmode_detail_close_detail_view_and_return_to_list_closetaskdetail_this_selectedtaskfordetail_null_this_viewmode_list_format_date_for_display_formatdate_datestring_if_datestring_return_never_return_formatdatetime_datestring_full_format_plan_for_display_formatplan_task_if_task_task_plan_return_no_plan_const_todocount_array_isarray_task_plan_todo_task_plan_todo_length_0_const_inprogress_task_plan_in_progress_yes_no_const_donecount_array_isarray_task_plan_done_task_plan_done_length_0_let_nextrun_if_array_isarray_task_plan_todo_task_plan_todo_length_0_try_const_nexttime_new_date_task_plan_todo_0_verify_it_s_a_valid_date_before_formatting_if_isnan_nexttime_gettime_nextrun_formatdatetime_nexttime_short_else_nextrun_invalid_date_console_warn_invalid_date_format_in_plan_todo_0_task_plan_todo_0_catch_error_console_error_error_formatting_next_run_time_error_message_nextrun_error_else_nextrun_none_return_next_nextrun_ntodo_todocount_nin_progress_inprogress_ndone_donecount_format_schedule_for_display_formatschedule_task_if_task_schedule_return_none_let_schedule_if_typeof_task_schedule_string_schedule_task_schedule_else_if_typeof_task_schedule_object_display_only_the_cron_parts_not_the_timezone_schedule_task_schedule_minute_task_schedule_hour_task_schedule_day_task_schedule_month_task_schedule_weekday_return_schedule_get_css_class_for_state_badge_getstatebadgeclass_state_switch_state_case_idle_return_scheduler_status_idle_case_running_return_scheduler_status_running_case_disabled_return_scheduler_status_disabled_case_error_return_scheduler_status_error_default_return_create_a_new_task_startcreatetask_this_iscreating_true_this_isediting_false_document_queryselector_x_data_schedulersettings_setattribute_data_editing_state_creating_this_editingtask_name_type_scheduled_default_to_scheduled_state_idle_initialize_with_idle_state_schedule_minute_hour_day_month_weekday_timezone_getusertimezone_token_this_generaterandomtoken_generate_token_even_for_scheduled_tasks_to_prevent_undefined_errors_plan_initialize_plan_for_all_task_types_to_prevent_undefined_errors_todo_in_progress_null_done_system_prompt_prompt_attachments_always_initialize_as_an_empty_array_set_up_flatpickr_after_the_component_is_visible_this_nexttick_this_initflatpickr_create_edit_an_existing_task_async_startedittask_taskid_const_task_this_tasks_find_t_t_uuid_taskid_if_task_showtoast_task_not_found_error_return_this_iscreating_false_this_isediting_true_document_queryselector_x_data_schedulersettings_setattribute_data_editing_state_editing_create_a_deep_copy_to_avoid_modifying_the_original_this_editingtask_json_parse_json_stringify_task_debug_log_console_log_task_data_for_editing_task_console_log_attachments_from_task_task_attachments_ensure_state_is_set_with_a_default_if_missing_if_this_editingtask_state_this_editingtask_state_idle_always_initialize_schedule_to_prevent_ui_errors_all_task_types_need_this_structure_for_the_form_to_work_properly_if_this_editingtask_schedule_typeof_this_editingtask_schedule_string_let_scheduleobj_minute_hour_day_month_weekday_timezone_getusertimezone_if_it_s_a_string_parse_it_if_typeof_this_editingtask_schedule_string_const_parts_this_editingtask_schedule_split_if_parts_length_5_scheduleobj_minute_parts_0_scheduleobj_hour_parts_1_scheduleobj_day_parts_2_scheduleobj_month_parts_3_scheduleobj_weekday_parts_4_this_editingtask_schedule_scheduleobj_else_ensure_timezone_exists_in_the_schedule_if_this_editingtask_schedule_timezone_this_editingtask_schedule_timezone_getusertimezone_ensure_attachments_is_always_an_array_if_this_editingtask_attachments_this_editingtask_attachments_else_if_typeof_this_editingtask_attachments_string_handle_case_where_attachments_might_be_stored_as_a_string_this_editingtask_attachments_this_editingtask_attachments_split_n_map_line_line_trim_filter_line_line_length_0_else_if_array_isarray_this_editingtask_attachments_if_not_an_array_or_string_set_to_empty_array_this_editingtask_attachments_ensure_appropriate_properties_are_initialized_based_on_task_type_if_this_editingtask_type_scheduled_initialize_token_for_scheduled_tasks_to_prevent_undefined_errors_if_ui_accesses_it_if_this_editingtask_token_this_editingtask_token_initialize_plan_stub_for_scheduled_tasks_to_prevent_undefined_errors_if_this_editingtask_plan_this_editingtask_plan_todo_in_progress_null_done_else_if_this_editingtask_type_adhoc_initialize_token_if_it_doesn_t_exist_if_this_editingtask_token_this_editingtask_token_this_generaterandomtoken_console_log_generated_new_token_for_adhoc_task_this_editingtask_token_console_log_setting_token_for_adhoc_task_this_editingtask_token_initialize_plan_stub_for_adhoc_tasks_to_prevent_undefined_errors_if_this_editingtask_plan_this_editingtask_plan_todo_in_progress_null_done_else_if_this_editingtask_type_planned_initialize_plan_if_it_doesn_t_exist_if_this_editingtask_plan_this_editingtask_plan_todo_in_progress_null_done_ensure_todo_is_an_array_if_array_isarray_this_editingtask_plan_todo_this_editingtask_plan_todo_initialize_token_to_prevent_undefined_errors_if_this_editingtask_token_this_editingtask_token_set_up_flatpickr_after_the_component_is_visible_and_task_data_is_loaded_this_nexttick_this_initflatpickr_edit_cancel_editing_canceledit_clean_up_flatpickr_instances_const_destroyflatpickr_inputid_const_input_document_getelementbyid_inputid_if_input_input_flatpickr_console_log_destroying_flatpickr_instance_for_inputid_input_flatpickr_destroy_also_remove_any_wrapper_elements_that_might_have_been_created_const_wrapper_input_closest_scheduler_flatpickr_wrapper_if_wrapper_wrapper_parentnode_move_the_input_back_to_its_original_position_wrapper_parentnode_insertbefore_input_wrapper_remove_the_wrapper_wrapper_parentnode_removechild_wrapper_remove_any_added_classes_input_classlist_remove_scheduler_flatpickr_input_if_this_iscreating_destroyflatpickr_newplannedtime_create_else_if_this_isediting_destroyflatpickr_newplannedtime_edit_reset_to_initial_state_but_keep_default_values_to_prevent_errors_this_editingtask_name_type_scheduled_state_idle_initialize_with_idle_state_schedule_minute_hour_day_month_weekday_timezone_getusertimezone_token_plan_initialize_plan_for_planned_tasks_todo_in_progress_null_done_system_prompt_prompt_attachments_always_initialize_as_an_empty_array_this_iscreating_false_this_isediting_false_document_queryselector_x_data_schedulersettings_removeattribute_data_editing_state_save_task_create_new_or_update_existing_async_savetask_validate_task_data_if_this_editingtask_name_trim_this_editingtask_prompt_trim_showtoast_task_name_and_prompt_are_required_error_alert_task_name_and_prompt_are_required_return_try_let_apiendpoint_taskdata_prepare_task_data_taskdata_name_this_editingtask_name_system_prompt_this_editingtask_system_prompt_prompt_this_editingtask_prompt_state_this_editingtask_state_idle_include_state_in_task_data_timezone_getusertimezone_process_attachments_now_always_stored_as_array_taskdata_attachments_array_isarray_this_editingtask_attachments_this_editingtask_attachments_map_line_typeof_line_string_line_trim_line_filter_line_line_line_trim_length_0_handle_task_type_specific_data_if_this_editingtask_type_scheduled_ensure_schedule_is_properly_formatted_as_an_object_if_typeof_this_editingtask_schedule_string_parse_string_schedule_into_object_const_parts_this_editingtask_schedule_split_taskdata_schedule_minute_parts_0_hour_parts_1_day_parts_2_month_parts_3_weekday_parts_4_timezone_getusertimezone_add_timezone_to_schedule_object_else_use_object_schedule_directly_but_ensure_timezone_is_included_taskdata_schedule_this_editingtask_schedule_timezone_this_editingtask_schedule_timezone_getusertimezone_don_t_send_token_or_plan_for_scheduled_tasks_delete_taskdata_token_delete_taskdata_plan_else_if_this_editingtask_type_adhoc_ad_hoc_task_with_token_ensure_token_is_a_non_empty_string_generate_a_new_one_if_needed_if_this_editingtask_token_this_editingtask_token_this_generaterandomtoken_console_log_generated_new_token_for_adhoc_task_this_editingtask_token_console_log_setting_token_in_taskdata_this_editingtask_token_taskdata_token_this_editingtask_token_don_t_send_schedule_or_plan_for_adhoc_tasks_delete_taskdata_schedule_delete_taskdata_plan_else_if_this_editingtask_type_planned_planned_task_with_plan_make_sure_plan_exists_and_has_required_properties_if_this_editingtask_plan_this_editingtask_plan_todo_in_progress_null_done_ensure_todo_and_done_are_arrays_if_array_isarray_this_editingtask_plan_todo_this_editingtask_plan_todo_if_array_isarray_this_editingtask_plan_done_this_editingtask_plan_done_validate_each_date_in_the_todo_list_to_ensure_it_s_a_valid_iso_string_const_validatedtodo_for_const_datestr_of_this_editingtask_plan_todo_try_const_date_new_date_datestr_if_isnan_date_gettime_validatedtodo_push_date_toisostring_else_console_warn_skipping_invalid_date_in_todo_list_datestr_catch_error_console_warn_error_processing_date_error_message_replace_with_validated_list_this_editingtask_plan_todo_validatedtodo_sort_the_todo_items_by_date_earliest_first_this_editingtask_plan_todo_sort_set_the_plan_in_taskdata_taskdata_plan_todo_this_editingtask_plan_todo_in_progress_this_editingtask_plan_in_progress_done_this_editingtask_plan_done_log_the_plan_data_for_debugging_console_log_planned_task_plan_data_json_stringify_taskdata_plan_null_2_don_t_send_schedule_or_token_for_planned_tasks_delete_taskdata_schedule_delete_taskdata_token_determine_if_creating_or_updating_if_this_iscreating_apiendpoint_scheduler_task_create_else_apiendpoint_scheduler_task_update_taskdata_task_id_this_editingtask_uuid_debug_log_the_final_task_data_being_sent_console_log_final_task_data_being_sent_to_api_json_stringify_taskdata_null_2_make_api_request_const_response_await_fetchapi_apiendpoint_method_post_headers_content_type_application_json_body_json_stringify_taskdata_if_response_ok_const_errordata_await_response_json_throw_new_error_errordata_error_failed_to_save_task_parse_response_data_to_get_the_created_updated_task_const_responsedata_await_response_json_show_success_message_showtoast_this_iscreating_task_created_successfully_task_updated_successfully_success_immediately_update_the_ui_if_the_response_includes_the_task_if_responsedata_responsedata_task_console_log_task_received_in_response_responsedata_task_update_the_tasks_array_if_this_iscreating_for_new_tasks_add_to_the_array_this_tasks_this_tasks_responsedata_task_else_for_updated_tasks_replace_the_existing_one_this_tasks_this_tasks_map_t_t_uuid_responsedata_task_uuid_responsedata_task_t_update_ui_using_the_shared_function_this_updatetasksui_else_fallback_to_fetching_tasks_if_no_task_in_response_await_this_fetchtasks_clean_up_flatpickr_instances_const_destroyflatpickr_inputid_const_input_document_getelementbyid_inputid_if_input_input_flatpickr_input_flatpickr_destroy_if_this_iscreating_destroyflatpickr_newplannedtime_create_else_if_this_isediting_destroyflatpickr_newplannedtime_edit_reset_task_data_and_form_state_this_editingtask_name_type_scheduled_state_idle_schedule_minute_hour_day_month_weekday_timezone_getusertimezone_token_plan_todo_in_progress_null_done_system_prompt_prompt_attachments_this_iscreating_false_this_isediting_false_document_queryselector_x_data_schedulersettings_removeattribute_data_editing_state_catch_error_console_error_error_saving_task_error_showtoast_failed_to_save_task_error_message_error_run_a_task_async_runtask_taskid_try_const_response_await_fetchapi_scheduler_task_run_method_post_headers_content_type_application_json_body_json_stringify_task_id_taskid_timezone_getusertimezone_if_response_ok_const_errordata_await_response_json_throw_new_error_errordata_error_failed_to_run_task_showtoast_task_started_successfully_success_refresh_task_list_this_fetchtasks_catch_error_console_error_error_running_task_error_showtoast_failed_to_run_task_error_message_error_reset_a_task_s_state_async_resettaskstate_taskid_try_const_task_this_tasks_find_t_t_uuid_taskid_if_task_showtoast_task_not_found_error_return_check_if_task_is_already_in_idle_state_if_task_state_idle_showtoast_task_is_already_in_idle_state_info_return_this_showloadingstate_true_call_api_to_update_the_task_state_const_response_await_fetchapi_scheduler_task_update_method_post_headers_content_type_application_json_body_json_stringify_task_id_taskid_state_idle_always_reset_to_idle_state_timezone_getusertimezone_if_response_ok_const_errordata_await_response_json_throw_new_error_errordata_error_failed_to_reset_task_state_showtoast_task_state_reset_to_idle_success_refresh_task_list_await_this_fetchtasks_this_showloadingstate_false_catch_error_console_error_error_resetting_task_state_error_showtoast_failed_to_reset_task_state_error_message_error_this_showloadingstate_false_delete_a_task_async_deletetask_taskid_confirm_deletion_if_confirm_are_you_sure_you_want_to_delete_this_task_this_action_cannot_be_undone_return_try_if_we_delete_selected_context_switch_to_another_first_switchfromcontext_taskid_const_response_await_fetchapi_scheduler_task_delete_method_post_headers_content_type_application_json_body_json_stringify_task_id_taskid_timezone_getusertimezone_if_response_ok_const_errordata_await_response_json_throw_new_error_errordata_error_failed_to_delete_task_showtoast_task_deleted_successfully_success_if_we_were_viewing_the_detail_of_the_deleted_task_close_the_detail_view_if_this_selectedtaskfordetail_this_selectedtaskfordetail_uuid_taskid_this_closetaskdetail_immediately_update_ui_without_waiting_for_polling_this_tasks_this_tasks_filter_t_t_uuid_taskid_update_ui_using_the_shared_function_this_updatetasksui_catch_error_console_error_error_deleting_task_error_showtoast_failed_to_delete_task_error_message_error_initialize_datetime_input_with_default_value_30_minutes_from_now_initdatetimeinput_event_if_event_target_value_const_now_new_date_now_setminutes_now_getminutes_30_format_as_yyyy_mm_ddthh_mm_const_year_now_getfullyear_const_month_string_now_getmonth_1_padstart_2_0_const_day_string_now_getdate_padstart_2_0_const_hours_string_now_gethours_padstart_2_0_const_minutes_string_now_getminutes_padstart_2_0_event_target_value_year_month_day_t_hours_minutes_if_using_flatpickr_update_it_as_well_if_event_target_flatpickr_event_target_flatpickr_setdate_event_target_value_generate_a_random_token_for_ad_hoc_tasks_generaterandomtoken_const_characters_abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz0123456789_let_token_for_let_i_0_i')s.length));
            }
            return token;
        },

        // Getter for filtered tasks
        get filteredTasks() {
            // Make sure we have tasks to filter
            if (!Array.isArray(this.tasks)) {
                console.warn('Tasks is not an array:', this.tasks);
                return [];
            }

            let filtered = [...this.tasks];

            // Apply type filter with case-insensitive comparison
            if (this.filterType && this.filterType !== 'all') {
                filtered = filtered.filter(task => {
                    if (!task.type) return false;
                    return String(task.type).toLowerCase() === this.filterType.toLowerCase();
                });
            }

            // Apply state filter with case-insensitive comparison
            if (this.filterState && this.filterState !== 'all') {
                filtered = filtered.filter(task => {
                    if (!task.state) return false;
                    return String(task.state).toLowerCase() === this.filterState.toLowerCase();
                });
            }

            // Sort the filtered tasks
            return this.sortTasks(filtered);
        },

        // Sort the tasks based on sort field and direction
        sortTasks(tasks) {
            if (!Array.isArray(tasks) || tasks.length === 0) {
                return tasks;
            }

            return [...tasks].sort((a, b) => {
                if (!this.sortField) return 0;

                const fieldA = a[this.sortField];
                const fieldB = b[this.sortField];

                // Handle cases where fields might be undefined
                if (fieldA === undefined && fieldB === undefined) return 0;
                if (fieldA === undefined) return 1;
                if (fieldB === undefined) return -1;

                // For dates, convert to timestamps
                if (this.sortField === 'createdAt' || this.sortField === 'updatedAt') {
                    const dateA = new Date(fieldA).getTime();
                    const dateB = new Date(fieldB).getTime();
                    return this.sortDirection === 'asc' ? dateA - dateB : dateB - dateA;
                }

                // For string comparisons
                if (typeof fieldA === 'string' && typeof fieldB === 'string') {
                    return this.sortDirection === 'asc'
                        ? fieldA.localeCompare(fieldB)
                        : fieldB.localeCompare(fieldA);
                }

                // For numerical comparisons
                return this.sortDirection === 'asc' ? fieldA - fieldB : fieldB - fieldA;
            });
        },

        // Computed property for attachments text representation
        get attachmentsText() {
            // Ensure we always have an array to work with
            const attachments = Array.isArray(this.editingTask.attachments)
                ? this.editingTask.attachments
                : [];

            // Join array items with newlines
            return attachments.join('\n');
        },

        // Setter for attachments text - preserves empty lines during editing
        set attachmentsText(value) {
            if (typeof value === 'string') {
                // Just split by newlines without filtering to preserve editing experience
                this.editingTask.attachments = value.split('\n');
            } else {
                // Fallback to empty array if not a string
                this.editingTask.attachments = [];
            }
        },

        // Debug method to test filtering logic
        testFiltering() {
            console.group('SchedulerSettings Debug: Filter Test');
            console.log('Current Filter Settings:');
            console.log('- Filter Type:', this.filterType);
            console.log('- Filter State:', this.filterState);
            console.log('- Sort Field:', this.sortField);
            console.log('- Sort Direction:', this.sortDirection);

            // Check if tasks is an array
            if (!Array.isArray(this.tasks)) {
                console.error('ERROR: this.tasks is not an array!', this.tasks);
                console.groupEnd();
                return;
            }

            console.log(`Raw Tasks (${this.tasks.length}):`, this.tasks);

            // Test filtering by type
            console.group('Filter by Type Test');
            ['all', 'adhoc', 'scheduled', 'recurring'].forEach(type => {
                const filtered = this.tasks.filter(task =>
                    type === 'all' ||
                    (task.type && String(task.type).toLowerCase() === type)
                );
                console.log(`Type "i18n.t('ui_i18n_t_ui_type')": ${filtered.length} tasks`, filtered);
            });
            console.groupEnd();

            // Test filtering by state
            console.group('Filter by State Test');
            ['all', 'idle', 'running', 'completed', 'failed'].forEach(state => {
                const filtered = this.tasks.filter(task =>
                    state === 'all' ||
                    (task.state && String(task.state).toLowerCase() === state)
                );
                console.log(`State "i18n.t('ui_i18n_t_ui_state')": ${filtered.length} tasks`, filtered);
            });
            console.groupEnd();

            // Show current filtered tasks
            console.log('Current Filtered Tasks:', this.filteredTasks);

            console.groupEnd();
        },

        // New comprehensive debug method
        debugTasks() {
            console.group('SchedulerSettings Comprehensive Debug');

            // Component state
            console.log('Component State:');
            console.log({
                filterType: this.filterType,
                filterState: this.filterState,
                sortField: this.sortField,
                sortDirection: this.sortDirection,
                isLoading: this.isLoading,
                isEditing: this.isEditing,
                isCreating: this.isCreating,
                viewMode: this.viewMode
            });

            // Tasks validation
            if (!this.tasks) {
                console.error('ERROR: this.tasks is undefined or null!');
                console.groupEnd();
                return;
            }

            if (!Array.isArray(this.tasks)) {
                console.error('ERROR: this.tasks is not an array!', typeof this.tasks, this.tasks);
                console.groupEnd();
                return;
            }

            // Raw tasks
            console.group('Raw Tasks');
            console.log(`Count: ${this.tasks.length}`);
            if (this.tasks.length > 0) {
                console.table(this.tasks.map(t => ({
                    uuid: t.uuid,
                    name: t.name,
                    type: t.type,
                    state: t.state
                })));

                // Inspect first task in detail
                console.log('First Task Structure:', JSON.stringify(this.tasks[0], null, 2));
            } else {
                console.log('No tasks available');
            }
            console.groupEnd();

            // Filtered tasks
            console.group('Filtered Tasks');
            const filteredTasks = this.filteredTasks;
            console.log(`Count: ${filteredTasks.length}`);
            if (filteredTasks.length > 0) {
                console.table(filteredTasks.map(t => ({
                    uuid: t.uuid,
                    name: t.name,
                    type: t.type,
                    state: t.state
                })));
            } else {
                console.log('No filtered tasks');
            }
            console.groupEnd();

            // Check for potential issues
            console.group('Potential Issues');

            // Check for case mismatches
            if (this.tasks.length > 0 && filteredTasks.length === 0) {
                console.warn('Filter seems to exclude all tasks. Checking why:');

                // Check type values
                const uniqueTypes = [...new Set(this.tasks.map(t => t.type))];
                console.log('Unique task types in data:', uniqueTypes);

                // Check state values
                const uniqueStates = [...new Set(this.tasks.map(t => t.state))];
                console.log('Unique task states in data:', uniqueStates);

                // Check for exact mismatches
                if (this.filterType !== 'all') {
                    const typeMatch = this.tasks.some(t =>
                        t.type && String(t.type).toLowerCase() === this.filterType.toLowerCase()
                    );
                    console.log(`Type "i18n.t('ui_i18n_t_ui_this_filtertype')" matches found:`, typeMatch);
                }

                if (this.filterState !== 'all') {
                    const stateMatch = this.tasks.some(t =>
                        t.state && String(t.state).toLowerCase() === this.filterState.toLowerCase()
                    );
                    console.log(`State "i18n.t('ui_i18n_t_ui_this_filterstate')" matches found:`, stateMatch);
                }
            }

            // Check for undefined or null values
            const hasUndefinedType = this.tasks.some(t => t.type === undefined || t.type === null);
            const hasUndefinedState = this.tasks.some(t => t.state === undefined || t.state === null);

            if (hasUndefinedType) {
                console.warn('Some tasks have undefined or null type values!');
            }

            if (hasUndefinedState) {
                console.warn('Some tasks have undefined or null state values!');
            }

            console.groupEnd();

            console.groupEnd();
        },

        // Initialize Flatpickr datetime pickers for both create and edit forms
        /**
         * Initialize Flatpickr date/time pickers for scheduler forms
         *
         * @param {string} mode - Which pickers to initialize: 'all', 'create', or 'edit'
         * @returns {void}
         */
        initFlatpickr(mode = 'all') {
            const initPicker = (inputId, refName, wrapperClass, options = {}) => {
                // Try to get input using Alpine.js x-ref first (more reliable)
                let input = this.$refs[refName];

                // Fall back to getElementById if x-ref is not available
                if (!input) {
                    input = document.getElementById(inputId);
                    console.log(`Using getElementById fallback for ${inputId}`);
                }

                if (!input) {
                    console.warn(`Input element ${inputId} not found by ID or ref`);
                    return null;
                }

                // Create a wrapper around the input
                const wrapper = document.createElement('div');
                wrapper.className = wrapperClass || 'scheduler-flatpickr-wrapper';
                wrapper.style.overflow = 'visible'; // Ensure dropdown can escape container

                // Replace the input with our wrapped version
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);
                input.classList.add('scheduler-flatpickr-input');

                // Default options
                const defaultOptions = {
                    dateFormat: "i18n.t('ui_i18n_t_ui_y_m_d_h_i')",
                    enableTime: true,
                    time_24hr: true,
                    static: false, // Not static so it will float
                    appendTo: document.body, // Append to body to avoid overflow issues
                    theme: "i18n.t('ui_i18n_t_ui_scheduler_theme')",
                    allowInput: true,
                    positionElement: wrapper, // Position relative to wrapper
                    onOpen: function(selectedDates, dateStr, instance) {
                        // Ensure calendar is properly positioned and visible
                        instance.calendarContainer.style.zIndex = '9999';
                        instance.calendarContainer.style.position = 'absolute';
                        instance.calendarContainer.style.visibility = 'visible';
                        instance.calendarContainer.style.opacity = '1';

                        // Add class to calendar container for our custom styling
                        instance.calendarContainer.classList.add('scheduler-theme');
                    },
                    // Set default date to 30 minutes from now if no date selected
                    onReady: function(selectedDates, dateStr, instance) {
                        if (!dateStr) {
                            const now = new Date();
                            now.setMinutes(now.getMinutes() + 30);
                            instance.setDate(now, true);
                        }
                    }
                };

                // Merge options
                const mergedOptions = {...defaultOptions, ...options};

                // Initialize flatpickr
                const fp = flatpickr(input, mergedOptions);

                // Add a clear button
                const clearButton = document.createElement('button');
                clearButton.className = 'scheduler-flatpickr-clear';
                clearButton.innerHTML = '×';
                clearButton.type = 'button';
                clearButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (fp) {
                        fp.clear();
                    }
                });
                wrapper.appendChild(clearButton);

                return fp;
            };

            // Clear any existing Flatpickr instances to prevent duplication
            if (mode === 'all' || mode === 'create') {
                const createInput = document.getElementById('newPlannedTime-create');
                if (createInput && createInput._flatpickr) {
                    createInput._flatpickr.destroy();
                }
            }

            if (mode === 'all' || mode === 'edit') {
                const editInput = document.getElementById('newPlannedTime-edit');
                if (editInput && editInput._flatpickr) {
                    editInput._flatpickr.destroy();
                }
            }

            // Initialize new instances
            if (mode === 'all' || mode === 'create') {
                initPicker('newPlannedTime-create', 'plannedTimeCreate', 'scheduler-flatpickr-wrapper', {
                    minuteIncrement: 5,
                    defaultHour: new Date().getHours(),
                    defaultMinute: Math.ceil(new Date().getMinutes() / 5) * 5
                });
            }

            if (mode === 'all' || mode === 'edit') {
                initPicker('newPlannedTime-edit', 'plannedTimeEdit', 'scheduler-flatpickr-wrapper', {
                    minuteIncrement: 5,
                    defaultHour: new Date().getHours(),
                    defaultMinute: Math.ceil(new Date().getMinutes() / 5) * 5
                });
            }
        },

        // Update tasks UI
        updateTasksUI() {
            // First update filteredTasks if that method exists
            if (typeof this.updateFilteredTasks === 'function') {
                this.updateFilteredTasks();
            }

            // Wait for UI to update
            this.$nextTick(() => {
                // Get empty state and task list elements
                const emptyElement = document.querySelector('.scheduler-empty');
                const tableElement = document.querySelector('.scheduler-task-list');

                // Calculate visibility state based on filtered tasks
                const hasFilteredTasks = Array.isArray(this.filteredTasks) && this.filteredTasks.length > 0;

                // Update visibility directly
                if (emptyElement) {
                    emptyElement.style.display = !hasFilteredTasks ? '' : 'none';
                }

                if (tableElement) {
                    tableElement.style.display = hasFilteredTasks ? '' : 'none';
                }
            });
        }
    };
};


// Only define the component if it doesn't already exist or extend the existing one
if (!window.schedulerSettings) {
    console.log('Defining schedulerSettings component from scratch');
    window.schedulerSettings = fullComponentImplementation;
} else {
    console.log('Extending existing schedulerSettings component');
    // Store the original function
    const originalSchedulerSettings = window.schedulerSettings;

    // Replace with enhanced version that merges the pre-initialized stub with the full implementation
    window.schedulerSettings = function() {
        // Get the base pre-initialized component
        const baseComponent = originalSchedulerSettings();

        // Create a backup of the original init function
        const originalInit = baseComponent.init || function() {};

        // Create our enhanced init function that adds the missing functionality
        baseComponent.init = function() {
            // Call the original init if it exists
            originalInit.call(this);

            console.log('Enhanced init running: adding missing methods to component');

            // Get the full implementation
            const fullImpl = fullComponentImplementation();

            // Add essential methods directly
            const essentialMethods = [
                'fetchTasks',
                'startCreateTask', 'startEditTask', 'cancelEdit',
                'saveTask', 'runTask', 'resetTaskState', 'deleteTask',
                'toggleTaskExpand', 'showTaskDetail', 'closeTaskDetail',
                'changeSort', 'formatDate', 'formatPlan', 'formatSchedule',
                'getStateBadgeClass', 'generateRandomToken', 'testFiltering',
                'debugTasks', 'sortTasks', 'initFlatpickr', 'initDateTimeInput',
                'updateTasksUI'
            ];

            essentialMethods.forEach(method => {
                if (typeof this[method] !== 'function' && typeof fullImpl[method] === 'function') {
                    console.log(`Adding missing method: ${method}`);
                    this[method] = fullImpl[method];
                }
            });

            // hack to expose deleteTask
            window.deleteTaskGlobal = this.deleteTask.bind(this);

            // Make sure we have a filteredTasks array initialized
            this.filteredTasks = [];

            // Initialize essential properties if missing
            if (!Array.isArray(this.tasks)) {
                this.tasks = [];
            }

            // Make sure attachmentsText getter/setter are defined
            if (!Object.getOwnPropertyDescriptor(this, 'attachmentsText')?.get) {
                Object.defineProperty(this, 'attachmentsText', {
                    get: function() {
                        // Ensure we always have an array to work with
                        const attachments = Array.isArray(this.editingTask?.attachments)
                            ? this.editingTask.attachments
                            : [];

                        // Join array items with newlines
                        return attachments.join('\n');
                    },
                    set: function(value) {
                        if (!this.editingTask) {
                            this.editingTask = { attachments: [] };
                        }

                        if (typeof value === 'string') {
                            // Just split by newlines without filtering to preserve editing experience
                            this.editingTask.attachments = value.split('\n');
                        } else {
                            // Fallback to empty array if not a string
                            this.editingTask.attachments = [];
                        }
                    }
                });
            }

            // Add methods for updating filteredTasks directly
            if (typeof this.updateFilteredTasks !== 'function') {
                this.updateFilteredTasks = function() {
                    // Make sure we have tasks to filter
                    if (!Array.isArray(this.tasks)) {
                        this.filteredTasks = [];
                        return;
                    }

                    let filtered = [...this.tasks];

                    // Apply type filter with case-insensitive comparison
                    if (this.filterType && this.filterType !== 'all') {
                        filtered = filtered.filter(task => {
                            if (!task.type) return false;
                            return String(task.type).toLowerCase() === this.filterType.toLowerCase();
                        });
                    }

                    // Apply state filter with case-insensitive comparison
                    if (this.filterState && this.filterState !== 'all') {
                        filtered = filtered.filter(task => {
                            if (!task.state) return false;
                            return String(task.state).toLowerCase() === this.filterState.toLowerCase();
                        });
                    }

                    // Sort the filtered tasks
                    if (typeof this.sortTasks === 'function') {
                        filtered = this.sortTasks(filtered);
                    }

                    // Directly update the filteredTasks property
                    this.filteredTasks = filtered;
                };
            }

            // Set up watchers to update filtered tasks when dependencies change
            this.$nextTick(() => {
                // Update filtered tasks when raw tasks change
                this.$watch('tasks', () => {
                    this.updateFilteredTasks();
                });

                // Update filtered tasks when filter type changes
                this.$watch('filterType', () => {
                    this.updateFilteredTasks();
                });

                // Update filtered tasks when filter state changes
                this.$watch('filterState', () => {
                    this.updateFilteredTasks();
                });

                // Update filtered tasks when sort field or direction changes
                this.$watch('sortField', () => {
                    this.updateFilteredTasks();
                });

                this.$watch('sortDirection', () => {
                    this.updateFilteredTasks();
                });

                // Initial update
                this.updateFilteredTasks();

                // Set up watcher for task type changes to initialize Flatpickr for planned tasks
                this.$watch('editingTask.type', (newType) => {
                    if (newType === 'planned') {
                        this.$nextTick(() => {
                            // Reinitialize Flatpickr when switching to planned task type
                            if (this.isCreating) {
                                this.initFlatpickr('create');
                            } else if (this.isEditing) {
                                this.initFlatpickr('edit');
                            }
                        });
                    }
                });

                // Initialize Flatpickr
                this.$nextTick(() => {
                    if (typeof this.initFlatpickr === 'function') {
                        this.initFlatpickr();
                    } else {
                        console.error('initFlatpickr is not available');
                    }
                });
            });

            // Try fetching tasks after a short delay
            setTimeout(() => {
                if (typeof this.fetchTasks === 'function') {
                    this.fetchTasks();
                } else {
                    console.error('fetchTasks still not available after enhancement');
                }
            }, 100);

            console.log('Enhanced init complete');
        };

        return baseComponent;
    };
}

// Force Alpine.js to register the component immediately
if (window.Alpine) {
    // Alpine is already loaded, register now
    console.log('Alpine already loaded, registering schedulerSettings component now');
    window.Alpine.data('schedulerSettings', window.schedulerSettings);
} else {
    // Wait for Alpine to load
    document.addEventListener('alpine:init', () => {
        console.log('Alpine:init - immediately registering schedulerSettings component');
        Alpine.data('schedulerSettings', window.schedulerSettings);
    });
}

// Add a document ready event handler to ensure the scheduler tab can be clicked on first load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded - setting up scheduler tab click handler');
    // Setup scheduler tab click handling
    const setupSchedulerTab = () => {
        const settingsModal = document.getElementById('settingsModal');
        if (!settingsModal) {
            setTimeout(setupSchedulerTab, 100);
            return;
        }

        // Create a global event listener for clicks on the scheduler tab
        document.addEventListener('click', function(e) {
            // Find if the click was on the scheduler tab or its children
            const schedulerTab = e.target.closest('.settings-tab[title="i18n.t('ui_i18n_t_ui_task_scheduler')"]');
            if (!schedulerTab) return;

            e.preventDefault();
            e.stopPropagation();

            // Get the settings modal data
            try {
                const modalData = Alpine.$data(settingsModal);
                if (modalData.activeTab !== 'scheduler') {
                    // Directly call the modal's switchTab method
                    modalData.switchTab('scheduler');
                }

                // Force start polling and fetch tasks immediately when tab is selected
                setTimeout(() => {
                    // Get the scheduler component data
                    const schedulerElement = document.querySelector('[x-data="i18n.t('ui_i18n_t_ui_schedulersettings')"]');
                    if (schedulerElement) {
                        const schedulerData = Alpine.$data(schedulerElement);

                        // Force fetch tasks and start polling
                        if (typeof schedulerData.fetchTasks === 'function') {
                            schedulerData.fetchTasks();
                        } else {
                            console.error('fetchTasks is not a function on scheduler component');
                        }
                    } else {
                        console.error('Could not find scheduler component element');
                    }
                }, 100);
            } catch (err) {
                console.error('Error handling scheduler tab click:', err);
            }
        }, true); // Use capture phase to intercept before Alpine.js handlers
    };

    // Initialize the tab handling
    setupSchedulerTab();
});
