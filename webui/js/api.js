/**
 * Call a JSON-in JSON-out API endpoint
 * Data is automatically serialized
 * @param {string} endpoint - The API endpoint to call
 * @param {any} data - The data to send to the API
 * @returns {Promise<any>} The JSON response from the API
 */
export async function callJi18n.t('ui_the_jsoi18n.t('ui_the_json_response_from_the_api_export_async_function_calljsonapi_endpoint_data_const_response_await_fetchapi_endpoint_method_post_headers_content_type_application_json_credentials_same_origin_body_json_stringify_data_if_response_ok_const_error_await_response_text_throw_new_error_error_const_jsonresponse_await_response_json_return_jsonresponse_fetch_wrapper_for_a0_apis_no_csrf_token_flow_uses_same_origin_credentials_only_param_string_url_the_url_to_fetch_param_object_request_the_fetch_request_options_returns_promise')h response
 */
export async function fetchApi(url, request) {
  async function _wrap(retry) {
    // create a new request object if none was provided
    const finalRequest = request || {};

    // ensure headers object exists
    finalRequest.headers = finalRequest.headers || {};

    // --- Dev‑Prod Parity Auth/Policy Headers Injection ---
    // For production‑like local mode we must always supply identity hints so selective
    // policy evaluation (scheduler.task.* etc.) can succeed. When full JWT auth is
    // disabled (REQUIRE_AUTH=false) the gateway does not attach tenant/persona metadata
    // automatically, leading to 403 (policy_denied) responses. We inject stable
    // headers here unless caller already provided them.
    // Tenant precedence: explicit header > localStorage override > env stub > default.
    try {
      if (!finalRequest.headers['X-Tenant-Ii18n.t('ui_x_tenant_id')alRequest.headers['x-tenant-ii18n.t('ui_x_tenant_id')    const storedTenant = (globalThis.localStorage && localStorage.getItem('tenant')) i18n.t('ui_tenant')
        i18n.t('ui_finalrequest_headers')Id'] = (storei18n.t('ui_storedtenant')trim();
i18n.t('ui_trim_if_finalrequest_headers')-Id'] && !finai18n.t('ui_finalrequest_headers')-id']) {
     i18n.t('ui_const_storedpersona_globalthis_localstorage_localstorage_getitem')) || '';
i18n.t('ui_')  i18n.t('ui_finalrequest_headers')-Id'] = (storei18n.t('ui_storedpersona')();
i18n.t('ui_trim_catch_e_best_effort_only_never_block_request_on_header_injection_failure_optional_bearer_token_support_for_dev_if_localstorage_has_gateway_jwt_and_no_authorization_header_cookie_is_httponly_so_cannot_be_read_attach_it_this_allows_exercising_protected_endpoints_with_a_minted_dev_token_without_weakening_security_assumptions_try_if_finalrequest_headers')tion'] && !finai18n.t('ui_finalrequest_headers')tion']) {
     i18n.t('ui_const_jwt_globalthis_localstorage_localstorage_getitem')wt');
       i18n.t('ui_if_ji18n.t('ui_bearer_jwt')with')    i18n.t('ui_finalrequest_headers')tion'] = `Bearei18n.t('ui_bearer_jwt_catch_e_ignore_perform_the_fetch_with_the_provided_request_const_response_await_fetch_url_finalrequest_if_redirect_to_login_handle_immediately_if_response_redirected_response_url_endswith_i18n_t')_ui_i18n_t_ui_login')")) {
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
