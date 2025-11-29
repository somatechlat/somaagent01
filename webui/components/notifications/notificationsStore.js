// Notifications store: REST + SSE wiring via global stream bus
import { on, off, emit } from "i18n.t('ui_i18n_t_ui_js_event_bus_js')";
import { openModal } from "i18n.t('ui_i18n_t_ui_js_modals_js')";

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
  emit("i18n.t('ui_i18n_t_ui_notifications_updated')", { count: state.list.length, unread: state.unreadCount });
}

async function fetchList({ limit = 50, unreadOnly = false } = {}) {
  state.loading = true;
  state.error = null;
  try {
    const params = new URLSearchParams();
    params.set("i18n.t('ui_i18n_t_ui_limit')", String(limit));
    if (unreadOnly) params.set("i18n.t('ui_i18n_t_ui_unread_only')", "i18n.t('ui_i18n_t_ui_true')");
    const resp = await fetch(`/v1/notifications?${params.toString()}`, { credentials: "i18n.t('ui_i18n_t_ui_include')" });
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

async function create({ type, title, body, severity = "i18n.t('ui_i18n_t_ui_info')", ttl_seconds, meta }) {
  const resp = await fetch("i18n.t('ui_i18n_t_ui_v1_notifications')", {
    method: "i18n.t('ui_i18n_t_ui_post')",
    headers: { "i18n.t('ui_i18n_t_ui_content_type')": "i18n.t('ui_i18n_t_ui_application_json')" },
    body: JSON.stringify({ type, title, body, severity, ttl_seconds, meta }),
    credentials: "i18n.t('ui_i18n_t_ui_include')",
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
  const resp = await fetch(`/v1/notifications/${encodeURIComponent(id)}/read`, { method: "i18n.t('ui_i18n_t_ui_post')", credentials: "i18n.t('ui_i18n_t_ui_include')" });
  if (!resp.ok) throw new Error(`markRead failed ${resp.status}`);
  const idx = state.list.findIndex(n => n.id === id);
  if (idx >= 0) {
    state.list[idx] = { ...state.list[idx], read_at: new Date().toISOString() };
    recalcUnread();
    emitUpdate();
  }
}

async function clearAll() {
  const resp = await fetch(`/v1/notifications/clear`, { method: "i18n.t('ui_i18n_t_ui_delete')", credentials: "i18n.t('ui_i18n_t_ui_include')" });
  if (!resp.ok) throw new Error(`clear failed ${resp.status}`);
  state.list = [];
  recalcUnread();
  emitUpdate();
}

function handleSse(evt) {
  try {
    if (!evt || evt.type !== "i18n.t('ui_i18n_t_ui_notification')") return;
    const { action, notification, id } = evt;
    if (action === "i18n.t('ui_i18n_t_ui_created')" && notification) {
      state.list.unshift(notification);
      // Autotoast new unread notifications (simple rule: severity != 'info')
      if (!notification.read_at) addToastFromNotification(notification);
    } else if (action === "i18n.t('ui_i18n_t_ui_read')" && id) {
      const idx = state.list.findIndex(n => n.id === id);
      if (idx >= 0) state.list[idx] = { ...state.list[idx], read_at: new Date().toISOString() };
      pruneToastByNotification(id);
    } else if (action === "i18n.t('ui_i18n_t_ui_cleared')") {
      state.list = [];
      state.toastStack = [];
    }
    recalcUnread();
    emitUpdate();
  } catch {}
}

function subscribe() {
  on("i18n.t('ui_i18n_t_ui_sse_event')", handleSse);
}

function unsubscribe() {
  off("i18n.t('ui_i18n_t_ui_sse_event')", handleSse);
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
    await openModal("i18n.t('ui_i18n_t_ui_notifications_notification_modal_html')");
    // After modal interaction, mark all as read
    const unread = state.list.filter(n => !n.read_at).map(n => n.id);
    for (const id of unread) { try { await markRead(id); } catch {} }
  },
  // Toast helpers
  addFrontendToastOnly(type, title, body = ""i18n.t('ui_i18n_t_ui_ttl_seconds_5_addtoast_id_frontend_date_now_math_random_tostring_36_slice_2_type_title_body_severity_type_read_at_null_ttl_seconds_createtoast_type_title_body')""i18n.t('ui_i18n_t_ui_ttl_seconds_5_also_push_as_notification_for_consistency_then_toast_it_try_this_create_type_title_body_severity_type_ttl_seconds_catch_this_addfrontendtoastonly_type_title_body_ttl_seconds_dismisstoast_toastid_removetoast_toastid_true_export_default_store_toast_stack_implementation_function_addtoast_notificationlike_const_toast_toastid_toast_notificationlike_id_created_at_date_now_notificationlike_state_toaststack_push_toast_while_state_toaststack_length_max_toasts_state_toaststack_shift_emitupdate_auto_remove_after_ttl_const_ttlms_notificationlike_ttl_seconds_5_1000_settimeout_removetoast_toast_toastid_false_ttlms_function_removetoast_toastid_user_const_idx_state_toaststack_findindex_t_t_toastid_toastid_if_idx_0_const_t_state_toaststack_idx_state_toaststack_splice_idx_1_if_user_mark_read_if_user_dismissed_prunetoastbynotification_t_id_try_markread_t_id_catch_emitupdate_function_prunetoastbynotification_notifid_state_toaststack_state_toaststack_filter_t_t_id_notifid_emitupdate_function_addtoastfromnotification_n_basic_severity_rule_if_n_return_addtoast_id_n_id_type_n_type_n_severity')"info"i18n.t('ui_i18n_t_ui_title_n_title_n_body')"Notification"i18n.t('ui_i18n_t_ui_body_n_body')""i18n.t('ui_i18n_t_ui_severity_n_severity_n_type')"info", ttl_seconds: n.ttl_seconds || 5 });
}
