/**
 * Call a JSON-in JSON-out API endpoint
 * Data is automatically serialized
 * @param {string} endpoint - The API endpoint to call
 * @param {any} data - The data to send to the API
 * @returns {Promise<any>} The JSON response from the API
 */
export async function callJi18n.t('i18n.t('ui_the_jsoi18n_t')'ui_the_json_response_from_the_api_export_async_function_calljsonapi_endpoint_data_const_response_await_fetchapi_endpoint_method_post_headers_content_type_application_json_credentials_same_origin_body_json_stringify_data_if_response_ok_const_error_await_response_text_throw_new_error_error_const_jsonresponse_await_response_json_return_jsonresponse_fetch_wrapper_for_a0_apis_no_csrf_token_flow_uses_same_origin_credentials_only_param_string_url_the_url_to_fetch_param_object_request_the_fetch_request_options_returns_promise'i18n.t('ui_h_response_export_async_function_fetchapi_url_request_async_function_wrap_retry_create_a_new_request_object_if_none_was_provided_const_finalrequest_request_ensure_headers_object_exists_finalrequest_headers_finalrequest_headers_dev_prod_parity_auth_policy_headers_injection_for_production_like_local_mode_we_must_always_supply_identity_hints_so_selective_policy_evaluation_scheduler_task_etc_can_succeed_when_full_jwt_auth_is_disabled_require_auth_false_the_gateway_does_not_attach_tenant_persona_metadata_automatically_leading_to_403_policy_denied_responses_we_inject_stable_headers_here_unless_caller_already_provided_them_tenant_precedence_explicit_header_localstorage_override_env_stub_default_try_if_finalrequest_headers')'X-Tenant-Ii18n.t('i18n.t('ui_x_tenant_id')')alRequest.headers['i18n.t('ui_x_tenant_ii18n_t')'ui_x_tenant_id'i18n.t('ui_const_storedtenant_globalthis_localstorage_localstorage_getitem')'tenant'i18n.t('ui_i18n_t')'ui_tenant'i18n.t('ui_i18n_t')'ui_finalrequest_headers'i18n.t('ui_id')'] = (storei18n.t('i18n.t('ui_storedtenant')')trim();
i18n.t('i18n.t('ui_trim_if_finalrequest_headers')')-Id'i18n.t('ui_finai18n_t')'ui_finalrequest_headers'i18n.t('ui_id')']) {
     i18n.t('i18n.t('ui_const_storedpersona_globalthis_localstorage_localstorage_getitem')')) || ''i18n.t('ui_i18n_t')'ui_'i18n.t('ui_i18n_t')'ui_finalrequest_headers'i18n.t('ui_id')'] = (storei18n.t('i18n.t('ui_storedpersona')')();
i18n.t('i18n.t('ui_trim_catch_e_best_effort_only_never_block_request_on_header_injection_failure_optional_bearer_token_support_for_dev_if_localstorage_has_gateway_jwt_and_no_authorization_header_cookie_is_httponly_so_cannot_be_read_attach_it_this_allows_exercising_protected_endpoints_with_a_minted_dev_token_without_weakening_security_assumptions_try_if_finalrequest_headers')')tion'i18n.t('ui_finai18n_t')'ui_finalrequest_headers'i18n.t('ui_tion')']) {
     i18n.t('i18n.t('ui_const_jwt_globalthis_localstorage_localstorage_getitem')')wt'i18n.t('ui_i18n_t')'ui_if_ji18n.t('i18n.t('ui_bearer_jwt')')with'i18n.t('ui_i18n_t')'ui_finalrequest_headers'i18n.t('ui_tion')'] = `Bearei18n.t('i18n.t('ui_bearer_jwt_catch_e_ignore_perform_the_fetch_with_the_provided_request_const_response_await_fetch_url_finalrequest_if_redirect_to_login_handle_immediately_if_response_redirected_response_url_endswith_i18n_t')')_ui_i18n_t_ui_login')")) {
      window.location.href = response.url;
      return;
    }

    // return the response
    return response;
  }

  // perform the request
  const response = await _wrap(false);  // single attempt only

  // return the response
  return response;
}
