// Stream client: wraps EventSource and emits onto event-bus
import { emit } from "/js/event-bus.js";

let sse = null;
let currentSessionId = null;
let lastEventId = null;
let lastHeartbeatAt = 0;
let monitorTimer = null;

function close() {
  try { if (sse) sse.close(); } catch {}
  sse = null;
  if (monitorTimer) { try { clearInterval(monitorTimer); } catch {} monitorTimer = null; }
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
    } catch (e) {
      // ignore bad payloads but log once
      console.warn("Bad SSE payload", e);
    }
  };
}

export function getInfo() {
  return { sessionId: currentSessionId, connected: !!sse, lastEventId };
}

export default { start, stop, getInfo };
