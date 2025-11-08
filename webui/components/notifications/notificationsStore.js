// Notifications store: REST + SSE wiring via global stream bus
import { on, off, emit } from "/js/event-bus.js";

const state = {
  list: [],
  unreadCount: 0,
  lastCursor: null,
  loading: false,
  error: null,
};

function recalcUnread() {
  state.unreadCount = state.list.reduce((acc, n) => acc + (n.read_at ? 0 : 1), 0);
}

async function fetchList({ limit = 50, unreadOnly = false } = {}) {
  state.loading = true;
  state.error = null;
  try {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    if (unreadOnly) params.set("unread_only", "true");
    const resp = await fetch(`/v1/ui/notifications?${params.toString()}`, { credentials: "include" });
    if (!resp.ok) throw new Error(`list failed ${resp.status}`);
    const data = await resp.json();
    state.list = data.notifications || [];
    if (state.list.length) state.lastCursor = { created_at: state.list[state.list.length-1].created_at, id: state.list[state.list.length-1].id };
    recalcUnread();
    emit("notifications.updated", { count: state.list.length, unread: state.unreadCount });
  } catch (e) {
    state.error = e?.message || String(e);
  } finally {
    state.loading = false;
  }
}

async function create({ type, title, body, severity = "info", ttl_seconds, meta }) {
  const resp = await fetch("/v1/ui/notifications", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, title, body, severity, ttl_seconds, meta }),
    credentials: "include",
  });
  if (!resp.ok) throw new Error(`create failed ${resp.status}`);
  const data = await resp.json();
  const item = data.notification;
  if (item) {
    state.list.unshift(item);
    recalcUnread();
    emit("notifications.updated", { count: state.list.length, unread: state.unreadCount });
  }
  return item;
}

async function markRead(id) {
  const resp = await fetch(`/v1/ui/notifications/${encodeURIComponent(id)}/read`, { method: "POST", credentials: "include" });
  if (!resp.ok) throw new Error(`markRead failed ${resp.status}`);
  const idx = state.list.findIndex(n => n.id === id);
  if (idx >= 0) {
    state.list[idx] = { ...state.list[idx], read_at: new Date().toISOString() };
    recalcUnread();
    emit("notifications.updated", { count: state.list.length, unread: state.unreadCount });
  }
}

async function clearAll() {
  const resp = await fetch(`/v1/ui/notifications/clear`, { method: "DELETE", credentials: "include" });
  if (!resp.ok) throw new Error(`clear failed ${resp.status}`);
  state.list = [];
  recalcUnread();
  emit("notifications.updated", { count: 0, unread: 0 });
}

function handleSse(evt) {
  try {
    if (!evt || evt.type !== "ui.notification") return;
    const { action, notification, id } = evt;
    if (action === "created" && notification) {
      state.list.unshift(notification);
    } else if (action === "read" && id) {
      const idx = state.list.findIndex(n => n.id === id);
      if (idx >= 0) state.list[idx] = { ...state.list[idx], read_at: new Date().toISOString() };
    } else if (action === "cleared") {
      state.list = [];
    }
    recalcUnread();
    emit("notifications.updated", { count: state.list.length, unread: state.unreadCount });
  } catch {}
}

function subscribe() {
  on("sse:event", handleSse);
}

function unsubscribe() {
  off("sse:event", handleSse);
}

export const store = {
  state,
  fetchList,
  create,
  markRead,
  clearAll,
  subscribe,
  unsubscribe,
};

export default { store };
