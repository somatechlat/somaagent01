/**
 * Call a JSON-in JSON-out API endpoint
 * Data is automatically serialized
 * @param {string} endpoint - The API endpoint to call
 * @param {any} data - The data to send to the API
 * @returns {Promise<any>} The JSON response from the API
 */
export async function callJsonApi(endpoint, data) {
  const response = await fetchApi(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }
  const jsonResponse = await response.json();
  return jsonResponse;
}

/**
 * Fetch wrapper for A0 APIs
 * No CSRF token flow; uses same-origin credentials only.
 * @param {string} url - The URL to fetch
 * @param {Object} [request] - The fetch request options
 * @returns {Promise<Response>} The fetch response
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
    // Tenant precedence: explicit header > localStorage override > default.
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
    if (response.redirected && response.url.endsWith("/login")) {
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
