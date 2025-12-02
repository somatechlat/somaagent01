/**
 * Centralised configuration for UI‑side API endpoints.
 *
 * All URL paths used by the Web UI are defined here to satisfy the VIBE
 * Coding Rules – no hard‑coded strings scattered across the codebase.
 *
 * The UI is served from the same origin as the gateway, therefore the base
 * URL is a relative path (`/v1`).  If the backend ever changes the prefix, only
 * this file needs to be updated.
 */
export const API = {
  // Root prefix for all API routes.
  BASE: "/v1",

  // Resource‑specific suffixes (concatenated with BASE when used).
  NOTIFICATIONS: "/notifications",
  SESSION: "/session",
  SESSIONS: "/sessions",
  UPLOADS: "/uploads",
  SETTINGS: "/settings",
  // Endpoint to test LLM connection credentials (used by Settings modal).
  TEST_CONNECTION: "/test_connection",
  ATTACHMENTS: "/attachments",
  HEALTH: "/health",
  SOMABRAIN_HEALTH: "/somabrain/health",
  // UI settings endpoint (relative to BASE, not absolute).
  UI_SETTINGS: "/settings/sections",
};
