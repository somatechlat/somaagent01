// Notifications store: REST + SSE wiring via global stream bus
import { on, off, emit } from "../../js/event-bus.js";
import { openModal } from "../../js/modals.js";

const state = {
  list: [],
  unreadCount: 0,
  lastCursor: null,
  loading: false,
  error: null,
  // Toast stack (in-memory, frontend only)
  toastStack: [],
};

const MAX_TOASTS = 5;

function recalcUnread() {
  state.unreadCount = state.list.reduce((acc, n) => acc + (n.read_at ? 0 : 1), 0);
}

function emitUpdate() {
  emit("notifications.updated", { count: state.list.length, unread: state.unreadCount });
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
    emitUpdate();
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
    emitUpdate();
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
    emitUpdate();
  }
}

async function clearAll() {
  const resp = await fetch(`/v1/ui/notifications/clear`, { method: "DELETE", credentials: "include" });
  if (!resp.ok) throw new Error(`clear failed ${resp.status}`);
  state.list = [];
  recalcUnread();
  emitUpdate();
}

function handleSse(evt) {
  try {
    if (!evt || evt.type !== "ui.notification") return;
    const { action, notification, id } = evt;
    if (action === "created" && notification) {
      state.list.unshift(notification);
      // Autotoast new unread notifications (simple rule: severity != 'info')
      if (!notification.read_at) addToastFromNotification(notification);
    } else if (action === "read" && id) {
      const idx = state.list.findIndex(n => n.id === id);
      if (idx >= 0) state.list[idx] = { ...state.list[idx], read_at: new Date().toISOString() };
      pruneToastByNotification(id);
    } else if (action === "cleared") {
      state.list = [];
      state.toastStack = [];
    }
    recalcUnread();
    emitUpdate();
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
  // Unified modal open
  async openModal() {
    await openModal("notifications/notification-modal.html");
    // After modal interaction, mark all as read
    const unread = state.list.filter(n => !n.read_at).map(n => n.id);
    for (const id of unread) { try { await markRead(id); } catch {} }
  },
  // Toast helpers
  addFrontendToastOnly(type, title, body = "", ttl_seconds = 5) {
    addToast({ id: `frontend-${Date.now()}-${Math.random().toString(36).slice(2)}`, type, title, body, severity: type, read_at: null, ttl_seconds });
  },
  createToast(type, title, body = "", ttl_seconds = 5) {
    // also push as notification (for consistency) then toast it
    try { this.create({ type, title, body, severity: type, ttl_seconds }); } catch { this.addFrontendToastOnly(type, title, body, ttl_seconds); }
  },
  dismissToast(toastId) { removeToast(toastId, true); },
};

export default { store };

// --- Toast stack implementation ---
function addToast(notificationLike) {
  const toast = {
    toastId: `toast-${notificationLike.id}`,
    created_at: Date.now(),
    ...notificationLike,
  };
  state.toastStack.push(toast);
  while (state.toastStack.length > MAX_TOASTS) state.toastStack.shift();
  emitUpdate();
  // auto-remove after ttl
  const ttlMs = (notificationLike.ttl_seconds || 5) * 1000;
  setTimeout(() => removeToast(toast.toastId, false), ttlMs);
}

function removeToast(toastId, user) {
  const idx = state.toastStack.findIndex(t => t.toastId === toastId);
  if (idx >= 0) {
    const t = state.toastStack[idx];
    state.toastStack.splice(idx,1);
    if (user) { // mark read if user dismissed
      pruneToastByNotification(t.id);
      try { markRead(t.id); } catch {}
    }
    emitUpdate();
  }
}

function pruneToastByNotification(notifId) {
  state.toastStack = state.toastStack.filter(t => t.id !== notifId);
  emitUpdate();
}

function addToastFromNotification(n) {
  // basic severity rule
  if (!n) return;
  addToast({ id: n.id, type: n.type || n.severity || "info", title: n.title || n.body || "Notification", body: n.body || "", severity: n.severity || n.type || "info", ttl_seconds: n.ttl_seconds || 5 });
}
