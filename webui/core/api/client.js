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
 * Core fetch wrapper with authentication and error handling
 * @param {string} url - Request URL
 * @param {Object} [options] - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export async function fetchApi(url, options = {}) {
  // Build initial config
  let config = {
    ...options,
    headers: injectAuthHeaders(options.headers || {}),
    credentials: options.credentials || 'same-origin',
  };
  
  // Apply request interceptors
  config = await applyRequestInterceptors(config);
  
  // Perform fetch
  let response = await fetch(url, config);
  
  // Handle login redirect
  if (response.redirected && response.url.endsWith('/login')) {
    window.location.href = response.url;
    return response;
  }
  
  // Apply response interceptors
  response = await applyResponseInterceptors(response, config);
  
  return response;
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
