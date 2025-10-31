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
 * Fetch wrapper for A0 APIs that ensures URL base resolution.
 * No CSRF token dance; relies on same-origin credentials or header auth per environment.
 * @param {string} url - The URL to fetch
 * @param {Object} [request] - The fetch request options
 * @returns {Promise<Response>} The fetch response
 */
export async function fetchApi(url, request) {
  function resolveUrl(u) {
    try {
      // If absolute URL, return as-is
      if (/^https?:\/\//i.test(u)) return u;
      const cfg = (globalThis.__SA01_CONFIG__ || {});
      const apiBase = (cfg.api_base || "/v1").replace(/\/$/, "");
      if (typeof u === "string" && u.startsWith("/v1")) {
        // Replace leading /v1 with configured base (supports custom prefixes)
        return apiBase + u.slice(3);
      }
      return u;
    } catch (_) {
      return url;
    }
  }
  // Create a new request object if none was provided
  const finalRequest = { ...(request || {}) };
  // Ensure same-origin credentials for cookies/session when applicable
  if (typeof finalRequest.credentials === "undefined") {
    finalRequest.credentials = "same-origin";
  }
  // Perform the fetch
  const finalUrl = resolveUrl(url);
  const response = await fetch(finalUrl, finalRequest);
  // Handle auth redirects gracefully
  if (response && response.redirected && response.url.endsWith("/login")) {
    window.location.href = response.url;
    return response;
  }
  return response;
}
