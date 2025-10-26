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
 * Fetch wrapper for A0 APIs that ensures token exchange
 * Automatically adds CSRF token to request headers
 * @param {string} url - The URL to fetch
 * @param {Object} [request] - The fetch request options
 * @returns {Promise<Response>} The fetch response
 */
export async function fetchApi(url, request) {
  async function _wrap(retry) {
    // get the CSRF token
    const token = await getCsrfToken();

    // create a new request object if none was provided
    const finalRequest = request || {};

    // ensure headers object exists
    finalRequest.headers = finalRequest.headers || {};

    // add the CSRF token to the headers
    finalRequest.headers["X-CSRF-Token"] = token;

    // perform the fetch with the updated request
    const response = await fetch(url, finalRequest);

    // check if there was an CSRF error
    if (response.status === 403 && retry) {
      // retry the request with new token
      invalidateCsrfToken();
      return await _wrap(false);
    }else if(response.redirected && response.url.endsWith("/login")){
      // redirect to login
      window.location.href = response.url;
      return;
    }

    // return the response
    return response;
  }

  // perform the request
  const response = await _wrap(true);

  // return the response
  return response;
}

let csrfToken = null;
let csrfTokenPromise = null;

function invalidateCsrfToken() {
  csrfToken = null;
}

async function getCsrfToken() {
  if (csrfToken) return csrfToken;
  if (!csrfTokenPromise) {
    csrfTokenPromise = (async () => {
      const gw = await fetch("/v1/csrf", { credentials: "include" });
      if (!gw.ok) throw new Error("Failed to fetch CSRF token");
      const json = await gw.json();
      csrfToken = json.token || "";
      return csrfToken;
    })()
      .catch((error) => {
        csrfTokenPromise = null;
        throw error;
      })
      .finally(() => {
        csrfTokenPromise = null;
      });
  }
  return csrfTokenPromise;
}
