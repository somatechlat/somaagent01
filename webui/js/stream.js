// Stream client: wraps EventSource and emits onto event-bus
import { emit } from "/js/event-bus.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";

let sse = null;
let currentSessionId = null;
let lastEventId = null;
let lastHeartbeatAt = 0;
let monitorTimer = null;
let reconnectTimer = null;
let attempt = 0;

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

  const url = `/v1/session/${encodeURIComponent(sessionId)}/events`;
  try {
    sse = new EventSource(url);
  } catch (e) {
    console.error("EventSource init failed", e);
    emit("stream.offline", { session_id: currentSessionId, error: e?.message || String(e) });
    return;
  }

  sse.onopen = () => {
    lastHeartbeatAt = Date.now();
    emit("stream.online", { session_id: currentSessionId });
    attempt = 0; // reset after successful open

    // Start simple heartbeat monitor
    if (monitorTimer) { try { clearInterval(monitorTimer); } catch {} }
    monitorTimer = setInterval(() => {
      const now = Date.now();
      // 20s without heartbeat → consider offline; EventSource will auto-retry
      if (now - lastHeartbeatAt > 20000) {
        emit("stream.offline", { session_id: currentSessionId, reason: "heartbeat-timeout" });
      }
    }, 5000);
  };

  sse.onerror = (e) => {
    // Browser retries automatically; we surface offline so UI can show banner
    emit("stream.offline", { session_id: currentSessionId, error: e?.message || "stream error" });
    // Also schedule a manual reconnect with jitter to avoid thundering herd
    if (!reconnectTimer) {
      attempt += 1;
      const delay = jitteredDelay(500, 15000);
      emit("stream.reconnecting", { session_id: currentSessionId, attempt, delay });
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
  return { sessionId: currentSessionId, connected: !!sse, lastEventId };
}

export function requestReconnect() {
  // Immediate reconnect attempt with small jitter, used on user actions
  if (reconnectTimer) { try { clearTimeout(reconnectTimer); } catch {} reconnectTimer = null; }
  attempt = Math.min(attempt, 1);
  const delay = jitteredDelay(200, 1000);
  emit("stream.reconnecting", { session_id: currentSessionId, attempt, delay, manual: true });
  setTimeout(() => {
    if (currentSessionId) {
      close();
      start(currentSessionId);
    }
  }, delay);
}

export default { start, stop, getInfo, requestReconnect };
