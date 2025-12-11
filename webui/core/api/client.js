/**
 * API Client
 * 
 * Centralized HTTP client with authentication, error handling, and interceptors.
 * Follows VIBE Coding Rules - real implementations only, no mocks.
 * 
 * @module core/api/client
 */

import { API_VERSION } from './endpoints.js';

/**
 * Request interceptors - functions called before each request
 * @type {Array<Function>}
 */
const requestInterceptors = [];

/**
 * Response interceptors - functions called after each response
 * @type {Array<Function>}
 */
const responseInterceptors = [];

/**
 * Add a request interceptor
 * @param {Function} interceptor - Function(config) => config
 * @returns {Function} Unsubscribe function
 */
export function addRequestInterceptor(interceptor) {
  requestInterceptors.push(interceptor);
  return () => {
    const idx = requestInterceptors.indexOf(interceptor);
    if (idx > -1) requestInterceptors.splice(idx, 1);
  };
}

/**
 * Add a response interceptor
 * @param {Function} interceptor - Function(response, config) => response
 * @returns {Function} Unsubscribe function
 */
export function addResponseInterceptor(interceptor) {
  responseInterceptors.push(interceptor);
  return () => {
    const idx = responseInterceptors.indexOf(interceptor);
    if (idx > -1) responseInterceptors.splice(idx, 1);
  };
}

/**
 * Apply request interceptors
 * @param {Object} config - Request configuration
 * @returns {Object} Modified configuration
 */
async function applyRequestInterceptors(config) {
  let result = { ...config };
  for (const interceptor of requestInterceptors) {
    try {
      result = await interceptor(result);
    } catch (e) {
      console.error('Request interceptor error:', e);
    }
  }
  return result;
}

/**
 * Apply response interceptors
 * @param {Response} response - Fetch response
 * @param {Object} config - Original request configuration
 * @returns {Response} Modified response
 */
async function applyResponseInterceptors(response, config) {
  let result = response;
  for (const interceptor of responseInterceptors) {
    try {
      result = await interceptor(result, config);
    } catch (e) {
      console.error('Response interceptor error:', e);
    }
  }
  return result;
}

/**
 * Inject authentication headers
 * @param {Object} headers - Request headers
 * @returns {Object} Headers with auth
 */
function injectAuthHeaders(headers) {
  const result = { ...headers };
  
  // Tenant ID injection
  if (!result['X-Tenant-Id'] && !result['x-tenant-id']) {
    try {
      const storedTenant = globalThis.localStorage?.getItem('tenant') || '';
      result['X-Tenant-Id'] = (storedTenant || 'public').trim();
    } catch (e) {
      result['X-Tenant-Id'] = 'public';
    }
  }
  
  // Persona ID injection
  if (!result['X-Persona-Id'] && !result['x-persona-id']) {
    try {
      const storedPersona = globalThis.localStorage?.getItem('persona') || '';
      result['X-Persona-Id'] = (storedPersona || 'ui').trim();
    } catch (e) {
      result['X-Persona-Id'] = 'ui';
    }
  }
  
  // JWT token injection (dev mode)
  if (!result['Authorization'] && !result['authorization']) {
    try {
      const jwt = globalThis.localStorage?.getItem('gateway_jwt');
      if (jwt && jwt.startsWith('ey')) {
        result['Authorization'] = `Bearer ${jwt}`;
      }
    } catch (e) {
      // Ignore
    }
  }
  
  return result;
}

/**
 * Core fetch wrapper with authentication and error handling.
 *
 * Returns a data object augmented with Response-like metadata so both
 * legacy callers (expecting a Response with `.ok` / `.json()`) and
 * modern callers (expecting parsed JSON) keep working.
 *
 * @param {string} url - Request URL (will be prefixed with /v1 if not already)
 * @param {Object} [options] - Fetch options
 * @returns {Promise<Object>} Parsed data object with response metadata attached
 */
export async function fetchApi(url, options = {}) {
  // Prepend API version if not already present
  const fullUrl = url.startsWith('/v1') || url.startsWith('http') ? url : `${API_VERSION}${url}`;

  // Build initial config
  let config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...injectAuthHeaders(options.headers || {}),
    },
    credentials: options.credentials || 'same-origin',
  };

  // Apply request interceptors
  config = await applyRequestInterceptors(config);

  // Perform fetch
  let response = await fetch(fullUrl, config);

  // Handle login redirect
  if (response.redirected && response.url.endsWith('/login')) {
    window.location.href = response.url;
    throw new Error('Redirected to login');
  }

  // Apply response interceptors
  response = await applyResponseInterceptors(response, config);

  // Read body once from a clone so the original response remains untouched
  const cloned = response.clone();
  const rawText = await cloned.text();

  // Parse JSON if possible; fall back to raw text
  let parsed;
  try {
    parsed = rawText ? JSON.parse(rawText) : {};
  } catch (e) {
    parsed = { raw: rawText };
  }

  // Build a compatibility wrapper that behaves like parsed JSON but exposes
  // Response-like metadata for callers that previously expected a Response.
  const result = (parsed && typeof parsed === 'object') ? parsed : { value: parsed };

  Object.defineProperties(result, {
    ok: { value: response.ok, enumerable: false },
    status: { value: response.status, enumerable: false },
    statusText: { value: response.statusText, enumerable: false },
    headers: { value: response.headers, enumerable: false },
    url: { value: response.url, enumerable: false },
    raw: { value: rawText, enumerable: false },
    json: { value: async () => parsed, enumerable: false },
    text: { value: async () => rawText, enumerable: false },
    response: { value: response, enumerable: false },
  });

  // Surface HTTP errors with meaningful messages while preserving parsed body
  if (!response.ok) {
    const message = (parsed && parsed.error) || rawText || `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.data = parsed;
    throw error;
  }

  return result;
}

/**
 * JSON API call helper
 * @param {string} endpoint - API endpoint (relative to API_VERSION)
 * @param {Object} data - Request body data
 * @param {Object} [options] - Additional fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function callJsonApi(endpoint, data, options = {}) {
  const url = endpoint.startsWith('/v1') ? endpoint : `${API_VERSION}${endpoint}`;
  
  const response = await fetchApi(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    body: JSON.stringify(data),
    ...options,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * GET request helper
 * @param {string} endpoint - API endpoint
 * @param {Object} [options] - Fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function get(endpoint, options = {}) {
  const url = endpoint.startsWith('/v1') ? endpoint : `${API_VERSION}${endpoint}`;
  
  const response = await fetchApi(url, {
    method: 'GET',
    ...options,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * POST request helper
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body
 * @param {Object} [options] - Fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function post(endpoint, data, options = {}) {
  return callJsonApi(endpoint, data, options);
}

/**
 * PUT request helper
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body
 * @param {Object} [options] - Fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function put(endpoint, data, options = {}) {
  const url = endpoint.startsWith('/v1') ? endpoint : `${API_VERSION}${endpoint}`;
  
  const response = await fetchApi(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    body: JSON.stringify(data),
    ...options,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * DELETE request helper
 * @param {string} endpoint - API endpoint
 * @param {Object} [options] - Fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function del(endpoint, options = {}) {
  const url = endpoint.startsWith('/v1') ? endpoint : `${API_VERSION}${endpoint}`;
  
  const response = await fetchApi(url, {
    method: 'DELETE',
    ...options,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// Export for backward compatibility
export default { fetchApi, callJsonApi, get, post, put, del };
