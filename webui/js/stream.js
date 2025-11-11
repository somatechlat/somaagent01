// Stream client: wraps EventSource and emits onto event-bus
import { emit, on } from "/js/event-bus.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";

let sse = null;
let currentSessionId = null;
let lastEventId = null;
let lastHeartbeatAt = 0;
let monitorTimer = null;
let reconnectTimer = null;
let attempt = 0;
let lastState = "offline"; // offline | stale | online

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
  emit("stream.offline", { session_id: currentSessionId });
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
    console.error("EventSource init failed", e);
    emit("stream.offline", { session_id: currentSessionId, error: e?.message || String(e) });
    lastState = "offline";
    return;
  }

  sse.onopen = () => {
    lastHeartbeatAt = Date.now();
    emit("stream.online", { session_id: currentSessionId });
    if (attempt > 0) emit("stream.retry.success", { session_id: currentSessionId, attempt });
    attempt = 0; // reset after successful open
    lastState = "online";

    // Start simple heartbeat monitor
    if (monitorTimer) { try { clearInterval(monitorTimer); } catch {} }
    monitorTimer = setInterval(() => {
      const now = Date.now();
      const diff = now - lastHeartbeatAt;
      if (diff > HEARTBEAT_DEAD_MS) {
        if (lastState !== "offline") {
          lastState = "offline";
          emit("stream.offline", { session_id: currentSessionId, reason: "heartbeat-timeout" });
        }
      } else if (diff > HEARTBEAT_STALE_MS) {
        if (lastState !== "stale") {
          lastState = "stale";
          emit("stream.stale", { session_id: currentSessionId, ms_since_heartbeat: diff });
        }
      } else {
        if (lastState !== "online") {
          lastState = "online";
          emit("stream.online", { session_id: currentSessionId });
        }
      }
    }, MONITOR_INTERVAL_MS);
  };

  sse.onerror = (e) => {
    // Browser retries automatically; we surface offline so UI can show banner
    emit("stream.offline", { session_id: currentSessionId, error: e?.message || "stream error" });
    // Also schedule a manual reconnect with jitter to avoid thundering herd
    if (!reconnectTimer) {
      attempt += 1;
      const delay = jitteredDelay(BACKOFF_BASE_MS, BACKOFF_CAP_MS);
      emit("stream.reconnecting", { session_id: currentSessionId, attempt, delay });
      if (GIVEUP_ATTEMPTS > 0 && attempt >= GIVEUP_ATTEMPTS) {
        emit("stream.retry.giveup", { session_id: currentSessionId, attempt });
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
      if (obj.type === "system.keepalive") {
        lastHeartbeatAt = Date.now();
        emit("stream.heartbeat", { session_id: currentSessionId });
        if (lastState !== "online") {
          lastState = "online";
          emit("stream.online", { session_id: currentSessionId });
        }
        return;
      }
      emit("sse:event", obj);
      if ((obj.type || "").toLowerCase() === "uploads.progress") {
        try { attachmentsStore.applyProgressEvent(obj); } catch {}
      }
    } catch (e) {
      // ignore bad payloads but log once
      console.warn("Bad SSE payload", e);
    }
  };
}

export function getInfo() {
  return { sessionId: currentSessionId, connected: !!sse, stale: lastState === "stale", lastEventId };
}

export function requestReconnect() {
  // Immediate reconnect attempt with small jitter, used on user actions
  if (reconnectTimer) { try { clearTimeout(reconnectTimer); } catch {} reconnectTimer = null; }
  attempt = Math.min(attempt, 1);
  const delay = jitteredDelay(MANUAL_BASE_MS, MANUAL_CAP_MS);
  emit("stream.reconnecting", { session_id: currentSessionId, attempt, delay, manual: true });
  setTimeout(() => {
    if (currentSessionId) {
      close();
      start(currentSessionId);
    }
  }, delay);
}

// Allow other modules to request reconnect via the bus
on("stream.requestReconnect", () => requestReconnect());

export default { start, stop, getInfo, requestReconnect };
