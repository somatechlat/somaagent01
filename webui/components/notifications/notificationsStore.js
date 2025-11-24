// Notifications store: REST + SSE wiring via global stream bus
import { on, off, emit } from "/js/event-bus.js";
import { openModal } from "/js/modals.js";

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

// All notification endpoints require a ``tenant_id`` query parameter. The UI
// operates in a single‑tenant mode for now, so we default to the public tenant.
const DEFAULT_TENANT_ID = "public";

async function fetchList({ limit = 50, unreadOnly = false } = {}) {
  // Load notifications from the backend. The FastAPI endpoint returns a plain
  // array of notification objects (no wrapper field). We include the required
  // ``tenant_id`` query parameter and forward pagination/filters.
  state.loading = true;
  state.error = null;
  try {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    params.set("tenant_id", DEFAULT_TENANT_ID);
    if (unreadOnly) params.set("unread_only", "true");
    const resp = await fetch(`/v1/ui/notifications?${params.toString()}`, { credentials: "include" });
    if (!resp.ok) throw new Error(`list failed ${resp.status}`);
    const data = await resp.json();
    // The API returns the array directly.
    state.list = Array.isArray(data) ? data : [];
    if (state.list.length) {
      const last = state.list[state.list.length - 1];
      state.lastCursor = { created_at: last.created_at, id: last.id };
    }
    recalcUnread();
    emitUpdate();
  } catch (e) {
    state.error = e?.message || String(e);
  } finally {
    state.loading = false;
  }
}

// Creation also requires ``tenant_id``. Use the default public tenant.
async function create({ type, title, body, severity = "info", ttl_seconds, meta }) {
  // The FastAPI endpoint expects ``tenant_id`` in the request body (the UI
  // previously supplied it as a query parameter, which caused a 422 error).
  // We therefore include it explicitly in the JSON payload.
  const payload = {
    tenant_id: DEFAULT_TENANT_ID,
    type,
    title,
    body,
    severity,
    ttl_seconds,
    meta,
  };
  const resp = await fetch(`/v1/ui/notifications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  if (!resp.ok) throw new Error(`create failed ${resp.status}`);
  const data = await resp.json();
  // The API returns the created notification object directly (no wrapper).
  const item = data;
  if (item) {
    state.list.unshift(item);
    recalcUnread();
    emitUpdate();
  }
  return item;
}

async function markRead(id) {
  const resp = await fetch(`/v1/ui/notifications/${encodeURIComponent(id)}/read?tenant_id=${DEFAULT_TENANT_ID}`, { method: "POST", credentials: "include" });
  if (!resp.ok) throw new Error(`markRead failed ${resp.status}`);
  const idx = state.list.findIndex(n => n.id === id);
  if (idx >= 0) {
    state.list[idx] = { ...state.list[idx], read_at: new Date().toISOString() };
    recalcUnread();
    emitUpdate();
  }
}

// The DELETE endpoint for clearing notifications is defined at
// ``/v1/ui/notifications`` (no trailing ``/clear``). Adjust the request
// accordingly to avoid 405 Method Not Allowed errors.
async function clearAll() {
  const resp = await fetch(`/v1/ui/notifications?tenant_id=${DEFAULT_TENANT_ID}`, { method: "DELETE", credentials: "include" });
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
