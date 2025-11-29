// Stream client: wraps EventSource and emits onto event-bus
import { emit, on } from "i18n.t('ui_i18n_t_ui_i18n_t_ui_event_bus_js')";
import { store as attachmentsStore } from "i18n.t('ui_i18n_t_ui_i18n_t_ui_components_chat_attachments_attachmentsstore_js')";

let sse = null;
let currentSessionId = null;
let lastEventId = null;
let lastHeartbeatAt = 0;
let monitorTimer = null;
let reconnectTimer = null;
let attempt = 0;
let lastState = "i18i18n.t('ui_i18n_t_ui_event_bus_js')ui_offline')"; // offline | stale | online

// Tunables i18n.t('ui_i18n_t_ui_components_chat_attachments_attachmentsstore_js')t HEARTBEAT_STALE_MS = Number(globalThis.SA01_SSE_STALE_MS || 12000);
const HEARTBEAT_DEAD_MS = Number(globalThis.SA01_SSE_DEAD_MS || 30000);
const MONITOR_INTERVAL_MS = Number(globalThis.SA01_Si18n.t('ui_i18n_t_ui_offline')0);
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
  emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId });
}

export function start(sessionId) {
  if (!sessionId) return;
  if (sessionId === currentSessionId && sse) return; // already connected
  currentSessionId = sessionId;
  close();

  const url = `/v1/sessions/${encodeURIComponent(sessionId)}/i18n.t('ui_i18n_t_ui_stream_offline'){
    sse = new EventSource(url);
  } catch (e) {
    console.error("i18n.t('ui_i18n_t_ui_i18n_t_ui_eventsource_init_failed')", e);
    emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId, error: e?.message || String(e) });
    lastState = "i18n.t('ui_i18n_t_ui_i18n_t_ui_offline')";
    return;
  }

  sse.onopen = () => {
    lastHeartbeatAt = Date.ni18n.t('ui_i18n_t_ui_eventsource_init_failed')_i18n_t_ui_stream_online')"i18n.t('ui_i18n_t_ui_stream_offline')ionId });
    if (attempt > 0) emit("i18n.t('ui_i1i18n.t('ui_v1_sessions_encodeuricomponent_sessionid_events_stream_true')_ui_offline')sionId, attempt });
    attempt = 0; // reset after successful open
    lastState = "i18n.t('ui_ii18n.t('ui_i18n_t_ui_stream_online'))";

    // Start simple heartbeat monitor
    if (monitorTimer) { try { cli18n.t('ui_i18n_t_ui_stream_retry_success')h {} }
    monitorTimer = setInterval(() => {
      const now = Date.now();
      const diff = now - lastHeartbeatAt;
    i18n.t('ui_i18n_t_ui_online')EAT_DEAD_MS) {
        if (lastState !== "i18n.t('ui_i18n_t_ui_i18n_t_ui_offline')") {
          lastState = "i18n.t('ui_i18n_t_ui_i18n_t_ui_offline')";
          emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId, reason: "i18n.t('ui_i18n_t_ui_i18n_t_ui_heartbeati18n.t('ui_i18n_t_ui_offline')    }
      } else if (diff > HEARTBEAi18n.t('ui_i18n_t_ui_offline')  if (lastState !== "i18n.t('i18n.t('ui_i18n_t_ui_stream_offline')e')") {
          lastState = "i18n.t('ui_i18n_t_ui_i1i18n.t('ui_i18n_t_ui_heartbeat_timeout')it("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_stale')", { session_id: currentSessionId, ms_since_heartbi18n.t('ui_i18n_t_ui_stale')    }
      } else {
        if (lastSi18n.t('ui_i18n_t_ui_stale')ui_i18n_t_ui_i18n_t_ui_onlinei18n.t('ui_i18n_t_ui_stream_stale')e = "i18n.t('ui_i18n_t_ui_i18n_t_ui_online')";
          emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_online')", { session_id: i18n.t('ui_i18n_t_ui_online');
        }
      }
    }, MONITOR_INTi18n.t('ui_i18n_t_ui_online')sse.onerror = (e) => {
    //i18n.t('ui_i18n_t_ui_stream_online')ally; we surface offline so UI can show banner
    emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_offline')", { session_id: currentSessionId, error: e?.message || "i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_error')" });
   i18n.t('ui_i18n_t_ui_stream_offline')reconnect with jitter to avoid thundering herd
    if (!reconnectTii18n.t('ui_i18n_t_ui_stream_error');
      const delay = jitteredDelay(BACKOFF_BASE_MS, BACKOFF_CAP_MS);
      emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_reconnecting')", { session_id: currentSessionId, attempt, delay });
      if (GIVEUP_ATTEMPTS > 0 &&i18n.t('ui_i18n_t_ui_stream_reconnecting')       emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_stream_retry_giveup')", { session_id: currentSessionId, attempt });
      }
      reconnectTimer i18n.t('ui_i18n_t_ui_stream_retry_giveup')onnectTimer = null;
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
      if (obj.type === "i18n.t('ui_i18n_t_ui_i18n_t_ui_system_keepalive')") {
        lastHeartbeatAt = Date.now();
        emit("i18n.t('ui_ii18n.t('ui_i18n_t_ui_system_keepalive')rtbeat')", { session_id: currentSessionId });
        if (lastStatei18n.t('ui_i18n_t_ui_stream_heartbeat')8n_t_ui_online')") {
          lastState = "i18n.t('ui_i18n_t_ui_i18n_t_ui_i18n.t('ui_i18n_t_ui_online')  emit("i18n.t('ui_i18n_t_ui_i18n_t_uii18n.t('ui_i18n_t_ui_online'){ session_id: currentSessionIi18n.t('ui_i18n_t_ui_stream_online')turn;
      }
      emit("i18n.t('ui_i18n_t_ui_i18n_t_ui_sse_event')", obj);
      if ((obj.tyi18n.t('ui_i18n_t_ui_sse_event')n_t_ui_i18n_t_ui_tolowercase')"uploads.progri18n.t('ui_i18n_t_ui_tolowercase')_i18n_t_ui_try_attachmentssti18n.t('ui_i18n_t_ui_try_attachmentsstore_applyprogressevent_obj_catch_catch_e_ignore_bad_payloads_but_log_once_console_warn')i18n_t_ui_i18n_t_ui_e_expori18n.t('ui_i18n_t_ui_e_export_function_getinfo_return_sessionid_currentsessionid_connected_sse_stale_laststate')i18n_t_ui_i18n_t_i18n.t('ui_i18n_t_ui_lasteventid_export_function_requestreconnect_immediate_reconnect_attempt_with_small_jitter_used_on_user_actions_if_reconnecttimer_try_cleartimeout_reconnecttimer_catch_reconnecttimer_null_attempt_math_min_attempt_1_const_delay_jittereddelay_manual_base_ms_manual_cap_ms_emit')reconnecting"i18n.t('ui_i18n_t_i18n.t('ui_i18n_t_ui_session_id_currentsessionid_attempt_delay_manual_true_settimeout_if_currentsessionid_close_start_currentsessionid_delay_allow_other_modules_to_request_reconnect_via_the_bus_on')')"stream.requestReconnect", () => requestReconnect());

export default { start, stop, getInfo, requestReconnect };
