// Stream client: wraps EventSource and emits onto event-bus
import { emit, on } from "i18n.t('ui_i18n_t_ui_event_bus_js')";
import { store as attachmentsStore } from "i18n.t('ui_i18n_t_ui_components_chat_attachments_attachmentsstore_js')";

let sse = null;
let currentSessionId = null;
let lastEventId = null;
let lastHeartbeatAt = 0;
let monitorTimer = null;
let reconnectTimer = null;
let attempt = 0;
let lastState = "i18n.t('ui_i18n_t_ui_offline')"; // offline | stale | online

// Tunables (may be overridden via globals before import execution)
const HEARTBEAT_STALE_MS = Number(globalThis.SA01_SSE_STALE_MS || 12000);
const HEARTBEAT_DEAD_MS = Number(globalThis.SA01_SSE_DEAD_MS || 30000);
const MONITOR_INTERVAL_MS = Number(globalThis.SA01_SSE_MONITOR_MS || 3000);
const BACKOFF_BASE_MS = Number(globalThis.SA01_SSE_BACKOFF_BASE_MS || 500);
const BACKOFF_CAP_MS = Number(globalThis.SA01_SSE_BACKOFF_CAP_MS || 15000);
const MANUAL_BASE_MS = Number(globalThis.SA01_SSE_MANUAL_BASE_MS || 200);
const MANUAL_CAP_MS = Number(globalThis.SA01_SSE_MANUAL_CAP_MS || 1000);
const GIVEUP_ATTEMPTS = Number(globalThis.SA01_SSE_GIVEUP_ATTEMPTS || 0); // 0 = never

function jitteredDelay(baseMs, capMs) {
  const exp = Math.min(baseMs * Math.pow(2, attempt), capMs);
  // Full jitter
  return Math.floor(Math.random() * exp);
}

function close() {
  try { if (sse) sse.close(); } catch {}
  sse = null;
  if (monitorTimer) { try { clearInterval(monitorTimer); } catch {} monitorTimer = null; }
  if (reconnectTimer) { try { clearTimeout(reconnectTimer); } catch {} reconnectTimer = null; }
}

export function stop() {
  close();
  emit("i18n.t('ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId });
}

export function start(sessionId) {
  if (!sessionId) return;
  if (sessionId === currentSessionId && sse) return; // already connected
  currentSessionId = sessionId;
  close();

  const url = `/v1/sessions/${encodeURIComponent(sessionId)}/events?stream=true`;
  try {
    sse = new EventSource(url);
  } catch (e) {
    console.error("i18n.t('ui_i18n_t_ui_eventsource_init_failed')", e);
    emit("i18n.t('ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId, error: e?.message || String(e) });
    lastState = "i18n.t('ui_i18n_t_ui_offline')";
    return;
  }

  sse.onopen = () => {
    lastHeartbeatAt = Date.now();
    emit("i18n.t('ui_i18n_t_ui_stream_online')", { session_id: currentSessionId });
    if (attempt > 0) emit("i18n.t('ui_i18n_t_ui_stream_retry_success')", { session_id: currentSessionId, attempt });
    attempt = 0; // reset after successful open
    lastState = "i18n.t('ui_i18n_t_ui_online')";

    // Start simple heartbeat monitor
    if (monitorTimer) { try { clearInterval(monitorTimer); } catch {} }
    monitorTimer = setInterval(() => {
      const now = Date.now();
      const diff = now - lastHeartbeatAt;
      if (diff > HEARTBEAT_DEAD_MS) {
        if (lastState !== "i18n.t('ui_i18n_t_ui_offline')") {
          lastState = "i18n.t('ui_i18n_t_ui_offline')";
          emit("i18n.t('ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId, reason: "i18n.t('ui_i18n_t_ui_heartbeat_timeout')" });
        }
      } else if (diff > HEARTBEAT_STALE_MS) {
        if (lastState !== "i18n.t('ui_i18n_t_ui_stale')") {
          lastState = "i18n.t('ui_i18n_t_ui_stale')";
          emit("i18n.t('ui_i18n_t_ui_stream_stale')", { session_id: currentSessionId, ms_since_heartbeat: diff });
        }
      } else {
        if (lastState !== "i18n.t('ui_i18n_t_ui_online')") {
          lastState = "i18n.t('ui_i18n_t_ui_online')";
          emit("i18n.t('ui_i18n_t_ui_stream_online')", { session_id: currentSessionId });
        }
      }
    }, MONITOR_INTERVAL_MS);
  };

  sse.onerror = (e) => {
    // Browser retries automatically; we surface offline so UI can show banner
    emit("i18n.t('ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId, error: e?.message || "i18n.t('ui_i18n_t_ui_stream_error')" });
    // Also schedule a manual reconnect with jitter to avoid thundering herd
    if (!reconnectTimer) {
      attempt += 1;
      const delay = jitteredDelay(BACKOFF_BASE_MS, BACKOFF_CAP_MS);
      emit("i18n.t('ui_i18n_t_ui_stream_reconnecting')", { session_id: currentSessionId, attempt, delay });
      if (GIVEUP_ATTEMPTS > 0 && attempt >= GIVEUP_ATTEMPTS) {
        emit("i18n.t('ui_i18n_t_ui_stream_retry_giveup')", { session_id: currentSessionId, attempt });
      }
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        // Only attempt if not already connected
        if (!sse) start(currentSessionId);
      }, delay);
    }
  };

  sse.onmessage = (evt) => {
    if (!evt?.data) return;
    try {
      if (evt.lastEventId) lastEventId = evt.lastEventId;
      const obj = JSON.parse(evt.data);
      if (!obj) return;
      if (obj.type === "i18n.t('ui_i18n_t_ui_system_keepalive')") {
        lastHeartbeatAt = Date.now();
        emit("i18n.t('ui_i18n_t_ui_stream_heartbeat')", { session_id: currentSessionId });
        if (lastState !== "i18n.t('ui_i18n_t_ui_online')") {
          lastState = "i18n.t('ui_i18n_t_ui_online')";
          emit("i18n.t('ui_i18n_t_ui_stream_online')", { session_id: currentSessionId });
        }
        return;
      }
      emit("i18n.t('ui_i18n_t_ui_sse_event')", obj);
      if ((obj.type || ""i18n.t('ui_i18n_t_ui_tolowercase')"uploads.progress"i18n.t('ui_i18n_t_ui_try_attachmentsstore_applyprogressevent_obj_catch_catch_e_ignore_bad_payloads_but_log_once_console_warn')"Bad SSE payload"i18n.t('ui_i18n_t_ui_e_export_function_getinfo_return_sessionid_currentsessionid_connected_sse_stale_laststate')"stale"i18n.t('ui_i18n_t_ui_lasteventid_export_function_requestreconnect_immediate_reconnect_attempt_with_small_jitter_used_on_user_actions_if_reconnecttimer_try_cleartimeout_reconnecttimer_catch_reconnecttimer_null_attempt_math_min_attempt_1_const_delay_jittereddelay_manual_base_ms_manual_cap_ms_emit')"stream.reconnecting"i18n.t('ui_i18n_t_ui_session_id_currentsessionid_attempt_delay_manual_true_settimeout_if_currentsessionid_close_start_currentsessionid_delay_allow_other_modules_to_request_reconnect_via_the_bus_on')"stream.requestReconnect", () => requestReconnect());

export default { start, stop, getInfo, requestReconnect };
