/**
 * Centralised configuration for UI‑side API endpoints.
 *
 * All URL paths used by the Web UI are defined here to satisfy the VIBE
 * Coding Rules – no hard‑coded strings scattered across the codebase.
 *
 * The UI is served from the same origin as the gateway, therefore the base
 * URL is a relative path (`/v1`).  If the backend ever changes the prefix, only
 * this file needs to be updated.
 * 
 * NOTE: This file is maintained for backward compatibility.
 * New code should import from 'core/api/endpoints.js' instead.
 */

// Re-export from new canonical location
export { API } from './core/api/endpoints.js';

// Also export individual constants for direct imports
export { API_VERSION, ENDPOINTS, buildUrl } from './core/api/endpoints.js';
