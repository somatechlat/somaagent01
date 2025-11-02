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
    body: JSON.stringify(data ?? {}),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }
  const jsonResponse = await response.json();
  return jsonResponse;
}

/**
 * Minimal fetch wrapper for Gateway /v1 APIs (same-origin)
 * - Prefixes relative API paths with /v1
 * - Does not use CSRF; relies on same-origin cookies or bearer tokens
 * @param {string} url - The URL to fetch
 * @param {Object} [request] - The fetch request options
 * @returns {Promise<Response>} The fetch response
 */
export async function fetchApi(url, request) {
  const finalRequest = request ? { ...request } : {};
  finalRequest.headers = finalRequest.headers || {};

  // Resolve absolute URL or prefix with /v1
  let target = url || "";
  const isAbsolute = /^https?:\/\//i.test(target);
  const isV1 = target.startsWith("/v1/");
  if (!isAbsolute && !isV1) {
    if (!target.startsWith("/")) target = "/" + target;
    target = "/v1" + target;
  }

  return await fetch(target, finalRequest);
}

// No CSRF token logic; same-origin cookies or Authorization headers should be configured by the platform
