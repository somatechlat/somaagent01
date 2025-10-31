// Minimal runtime config loader for the Web UI
// - Fetches /ui/config.json if available
// - Exposes window.__SA01_CONFIG__ with safe defaults

(function initDefault() {
  if (!globalThis.__SA01_CONFIG__) {
    globalThis.__SA01_CONFIG__ = {
      api_base: "/v1",
      universe_default: undefined,
      namespace_default: "wm",
      features: { write_through: false, write_through_async: false, require_auth: false }
    };
  }
})();

export async function loadRuntimeConfig() {
  try {
    const resp = await fetch("/ui/config.json", { credentials: "same-origin" });
    if (!resp || !resp.ok) return globalThis.__SA01_CONFIG__;
    const cfg = await resp.json().catch(() => ({}));
    if (cfg && typeof cfg === "object") {
      globalThis.__SA01_CONFIG__ = Object.assign({}, globalThis.__SA01_CONFIG__ || {}, cfg);
    }
  } catch (_) {
    // keep defaults
  }
  return globalThis.__SA01_CONFIG__;
}

// Eagerly kick off the load but don't block page
try { loadRuntimeConfig(); } catch (_) {}
