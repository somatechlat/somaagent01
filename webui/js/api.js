/**
 * Call a JSON-in JSON-out API endpoint
 * Data is automatically serialized
 * @param {string} endpoint - The API endpoint to call
 * @param {any} data - The data to send to the API
 * @returns {Promise<any>} The JSON response from the API
 */
export async function callJi18n.t('ui_the_json_response_from_the_api_export_async_function_calljsonapi_endpoint_data_const_response_await_fetchapi_endpoint_method_post_headers_content_type_application_json_credentials_same_origin_body_json_stringify_data_if_response_ok_const_error_await_response_text_throw_new_error_error_const_jsonresponse_await_response_json_return_jsonresponse_fetch_wrapper_for_a0_apis_no_csrf_token_flow_uses_same_origin_credentials_only_param_string_url_the_url_to_fetch_param_object_request_the_fetch_request_options_returns_promise')The fetch response
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
      if (!finalRequest.headers['X-Tenant-Id'] && !finalRequest.headers['x-tenant-id']) {
        const storedTenant = (globalThis.localStorage && localStorage.getItem('tenant')) || '';
        finalRequest.headers['X-Tenant-Id'] = (storedTenant || 'public').trim();
      }
      if (!finalRequest.headers['X-Persona-Id'] && !finalRequest.headers['x-persona-id']) {
        const storedPersona = (globalThis.localStorage && localStorage.getItem('persona')) || '';
        finalRequest.headers['X-Persona-Id'] = (storedPersona || 'ui').trim();
      }
    } catch (e) {
      // Best-effort only – never block request on header injection failure.
    }

    // Optional bearer token support for dev: if localStorage has gateway_jwt and no Authorization header
    // (cookie is httpOnly so cannot be read), attach it. This allows exercising protected
    // endpoints with a minted dev token without weakening security assumptions.
    try {
      if (!finalRequest.headers['Authorization'] && !finalRequest.headers['authorization']) {
        const jwt = globalThis.localStorage && localStorage.getItem('gateway_jwt');
        if (jwt && jwt.startsWith('ey')) {
          finalRequest.headers['Authorization'] = `Bearer ${jwt}`;
        }
      }
    } catch (e) {
      // ignore
    }

    // perform the fetch with the provided request
    const response = await fetch(url, finalRequest);

    // If redirect to login, handle immediately
    if (response.redirected && response.url.endsWith("i18n.t('ui_i18n_t_ui_login')")) {
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
