import * as msgs from "/js/messages.js";
import * as api from "/js/api.js";
import * as css from "/js/css.js";
import { importComponent } from "/js/components.js";
import { sleep } from "/js/sleep.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

globalThis.fetchApi = api.fetchApi; // TODO - backward compatibility for non-modular scripts, remove once refactored to alpine

const leftPanel = document.getElementById("left-panel");
const rightPanel = document.getElementById("right-panel");
const container = document.querySelector(".container");
const chatInput = document.getElementById("chat-input");
const chatHistory = document.getElementById("chat-history");
const sendButton = document.getElementById("send-button");
const inputSection = document.getElementById("input-section");
const statusSection = document.getElementById("status-section");
const chatsSection = document.getElementById("chats-section");
const tasksSection = document.getElementById("tasks-section");
const progressBar = document.getElementById("progress-bar");
const autoScrollSwitch = document.getElementById("auto-scroll-switch");
const timeDate = document.getElementById("time-date-container");

let autoScroll = true;
let context = "";
let resetCounter = 0;
let skipOneSpeech = false;
let connectionStatus = undefined; // undefined = not checked yet, true = connected, false = disconnected
let healthState = { status: "unknown", components: {} };
// Dev guards/counters to prevent unintended re-inits and to aid debugging
window.__newContextCount = window.__newContextCount || 0;
window.__defaultSelectionDone = window.__defaultSelectionDone || false;

// --- Gateway SSE streaming helpers (Sprint S2) ---
let _gatewaySSE = null;
let _gatewaySSESession = null;
let _sseActiveAssistantBySession = {}; // sessionId -> stable in-progress assistant message id
let __sseConnected = false; // dedupe poll vs SSE when connected
let __sseDesired = false; // true as soon as we attempt to open SSE; helps dedupe before onopen
let __provisionalContext = false; // set true when we create a temp session id client-side prior to server ack
let _optimisticToolStarts = new Map(); // toolName -> optimistic message id
let __sendInFlight = false; // gate duplicate rapid submissions

// Render a single Gateway event payload to the chat UI in a normalized way
function renderGatewayEvent(sessionId, event) {
  try {
    if (!event) return;
    const kind = String(event.type || "").toLowerCase();
    const role = (event.role || "assistant").toLowerCase();
    const meta = event.metadata || {};
    const status = String(meta.status || "").toLowerCase();
    const isStreaming = status === "streaming";
    const content = event.message || "";

    // Use a stable id for all streaming chunks in a single assistant turn, and per-tool lifecycle
    let stableId = event.event_id || event.id || generateGUID();

    // Normalize tool lifecycle even if role is misclassified but metadata indicates a tool event
    if ((meta && meta.tool_name) && (status === "start" || kind === "tool.start" || kind === "tool.result")) {
      const toolName = meta.tool_name || event.tool_name || "Tool";
      const isStart = status === "start" || kind === "tool.start";
      const reqId = meta.request_id || meta.requestId || stableId;
      const heading = `Tool: ${toolName}`;
      const body = isStart ? "Starting…" : content;
      // Dedupe any prior optimistic start for same tool name
      try {
        const optId = _optimisticToolStarts.get(toolName);
        if (optId && optId !== reqId) {
          removeMessageById(optId);
          _optimisticToolStarts.delete(toolName);
        }
      } catch (_) {}
      setMessage(reqId, "tool", heading, body, false, { ...meta });
      return;
    }

    if (role === "assistant") {
      // Insert a Thinking… placeholder only for streaming or explicit thinking events
      if (isStreaming || kind === "assistant.thinking") {
        const thinkingId = `assistant-current-${sessionId}`;
        if (!document.getElementById(`message-${thinkingId}`)) {
          setMessage(
            thinkingId,
            "agent",
            "Thinking…",
            "",
            false,
            meta && (meta.analysis ? { thoughts: meta.analysis } : { ...meta })
          );
        }
      }
      if (isStreaming) {
        if (!_sseActiveAssistantBySession[sessionId]) {
          _sseActiveAssistantBySession[sessionId] = `assistant-current-${sessionId}`;
        }
        stableId = _sseActiveAssistantBySession[sessionId];
      } else if (_sseActiveAssistantBySession[sessionId]) {
        // Finalize by reusing the in-progress id, then clear it
        stableId = _sseActiveAssistantBySession[sessionId];
        delete _sseActiveAssistantBySession[sessionId];
      }
      // Surface explicit chat failures as a red toast so it's visible
      try {
        const msg = (event.message || "").toString();
        const m = meta || {};
        const looksFailure = (m.error && String(m.error).length > 0) || msg.trim().toLowerCase().startsWith("i encountered an error");
        if (!isStreaming && looksFailure) {
          notificationStore.frontendError(
            m.error ? String(m.error) : "Agent failed to reply. Check settings and provider credentials.",
            "Chat error",
            8,
            "chat-error"
          );
        }
      } catch (_) {}
    } else if (role === "tool") {
      // Prefer request_id for stable threading of tool.start -> tool.result
      const reqId = meta.request_id || meta.requestId || null;
      if (reqId) stableId = reqId;
    }

    // Thinking event
    if (role === "assistant" && (status === "thinking" || kind === "assistant.thinking")) {
      const kvps = meta && (meta.analysis ? { thoughts: meta.analysis } : { ...meta });
      setMessage(stableId, "agent", "Thinking…", "", false, kvps);
      return;
    }

    // Tool lifecycle: accept either role+status or explicit type names
    if (role === "tool" || kind === "tool.start" || kind === "tool.result") {
      const toolName = meta.tool_name || event.tool_name || "Tool";
      const heading = `Tool: ${toolName}`;
      const isStart = status === "start" || kind === "tool.start";
      // Use a stable id per tool lifecycle. Prefer request_id; otherwise, fall back to a deterministic id.
      const reqId = meta.request_id || meta.requestId || null;
      const fallbackId = `tool-${sessionId}-${toolName}`;
      stableId = reqId ? reqId : fallbackId;
      // Keep a visible "Starting…" body for lifecycle parity; show details via kvps/meta on result.
      const body = "Starting…";
      // Dedupe any prior optimistic start for same tool name
      try {
        const optId = _optimisticToolStarts.get(toolName);
        if (optId && optId !== stableId) {
          removeMessageById(optId);
          _optimisticToolStarts.delete(toolName);
        }
        // If backend emits request_id only on result, remove any prior fallback-id message
        if (reqId && fallbackId !== reqId) {
          removeMessageById(fallbackId);
        }
        // Additional UI dedupe: ensure only one "Tool: <name>" heading exists
        try {
          const headings = Array.from(document.querySelectorAll('#chat-history .message-tool .msg-heading h4'));
          for (const h of headings) {
            if (String(h.textContent || '').trim().toLowerCase() === heading.toLowerCase()) {
              const container = h.closest('.message-container');
              if (container && container.id !== `message-${stableId}`) {
                container.remove();
              }
            }
          }
        } catch (_) {}
      } catch (_) {}
      setMessage(stableId, "tool", heading, body, false, { ...meta });
      return;
    }

    // Upload progress events (sa01-v1)
    if (kind === "uploads.progress") {
      const filename = meta.filename || "file";
      const bytes = meta.bytes_uploaded || 0;
      const total = meta.bytes_total || 0;
      const pct = total > 0 ? Math.min(100, Math.floor((bytes / total) * 100)) : null;
      const upId = `upload-${sessionId}-${filename}`;
      const isDone = (total > 0 && bytes >= total) || String(meta.status || '').toLowerCase() === 'done';
      const upHeading = `${isDone ? 'Uploaded' : 'Uploading'}: ${filename}`;
      const url = meta.url || (meta.attachment_id ? `/v1/attachments/${meta.attachment_id}` : undefined);
      const kv = { ...meta, percent: pct ?? 0, url };
      setMessage(upId, "upload", upHeading, "", false, kv);
      return;
    }

    // Default assistant/info rendering
    const heading = role === "assistant" ? "Soma response" : "Info";
    const type = role === "assistant" ? "response" : "info";
    const kvps = { ...meta };
    setMessage(stableId, type, heading, content, isStreaming, kvps);
  } catch (e) {
    console.warn("Event render error:", e);
  }
}

function removeMessageById(mid) {
  try {
    const el = document.getElementById(`message-${mid}`);
    if (el) {
      const group = el.parentElement && el.parentElement.classList?.contains('message-group') ? el.parentElement : el.closest('.message-group');
      el.remove();
      if (group && group.children.length === 0) {
        group.remove();
      }
    }
  } catch (_) { /* ignore */ }
}

function closeGatewayStream() {
  if (_gatewaySSE) {
    try {
      _gatewaySSE.close();
    } catch (e) {
      // ignore
    }
    _gatewaySSE = null;
    _gatewaySSESession = null;
  }
  __sseDesired = false;
}

function openGatewayStream(sessionId) {
  if (!sessionId) return;
  if (_gatewaySSE && _gatewaySSESession === sessionId) return;
  // Replace any existing stream
  closeGatewayStream();

  // Direct Gateway SSE only (legacy proxy removed)
  const base = (globalThis.__SA01_CONFIG__ && globalThis.__SA01_CONFIG__.api_base) || "/v1";
  const directUrl = `${String(base).replace(/\/$/, "")}/session/${encodeURIComponent(sessionId)}/events`;
  const es = new EventSource(directUrl);

  _gatewaySSE = es;
  _gatewaySSESession = sessionId;
  __sseDesired = true; // mark intent to stream immediately for poll dedupe

  const _handleSSEMessage = (evt) => {
    if (!evt?.data) return;
    try {
      const event = JSON.parse(evt.data);
      renderGatewayEvent(sessionId, event);
    } catch (e) {
      console.warn("SSE parse error:", e);
    }
  };

  es.onmessage = _handleSSEMessage;

  es.onerror = (e) => {
    // Notify once that live updates are offline; browser will auto-retry.
    if (!window.__sseWarned) {
      try {
        notificationStore.frontendWarning(
          "Live updates connection lost. We'll retry in the background.",
          "Live updates offline",
          6
        );
      } catch (_) {}
      window.__sseWarned = true;
    }
    __sseConnected = false;
  };

  es.onopen = () => {
    // Reset warning flag when connection re-establishes
    window.__sseWarned = false;
    __sseConnected = true;
  };
}

// Initialize the toggle button
setupSidebarToggle();
// Initialize tabs
setupTabs();

export function getAutoScroll() {
  return autoScroll;
}

function isMobile() {
  return window.innerWidth <= 768;
}

function toggleSidebar(show) {
  const overlay = document.getElementById("sidebar-overlay");
  if (typeof show === "boolean") {
    leftPanel.classList.toggle("hidden", !show);
    rightPanel.classList.toggle("expanded", !show);
    overlay.classList.toggle("visible", show);
  } else {
    leftPanel.classList.toggle("hidden");
    rightPanel.classList.toggle("expanded");
    overlay.classList.toggle(
      "visible",
      !leftPanel.classList.contains("hidden")
    );
  }
}

function handleResize() {
  const overlay = document.getElementById("sidebar-overlay");
  if (isMobile()) {
    leftPanel.classList.add("hidden");
    rightPanel.classList.add("expanded");
    overlay.classList.remove("visible");
  } else {
    leftPanel.classList.remove("hidden");
    rightPanel.classList.remove("expanded");
    overlay.classList.remove("visible");
  }
}

globalThis.addEventListener("load", handleResize);
globalThis.addEventListener("resize", handleResize);

document.addEventListener("DOMContentLoaded", () => {
  if (window.__overlayInitDone) return;
  window.__overlayInitDone = true;
  const overlay = document.getElementById("sidebar-overlay");
  overlay.addEventListener("click", () => {
    if (isMobile()) {
      toggleSidebar(false);
    }
  });
  // Eagerly load critical UI components so they are present before any toasts/updates
  try {
    const eagerSelectors = [
      'x-component[path="notifications/notification-toast-stack.html"]',
      'x-component[path="notifications/notification-icons.html"]',
      'x-component[path="/chat/attachments/inputPreview.html"]'
    ];
    const nodes = document.querySelectorAll(eagerSelectors.join(","));
    nodes.forEach((n) => {
      const p = n.getAttribute("path");
      if (p) importComponent(p, n).catch(() => {});
    });
  } catch (_) {}
  // Populate the chats list from live sessions (non-blocking)
  try { refreshChatsList(); } catch (_) {}
  // Kick a quick health probe so connection status becomes available immediately
  try {
    const base = (globalThis.__SA01_CONFIG__ && globalThis.__SA01_CONFIG__.api_base) || "/v1";
    fetch(String(base).replace(/\/$/, "") + "/health", { method: "GET", credentials: "same-origin" })
      .then(async (resp) => {
        if (!resp || !resp.ok) throw new Error("HTTP " + (resp && resp.status));
        const data = await resp.json().catch(() => ({}));
        const status = (data && (data.status || data.overall || data.state)) || "ok";
        setConnectionStatus(status, data && (data.components || data.services || {}));
      })
      .catch(() => {
        setConnectionStatus("down");
      });
  } catch (_) {
    /* ignore */
  }
});

function setupSidebarToggle() {
  const leftPanel = document.getElementById("left-panel");
  const rightPanel = document.getElementById("right-panel");
  const toggleSidebarButton = document.getElementById("toggle-sidebar");
  if (toggleSidebarButton) {
    toggleSidebarButton.addEventListener("click", toggleSidebar);
  } else {
    console.error("Toggle sidebar button not found");
    setTimeout(setupSidebarToggle, 100);
  }
}
// Avoid duplicate registrations; main UI init will call this once

export async function sendMessage() {
  if (__sendInFlight) return;
  __sendInFlight = true;
  try {
    // Gate sending if backend/gateway is unhealthy
    if (getConnectionStatus() === false) {
      // In dev/test, allow sending even if health shows down (poll may fail without infra)
      try {
        notificationStore.frontendWarning(
          "Agent appears offline – attempting to send anyway…",
          "Offline",
          4
        );
      } catch (_) {}
      // continue without returning; backend may still accept the request (outbox fallback)
    }
    const message = chatInput.value.trim();
    let attachmentsWithUrls = attachmentsStore.getAttachmentsForSending();
    // Fallback: if Alpine store hasn't processed the file input yet, read directly from the hidden input element
    if (!attachmentsWithUrls || attachmentsWithUrls.length === 0) {
      try {
        const fileInput = document.getElementById("file-input");
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
          attachmentsWithUrls = Array.from(fileInput.files).map((file) => ({ file, name: file.name, type: 'file' }));
        }
      } catch (_) {}
    }
    if (!attachmentsWithUrls || attachmentsWithUrls.length === 0) {
      // Allow one microtask/frame for any pending change handlers to populate
      try { await sleep(0); } catch {}
      try {
        const fileInput2 = document.getElementById("file-input");
        if (fileInput2 && fileInput2.files && fileInput2.files.length > 0) {
          attachmentsWithUrls = Array.from(fileInput2.files).map((file) => ({ file, name: file.name, type: 'file' }));
        }
      } catch {}
    }
    const hasAttachments = (attachmentsWithUrls && attachmentsWithUrls.length > 0);

    if (message || hasAttachments) {
      let response;
      const messageId = generateGUID();

      // Ensure we have a session id before sending so SSE can connect and receive early events
      if (!context || String(context).trim() === "") {
        const preCtx = generateGUID();
        setContext(preCtx);
        __provisionalContext = true;
        try { openGatewayStream(preCtx); } catch (_) {}
      } else {
        try { openGatewayStream(context); } catch (_) {}
      }

      // Clear input and attachments
      chatInput.value = "";
      attachmentsStore.clearAttachments();
      adjustTextareaHeight();

      // Optimistically add a Thinking… placeholder to avoid missing very-early SSE events during session handoff
      try {
        const sid = context || _gatewaySSESession || (typeof getContext === 'function' ? getContext() : null) || 'pending';
        const thinkingId = `assistant-current-${sid}`;
        if (!document.getElementById(`message-${thinkingId}`)) {
          setMessage(thinkingId, "agent", "Thinking…", "", false, {});
        }
      } catch (_) {}

      // Fast-path: slash command to trigger a tool request directly.
      if (!hasAttachments && message.toLowerCase().startsWith("/tool ")) {
        try {
          // Format: /tool <tool_name> <json-args>
          const parts = message.split(/\s+/, 3);
          const toolName = parts[1];
          const jsonArgsRaw = parts.length >= 3 ? message.slice(message.indexOf(toolName) + toolName.length).trim() : "{}";
          let args = {};
          if (jsonArgsRaw) {
            try {
              args = JSON.parse(jsonArgsRaw);
            } catch (e) {
              await toastFrontendError(`Invalid JSON for tool args: ${e?.message || e}`);
              return;
            }
          }
          // Ensure we have a session id to target
          if (!context) {
            setContext(generateGUID());
          }
          const trResp = await api.fetchApi("/v1/tool/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: context,
              tool_name: toolName,
              args,
              persona_id: undefined,
              metadata: {},
            }),
          });
          if (!trResp.ok) {
            const body = await trResp.text().catch(() => "");
            throw new Error(`Tool enqueue failed: HTTP ${trResp.status}${body ? ` — ${body}` : ""}`);
          }
          // Rely on SSE tool.start/result lifecycle to avoid duplicate headings
          // Ensure SSE is connected so we get the tool result event
          try {
            openGatewayStream(context);
          } catch (e) {
            console.warn("Failed to open Gateway SSE stream:", e);
          }
          justToast("Tool request enqueued", "success", 10000, "tool-enqueue");
          return; // Done handling /tool command
        } catch (e) {
          return toastFetchError("Error processing /tool command", e);
        }
      }

      // Include attachments in the user message
      if (hasAttachments) {
        const heading =
          attachmentsWithUrls.length > 0
            ? "Uploading attachments..."
            : "User message";

        // Render user message with attachments (optimistic)
        setMessage(messageId, "user", heading, message, false, {
          // attachments: attachmentsWithUrls, // skip here, let the backend properly log them
        });
        // Track local id so we can rename to server event_id when available
        window.__lastLocalUserId = messageId;

        // sleep one frame to render the message before upload starts - better UX
        sleep(0);

        // Do not render optimistic upload blocks; rely on uploads.progress SSE events

        // Gateway-first two-step: 1) upload files, 2) post message with attachment paths.
        let gatewaySucceeded = false;
        try {
          const uploadFd = new FormData();
          if (context) uploadFd.append("session_id", context);
          for (let i = 0; i < attachmentsWithUrls.length; i++) {
            uploadFd.append("files", attachmentsWithUrls[i].file);
          }
          const upResp = await api.fetchApi("/v1/uploads", { method: "POST", body: uploadFd });
          if (upResp.ok) {
            const filesJson = await upResp.json();
            const paths = Array.isArray(filesJson) ? filesJson.map((d) => d.path).filter(Boolean) : [];
            const msgResp = await api.fetchApi("/v1/session/message", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: context || undefined,
                persona_id: undefined,
                message,
                attachments: paths,
                metadata: {},
              }),
            });
            if (msgResp.ok) {
              const body = await msgResp.json().catch(() => ({}));
              response = new Response(
                JSON.stringify({ accepted: true, session_id: body.session_id, event_id: body.event_id }),
                { status: 200, headers: { "Content-Type": "application/json" } }
              );
              gatewaySucceeded = true;
            }
          }
        } catch (_) {}
      if (!gatewaySucceeded) {
        throw new Error("Failed to send message via Gateway");
      }
      } else {
        // For text-only messages
        // Render optimistic user message immediately
        setMessage(messageId, "user", "User message", message, false, {});
        window.__lastLocalUserId = messageId;
        // Prefer direct Gateway API
        const gwResp = await api.fetchApi("/v1/session/message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: context || undefined, persona_id: undefined, message, attachments: [], metadata: {} })
        });
        if (gwResp.ok) {
          const body = await gwResp.json().catch(() => ({}));
          response = new Response(JSON.stringify({ accepted: true, session_id: body.session_id, event_id: body.event_id }), { status: 200, headers: { "Content-Type": "application/json" } });
        } else {
          throw new Error(`Gateway message send failed: ${gwResp.status}`);
        }
      }

      // Handle response (be robust to non-JSON error bodies)
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        await toastFrontendError(
          `Message send failed: HTTP ${response.status}${text ? ` — ${text}` : ""}`,
          "Send Failed"
        );
        return;
      }
      const jsonResponse = await response.json().catch(() => null);
      if (!jsonResponse) {
        toast("No response returned.", "error");
      } else {
        // Gateway mode returns {accepted: true, session_id, event_id}
        if (jsonResponse.accepted && jsonResponse.session_id) {
          // Preserve chat if we are switching from a provisional client id to the server session id
          const preserve = __provisionalContext === true;
          setContext(jsonResponse.session_id, { preserveHistory: preserve });
          try {
            openGatewayStream(jsonResponse.session_id);
          } catch (e) {
            console.warn("Failed to open Gateway SSE stream:", e);
          }
          __provisionalContext = false;
          // If we rendered an optimistic user message, rename DOM ids to the server event_id to dedupe with poll
          try {
            if (jsonResponse.event_id && window.__lastLocalUserId) {
              const fromId = `message-${window.__lastLocalUserId}`;
              const toId = `message-${jsonResponse.event_id}`;
              const fromGroupId = `message-group-${window.__lastLocalUserId}`;
              const toGroupId = `message-group-${jsonResponse.event_id}`;
              const el = document.getElementById(fromId);
              if (el) el.id = toId;
              const grp = document.getElementById(fromGroupId);
              if (grp) grp.id = toGroupId;
              window.__lastLocalUserId = null;
            }
          } catch (_) {}
        } else if (jsonResponse.context) {
          // Local mode legacy path
          setContext(jsonResponse.context);
        }
      }
    }
  } catch (e) {
    toastFetchError("Error sending message", e); // Will use new notification system
  } finally {
    __sendInFlight = false;
  }
}

function toastFetchError(text, error) {
  console.error(text, error);
  // Use new frontend error notification system (async, but we don't need to wait)
  const errorMessage = error?.message || error?.toString() || "Unknown error";

  if (getConnectionStatus()) {
    // Backend is connected, just show the error
    toastFrontendError(`${text}: ${errorMessage}`).catch((e) =>
      console.error("Failed to show error toast:", e)
    );
  } else {
    // Backend is disconnected, show connection error
    toastFrontendError(
      `${text} (backend appears to be disconnected): ${errorMessage}`,
      "Connection Error"
    ).catch((e) => console.error("Failed to show connection error toast:", e));
  }
}
globalThis.toastFetchError = toastFetchError;

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) {
    e.preventDefault();
    sendMessage();
  }
});

sendButton.addEventListener("click", sendMessage);

// Global shortcuts for parity and productivity
// - Ctrl/Cmd+Enter: send message
// - Ctrl/Cmd+N: new chat
// - Ctrl/Cmd+Shift+D: delete current chat
document.addEventListener("keydown", (e) => {
  try {
    const isMac = navigator.platform.toUpperCase().includes("MAC");
    const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;
    if (!ctrlOrCmd) return;

    // Send message: Ctrl/Cmd+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
      return;
    }

    // New chat: Ctrl/Cmd+N
    if ((e.key === "n" || e.key === "N") && !e.shiftKey) {
      e.preventDefault();
      try { newChat(); } catch (_) {}
      return;
    }

    // Delete current chat: Ctrl/Cmd+Shift+D
    if ((e.key === "d" || e.key === "D") && e.shiftKey) {
      e.preventDefault();
      try { if (typeof killChat === 'function' && getContext()) killChat(getContext()); } catch(_) {}
      return;
    }
  } catch (_) {}
});

export function updateChatInput(text) {
  console.log("updateChatInput called with:", text);

  // Append text with proper spacing
  const currentValue = chatInput.value;
  const needsSpace = currentValue.length > 0 && !currentValue.endsWith(" ");
  chatInput.value = currentValue + (needsSpace ? " " : "") + text + " ";

  // Adjust height and trigger input event
  adjustTextareaHeight();
  chatInput.dispatchEvent(new Event("input"));

  console.log("Updated chat input value:", chatInput.value);
}

function updateUserTime() {
  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();
  const ampm = hours >= 12 ? "pm" : "am";
  const formattedHours = hours % 12 || 12;

  // Format the time
  const timeString = `${formattedHours}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")} ${ampm}`;

  // Format the date
  const options = { year: "numeric", month: "short", day: "numeric" };
  const dateString = now.toLocaleDateString(undefined, options);

  // Update the HTML
  const userTimeElement = document.getElementById("time-date");
  userTimeElement.innerHTML = `${timeString}<br><span id="user-date">${dateString}</span>`;
}

updateUserTime();
setInterval(updateUserTime, 1000);

function setMessage(id, type, heading, content, temp, kvps = null) {
  const result = msgs.setMessage(id, type, heading, content, temp, kvps);
  if (autoScroll) chatHistory.scrollTop = chatHistory.scrollHeight;
  return result;
}

globalThis.loadKnowledge = async function () {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".txt,.pdf,.csv,.html,.json,.md";
  input.multiple = true;

  input.onchange = async () => {
    try {
      const formData = new FormData();
      for (let file of input.files) {
        formData.append("files[]", file);
      }

      formData.append("ctxid", getContext());

      const response = await api.fetchApi("/import_knowledge", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        toast(await response.text(), "error");
      } else {
        const data = await response.json();
        toast(
          "Knowledge files imported: " + data.filenames.join(", "),
          "success"
        );
      }
    } catch (e) {
      toastFetchError("Error loading knowledge", e);
    }
  };

  input.click();
};

function adjustTextareaHeight() {
  chatInput.style.height = "auto";
  chatInput.style.height = chatInput.scrollHeight + "px";
}

export const sendJsonData = async function (url, data) {
  // Block legacy endpoints to avoid 404 spam and confusing errors
  const u = String(url || "");
  if (!u.startsWith("/v1/")) {
    const legacy = new Set([
      "/pause",
      "/chat_reset",
      "/chat_remove",
      "/nudge",
      "/restart",
      "/chat_load",
      "/chat_export",
      "/file_info",
      "/history_get",
      "/ctx_window_get",
    ]);
    if (legacy.has(u)) {
      throw new Error("Legacy UI action is disabled in this build.");
    }
  }
  return await api.callJsonApi(url, data);
};
globalThis.sendJsonData = sendJsonData;

function generateGUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0;
    var v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getConnectionStatus() {
  return connectionStatus;
}

function setConnectionStatus(status, components = null) {
  let indicatorStatus;
  if (typeof status === "string") {
    indicatorStatus = status;
    // Consider "degraded" as connected so users can send messages while memory is unavailable
    connectionStatus = status !== "down";
  } else {
    indicatorStatus = status ? "ok" : "down";
    connectionStatus = !!status;
  }

  const statusIconEl = document.getElementById("status-indicator");
  const offlineBanner = document.getElementById("offline-banner");
  const memoryBanner = document.getElementById("memory-banner");
  if (statusIconEl) {
    statusIconEl.dataset.status = indicatorStatus;
    const tooltip = formatHealthTooltip(components, indicatorStatus);
    statusIconEl.setAttribute("title", tooltip);
  }
  if (offlineBanner) {
    if (indicatorStatus === "down") {
      offlineBanner.classList.remove("hidden");
      // Show toast notification once when going offline
      if (!window.__offlineNotified) {
        // Make it a prominent red toast using the current notification UI
        notificationStore.frontendError(
          "SomaBrain is offline – the gateway can't be reached. Chat may fail until the backend is healthy.",
          "Offline",
          8
        );
        window.__offlineNotified = true;
      }
    } else {
      offlineBanner.classList.add("hidden");
      // Reset flag when back online
      window.__offlineNotified = false;
    }
  }

  // Memory-only degradation indicator
  try {
    let memoryDegraded = false;
    if (components && typeof components === 'object') {
      for (const [name, info] of Object.entries(components)) {
        const key = String(name || '').toLowerCase();
        const status = (info && (info.status || info.state)) || '';
        const s = String(status).toLowerCase();
        const looksMemory = /memory|somabrain|replicator|wm|sync/.test(key);
        if (looksMemory && (s === 'down' || s === 'degraded' || s === 'error' || s === 'warning' || s === 'unhealthy')) {
          memoryDegraded = true;
          break;
        }
      }
    }
    if (memoryBanner) {
      // Show memory banner only when overall is not fully down but memory is degraded
      if (indicatorStatus !== 'down' && memoryDegraded) {
        memoryBanner.classList.remove('hidden');
        if (!window.__memoryNotified) {
          notificationStore.frontendWarning(
            'Memories degraded – conversation will continue but long-term memory may be delayed.',
            'Memories degraded',
            6,
            'memory-health'
          );
          window.__memoryNotified = true;
        }
      } else {
        memoryBanner.classList.add('hidden');
        window.__memoryNotified = false;
      }
    }
  } catch (e) {
    // Non-fatal
  }
}

function formatHealthTooltip(components, status) {
  const header = `Health: ${status}`;
  if (!components || Object.keys(components).length === 0) {
    return header;
  }
  const lines = Object.entries(components).map(([name, info]) => {
    if (info && typeof info === "object") {
      const detail = info.detail ? ` (${info.detail})` : "";
      return `${name}: ${info.status ?? "unknown"}${detail}`;
    }
    return `${name}: ${info}`;
  });
  return `${header}\n${lines.join("\n")}`;
}

let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;

// Legacy poll removed: SSE is the sole transport for messages/events
// (poll() removed)

// Fetch recent events for a session and render them into the chat history
async function loadSessionHistory(sessionId) {
  if (!sessionId) return;
  try {
    const resp = await api.fetchApi(`/v1/sessions/${encodeURIComponent(sessionId)}/events?limit=200`, { method: 'GET' });
    if (!resp.ok) return;
    const body = await resp.json().catch(() => null);
    if (!body || !Array.isArray(body.events)) return;
    for (const entry of body.events) {
      const payload = entry && entry.payload ? entry.payload : null;
      if (!payload) continue;
      renderGatewayEvent(sessionId, payload);
    }
  } catch (e) {
    // benign: do not disrupt UI if history fails
  }
}

async function monitorHealth() {
  while (true) {
    try {
      const base = (globalThis.__SA01_CONFIG__ && globalThis.__SA01_CONFIG__.api_base) || "/v1";
      const response = await fetch(String(base).replace(/\/$/, "") + "/health", {
        method: "GET",
        credentials: "same-origin",
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      healthState = {
        status: data.status || "ok",
        components: data.components || {},
      };
      setConnectionStatus(healthState.status, healthState.components);
    } catch (error) {
      healthState = {
        status: "down",
        components: {
          gateway: { status: "down", detail: error?.message || "unreachable" },
        },
      };
      setConnectionStatus(healthState.status, healthState.components);
    }
    await sleep(15000);
  }
}

monitorHealth().catch((error) => console.error("Health monitor failed", error));

function afterMessagesUpdate(logs) {
  if (localStorage.getItem("speech") == "true") {
    speakMessages(logs);
  }
}

function speakMessages(logs) {
  if (skipOneSpeech) {
    skipOneSpeech = false;
    return;
  }
  // log.no, log.type, log.heading, log.content
  for (let i = logs.length - 1; i >= 0; i--) {
    const log = logs[i];

    // if already spoken, end
    // if(log.no < lastSpokenNo) break;

    // finished response
    if (log.type == "response") {
      // lastSpokenNo = log.no;
      speechStore.speakStream(
        getChatBasedId(log.no),
        log.content,
        log.kvps?.finished
      );
      return;

      // finished LLM headline, not response
    } else if (
      log.type == "agent" &&
      log.kvps &&
      log.kvps.headline &&
      log.kvps.tool_args &&
      log.kvps.tool_name != "response"
    ) {
      // lastSpokenNo = log.no;
      speechStore.speakStream(getChatBasedId(log.no), log.kvps.headline, true);
      return;
    }
  }
}

function updateProgress(progress, active) {
  if (!progress) progress = "";

  if (!active) {
    removeClassFromElement(progressBar, "shiny-text");
  } else {
    addClassToElement(progressBar, "shiny-text");
  }

  progress = msgs.convertIcons(progress);

  if (progressBar.innerHTML != progress) {
    progressBar.innerHTML = progress;
  }
}

globalThis.pauseAgent = async function (paused) {
  try {
    if (!context) return;
    const resp = await api.fetchApi(`/v1/sessions/${context}/pause`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paused }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  } catch (e) {
    globalThis.toastFetchError("Error pausing agent", e);
  }
};

globalThis.resetChat = async function (ctxid = null) {
  try {
    const sid = ctxid === null ? context : ctxid;
    if (!sid) return;
    const resp = await api.fetchApi(`/v1/sessions/${sid}/reset`, { method: "POST" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    // Immediately clear local state and history for this session to reflect reset
    setContext(sid);
    resetCounter++;
    if (ctxid === null) updateAfterScroll();
  } catch (e) {
    globalThis.toastFetchError("Error resetting chat", e);
  }
};

globalThis.newChat = async function () {
  try {
    newContext();
    updateAfterScroll();
  } catch (e) {
    globalThis.toastFetchError("Error creating new chat", e);
  }
};

globalThis.killChat = async function (id) {
  if (!id) {
    console.error("No chat ID provided for deletion");
    return;
  }

  console.log("Deleting chat with ID:", id);

  try {
    const chatsAD = Alpine.$data(chatsSection);
    console.log(
      "Current contexts before deletion:",
      JSON.stringify(chatsAD.contexts.map((c) => ({ id: c.id, name: c.name })))
    );

    // switch to another context if deleting current
    switchFromContext(id);

    // Delete the chat on the server
    const del = await api.fetchApi(`/v1/sessions/${id}`, { method: "DELETE" });
    if (!del.ok) throw new Error(`HTTP ${del.status}`);

    // Update the UI manually to ensure the correct chat is removed
    // Deep clone the contexts array to prevent reference issues
    const updatedContexts = chatsAD.contexts.filter((ctx) => ctx.id !== id);
    console.log(
      "Updated contexts after deletion:",
      JSON.stringify(updatedContexts.map((c) => ({ id: c.id, name: c.name })))
    );

    // Force UI update by creating a new array
    chatsAD.contexts = [...updatedContexts];

    updateAfterScroll();
    try { refreshChatsList(); } catch (_) {}
    justToast("Chat deleted successfully", "success", 1000, "chat-removal");
  } catch (e) {
    console.error("Error deleting chat:", e);
    globalThis.toastFetchError("Error deleting chat", e);
  }
};

export function switchFromContext(id) {
  // If we're deleting the currently selected chat, switch to another one first
  if (context === id) {
    const chatsAD = Alpine.$data(chatsSection);

    // Find an alternate chat to switch to if we're deleting the current one
    let alternateChat = null;
    for (let i = 0; i < chatsAD.contexts.length; i++) {
      if (chatsAD.contexts[i].id !== id) {
        alternateChat = chatsAD.contexts[i];
        break;
      }
    }

    if (alternateChat) {
      setContext(alternateChat.id);
    } else {
      // If no other chats, create a new empty context
      newContext();
    }
  }
}

// Function to ensure proper UI state when switching contexts
function ensureProperTabSelection(contextId) {
  // Get current active tab
  const activeTab = localStorage.getItem("activeTab") || "chats";

  // First attempt to determine if this is a task or chat based on the task list
  const tasksSection = document.getElementById("tasks-section");
  let isTask = false;

  if (tasksSection) {
    const tasksAD = Alpine.$data(tasksSection);
    if (tasksAD && tasksAD.tasks) {
      isTask = tasksAD.tasks.some((task) => task.id === contextId);
    }
  }

  // If we're selecting a task but are in the chats tab, switch to tasks tab
  if (isTask && activeTab === "chats") {
    // Store this as the last selected task before switching
    localStorage.setItem("lastSelectedTask", contextId);
    activateTab("tasks");
    return true;
  }

  // If we're selecting a chat but are in the tasks tab, switch to chats tab
  if (!isTask && activeTab === "tasks") {
    // Store this as the last selected chat before switching
    localStorage.setItem("lastSelectedChat", contextId);
    activateTab("chats");
    return true;
  }

  return false;
}

globalThis.selectChat = async function (id) {
  if (id === context) return; //already selected

  // Check if we need to switch tabs based on the context type
  const tabSwitched = ensureProperTabSelection(id);

  // If we didn't switch tabs, proceed with normal selection
  if (!tabSwitched) {
    // Switch to the new context - this will clear chat history and reset tracking variables
    setContext(id);

    // Update both contexts and tasks lists to reflect the selected item
    const chatsAD = Alpine.$data(chatsSection);
    const tasksSection = document.getElementById("tasks-section");
    if (tasksSection) {
      const tasksAD = Alpine.$data(tasksSection);
      tasksAD.selected = id;
    }
    chatsAD.selected = id;

    // Store this selection in the appropriate localStorage key
    const activeTab = localStorage.getItem("activeTab") || "chats";
    if (activeTab === "chats") {
      localStorage.setItem("lastSelectedChat", id);
    } else if (activeTab === "tasks") {
      localStorage.setItem("lastSelectedTask", id);
    }

    // No poll; setContext() handles history preload and SSE attach
  }

  updateAfterScroll();
};

function generateShortId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export const newContext = function () {
  context = generateShortId();
  setContext(context);
  try { window.__newContextCount++; } catch(_) {}
  // Optimistically add to chats list
  try {
    if (globalThis.Alpine && chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      if (chatsAD) {
        const exists = (chatsAD.contexts || []).some(c => c.id === context);
        if (!exists) {
          const nextNo = (chatsAD.contexts?.length || 0) + 1;
          const item = { id: context, name: "", no: nextNo };
          chatsAD.contexts = [item, ...(chatsAD.contexts || [])];
          chatsAD.selected = context;
        }
      }
    }
  } catch (_) {}
}

export const setContext = function (id, options = {}) {
  if (id == context) return;
  const preserve = options && options.preserveHistory === true;
  context = id;
  // Close any active Gateway SSE stream when switching context; a next send/open will reopen
  try { closeGatewayStream(); } catch (_) {}
  // Always reset the log tracking variables when switching contexts
  lastLogGuid = "";
  lastLogVersion = 0;
  lastSpokenNo = 0;

  // Stop speech when switching chats (unless preserving in-flight render)
  if (!preserve) {
    speechStore.stopAudio();
  }

  // Clear the chat history only when not preserving
  if (!preserve) {
    chatHistory.innerHTML = "";
  }

  // Update both selected states
  if (globalThis.Alpine) {
    if (chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      if (chatsAD) {
        chatsAD.selected = id;
        // Mark selection and ensure the chat exists in list if we have none yet
        if (!Array.isArray(chatsAD.contexts)) chatsAD.contexts = [];
        const exists = chatsAD.contexts.some(c => c.id === id);
        if (!exists) {
          const nextNo = (chatsAD.contexts?.length || 0) + 1;
          chatsAD.contexts = [{ id, name: "", no: nextNo }, ...chatsAD.contexts];
        }
      }
    }
    if (tasksSection) {
      const tasksAD = Alpine.$data(tasksSection);
      if (tasksAD) tasksAD.selected = id;
    }
  }

  //skip one speech if enabled when switching context
  if (localStorage.getItem("speech") == "true") skipOneSpeech = true;
  
  // Load recent history, then open SSE for live updates
  try {
    (async () => {
      try { await loadSessionHistory(id); } catch (_) {}
      try { openGatewayStream(id); } catch (_) {}
    })();
  } catch (_) {}
};

export const getContext = function () {
  return context;
};

export const getChatBasedId = function (id) {
  return context + "-" + resetCounter + "-" + id;
};

globalThis.toggleAutoScroll = async function (_autoScroll) {
  autoScroll = _autoScroll;
};

globalThis.toggleJson = async function (showJson) {
  css.toggleCssProperty(".msg-json", "display", showJson ? "block" : "none");
};

globalThis.toggleThoughts = async function (showThoughts) {
  css.toggleCssProperty(
    ".msg-thoughts",
    "display",
    showThoughts ? undefined : "none"
  );
};

globalThis.toggleUtils = async function (showUtils) {
  css.toggleCssProperty(
    ".message-util",
    "display",
    showUtils ? undefined : "none"
  );
};

globalThis.toggleDarkMode = function (isDark) {
  if (isDark) {
    document.body.classList.remove("light-mode");
    document.body.classList.add("dark-mode");
  } else {
    document.body.classList.remove("dark-mode");
    document.body.classList.add("light-mode");
  }
  console.log("Dark mode:", isDark);
  localStorage.setItem("darkMode", isDark);
};

globalThis.toggleSpeech = function (isOn) {
  console.log("Speech:", isOn);
  localStorage.setItem("speech", isOn);
  if (!isOn) speechStore.stopAudio();
};

globalThis.nudge = async function () {
  try {
    const sid = getContext();
    if (!sid) return;
    const resp = await api.fetchApi("/v1/session/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sid, action: "nudge", metadata: {} }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  } catch (e) {
    toastFetchError("Error nudging agent", e);
  }
};

// Restart action removed: feature not available in canonical Gateway UI.

// Modify this part
document.addEventListener("DOMContentLoaded", () => {
  const isDarkMode = localStorage.getItem("darkMode") !== "false";
  toggleDarkMode(isDarkMode);
});

globalThis.loadChats = async function () {
  try {
    const fileContents = await readJsonFiles();
    const resp = await api.fetchApi("/v1/sessions/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chats: fileContents }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json().catch(() => null);
    if (!data || !Array.isArray(data.ctxids) || data.ctxids.length === 0) {
      toast("No chats imported.", "warning");
      return;
    }
    setContext(data.ctxids[0], { preserveHistory: true });
    toast("Chats imported.", "success");
  } catch (e) {
    toastFetchError("Error loading chats", e);
  }
};

globalThis.saveChat = async function () {
  try {
    if (!context) throw new Error("No active session");
    const resp = await api.fetchApi("/v1/sessions/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: context }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json().catch(() => null);
    if (!data || !data.content) {
      toast("No export content returned.", "error");
      return;
    }
    const fname = (data.ctxid || context) + ".json";
    downloadFile(fname, data.content);
    toast("Chat file downloaded.", "success");
  } catch (e) {
    toastFetchError("Error saving chat", e);
  }
};

function downloadFile(filename, content) {
  // Create a Blob with the content to save
  const blob = new Blob([content], { type: "application/json" });

  // Create a link element
  const link = document.createElement("a");

  // Create a URL for the Blob
  const url = URL.createObjectURL(blob);
  link.href = url;

  // Set the file name for download
  link.download = filename;

  // Programmatically click the link to trigger the download
  link.click();

  // Clean up by revoking the object URL
  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 0);
}

function readJsonFiles() {
  return new Promise((resolve, reject) => {
    // Create an input element of type 'file'
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json"; // Only accept JSON files
    input.multiple = true; // Allow multiple file selection

    // Trigger the file dialog
    input.click();

    // When files are selected
    input.onchange = async () => {
      const files = input.files;
      if (!files.length) {
        resolve([]); // Return an empty array if no files are selected
        return;
      }

      // Read each file as a string and store in an array
      const filePromises = Array.from(files).map((file) => {
        return new Promise((fileResolve, fileReject) => {
          const reader = new FileReader();
          reader.onload = () => fileResolve(reader.result);
          reader.onerror = fileReject;
          reader.readAsText(file);
        });
      });

      try {
        const fileContents = await Promise.all(filePromises);
        resolve(fileContents);
      } catch (error) {
        reject(error); // In case of any file reading error
      }
    };
  });
}

function addClassToElement(element, className) {
  element.classList.add(className);
}

function removeClassFromElement(element, className) {
  element.classList.remove(className);
}

function justToast(text, type = "info", timeout = 5000, group = "") {
  try {
    notificationStore.addFrontendToastOnly(
      type,
      text,
      "",
      Math.max(1, timeout / 1000),
      group
    );
  } catch (_) {}
  // Fallback: if Alpine toast stack hasn't rendered yet, inject a minimal toast DOM so tests/UI see it immediately
  try {
    setTimeout(() => {
      const hasStack = document.querySelector('.toast-stack-container .toast-item');
      if (!hasStack) {
        let cont = document.querySelector('.toast-stack-container');
        if (!cont) {
          cont = document.createElement('div');
          cont.className = 'toast-stack-container';
          cont.style.position = 'fixed';
          cont.style.bottom = '10px';
          cont.style.right = '10px';
          cont.style.zIndex = '15000';
          cont.style.display = 'flex';
          cont.style.flexDirection = 'column-reverse';
          cont.style.gap = '8px';
          document.body.appendChild(cont);
        }
        const item = document.createElement('div');
        item.className = `toast-item notification-${type}`;
        item.style.padding = '12px';
        item.style.border = '1px solid var(--color-border)';
        item.style.borderLeft = '4px solid var(--color-primary)';
        item.style.background = 'var(--color-panel)';
        item.style.borderRadius = '8px';
        const span = document.createElement('div');
        span.className = 'toast-message';
        span.textContent = text;
        item.appendChild(span);
        cont.appendChild(item);
        setTimeout(() => { try { item.remove(); } catch(_) {} }, timeout);
      }
    }, 250);
  } catch (_) {}
}
  

function toast(text, type = "info", timeout = 5000) {
  // Convert timeout from milliseconds to seconds for new notification system
  const display_time = Math.max(timeout / 1000, 1); // Minimum 1 second

  // Use new frontend notification system based on type
    switch (type.toLowerCase()) {
      case "error":
        return notificationStore.frontendError(text, "Error", display_time);
      case "success":
        return notificationStore.frontendInfo(text, "Success", display_time);
      case "warning":
        return notificationStore.frontendWarning(text, "Warning", display_time);
      case "info":
      default:
        return notificationStore.frontendInfo(text, "Info", display_time);
    }

}
globalThis.toast = toast;

// OLD: hideToast function removed - now using new notification system

function scrollChanged(isAtBottom) {
  if (globalThis.Alpine && autoScrollSwitch) {
    const inputAS = Alpine.$data(autoScrollSwitch);
    if (inputAS) {
      inputAS.autoScroll = isAtBottom;
    }
  }
  // autoScrollSwitch.checked = isAtBottom
}

function updateAfterScroll() {
  // const toleranceEm = 1; // Tolerance in em units
  // const tolerancePx = toleranceEm * parseFloat(getComputedStyle(document.documentElement).fontSize); // Convert em to pixels
  const tolerancePx = 10;
  const chatHistory = document.getElementById("chat-history");
  const isAtBottom =
    chatHistory.scrollHeight - chatHistory.scrollTop <=
    chatHistory.clientHeight + tolerancePx;

  scrollChanged(isAtBottom);
}

chatHistory.addEventListener("scroll", updateAfterScroll);

chatInput.addEventListener("input", adjustTextareaHeight);

// Polling scheduler removed

// Setup event handlers once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  if (window.__mainUiInitDone) return;
  window.__mainUiInitDone = true;
  setupSidebarToggle();
  setupTabs();
  initializeActiveTab();
  // Populate chats list and ensure a reasonable default selection
  (async () => {
    try { await refreshChatsList(); } catch (_) {}
    try { ensureDefaultChatSelected(); } catch (_) {}
  })();
});

// Setup tabs functionality
function setupTabs() {
  const chatsTab = document.getElementById("chats-tab");
  const tasksTab = document.getElementById("tasks-tab");

  if (chatsTab && tasksTab) {
    chatsTab.addEventListener("click", function () {
      activateTab("chats");
    });

    tasksTab.addEventListener("click", function () {
      activateTab("tasks");
    });
  } else {
    console.error("Tab elements not found");
    setTimeout(setupTabs, 100); // Retry setup
  }
}

function activateTab(tabName) {
  const chatsTab = document.getElementById("chats-tab");
  const tasksTab = document.getElementById("tasks-tab");
  const chatsSection = document.getElementById("chats-section");
  const tasksSection = document.getElementById("tasks-section");

  // Get current context to preserve before switching
  const currentContext = context;

  // Store the current selection for the active tab before switching
  const previousTab = localStorage.getItem("activeTab");
  if (previousTab === "chats") {
    localStorage.setItem("lastSelectedChat", currentContext);
  } else if (previousTab === "tasks") {
    localStorage.setItem("lastSelectedTask", currentContext);
  }

  // Reset all tabs and sections
  chatsTab.classList.remove("active");
  tasksTab.classList.remove("active");
  chatsSection.style.display = "none";
  tasksSection.style.display = "none";

  // Remember the last active tab in localStorage
  localStorage.setItem("activeTab", tabName);

  // Activate selected tab and section
  if (tabName === "chats") {
    chatsTab.classList.add("active");
    chatsSection.style.display = "";

    // Get the available contexts from Alpine.js data
    const chatsAD = globalThis.Alpine ? Alpine.$data(chatsSection) : null;
    const availableContexts = chatsAD?.contexts || [];

    // Restore previous chat selection
    const lastSelectedChat = localStorage.getItem("lastSelectedChat");

    // Only switch if:
    // 1. lastSelectedChat exists AND
    // 2. It's different from current context AND
    // 3. The context actually exists in our contexts list OR there are no contexts yet
    if (
      lastSelectedChat &&
      lastSelectedChat !== currentContext &&
      (availableContexts.some((ctx) => ctx.id === lastSelectedChat) ||
        availableContexts.length === 0)
    ) {
      setContext(lastSelectedChat);
    }
  } else if (tabName === "tasks") {
    tasksTab.classList.add("active");
    tasksSection.style.display = "flex";
    tasksSection.style.flexDirection = "column";

    // Get the available tasks from Alpine.js data
    const tasksAD = globalThis.Alpine ? Alpine.$data(tasksSection) : null;
    const availableTasks = tasksAD?.tasks || [];

    // Restore previous task selection
    const lastSelectedTask = localStorage.getItem("lastSelectedTask");

    // Only switch if:
    // 1. lastSelectedTask exists AND
    // 2. It's different from current context AND
    // 3. The task actually exists in our tasks list
    if (
      lastSelectedTask &&
      lastSelectedTask !== currentContext &&
      availableTasks.some((task) => task.id === lastSelectedTask)
    ) {
      setContext(lastSelectedTask);
    }
  }

  // SSE provides live updates; no legacy poll
}

// Add function to initialize active tab and selections from localStorage
function initializeActiveTab() {
  // Initialize selection storage if not present
  if (!localStorage.getItem("lastSelectedChat")) {
    localStorage.setItem("lastSelectedChat", "");
  }
  if (!localStorage.getItem("lastSelectedTask")) {
    localStorage.setItem("lastSelectedTask", "");
  }

  const activeTab = localStorage.getItem("activeTab") || "chats";
  activateTab(activeTab);
}

// -------- Chats list integration --------
async function refreshChatsList() {
  try {
    const resp = await api.fetchApi('/v1/sessions', { method: 'GET' });
    if (!resp.ok) return;
    const arr = await resp.json().catch(() => []);
    if (!Array.isArray(arr)) return;
    const mapped = arr.map((s, idx) => ({ id: s.session_id || s.id || s.sessionId, name: s.subject || (s.metadata && (s.metadata.title || s.metadata.name)) || '', no: idx + 1 }));
    if (globalThis.Alpine && chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      if (chatsAD) {
        chatsAD.contexts = mapped;
        // Keep selection if present
        if (context) {
          chatsAD.selected = context;
        }
      }
    }
  } catch (e) {
    // benign: silently ignore
  }
}
globalThis.refreshChatsList = refreshChatsList;

// Select a default chat if none currently selected
function ensureDefaultChatSelected() {
  // Run once per page load to avoid accidental periodic session creation
  if (window.__defaultSelectionDone) return;
  if (context && String(context).trim() !== "") { window.__defaultSelectionDone = true; return; }
  if (!(globalThis.Alpine && chatsSection)) return;
  const chatsAD = Alpine.$data(chatsSection);
  const list = Array.isArray(chatsAD?.contexts) ? chatsAD.contexts : [];
  if (list.length === 0) {
    // Do not auto-create a session; leave empty state until user acts
    window.__defaultSelectionDone = true;
    return;
  }
  const last = localStorage.getItem("lastSelectedChat");
  const pick = list.find(c => c.id === last) || list[0];
  if (pick && pick.id) {
    setContext(pick.id, { preserveHistory: true });
  }
  window.__defaultSelectionDone = true;
}

/*
 * A0 Chat UI
 *
 * Tasks tab functionality:
 * - Tasks are displayed in the Tasks tab with the same mechanics as chats
 * - Both lists are sorted by creation time (newest first)
 * - Selection state is preserved across tab switches
 * - The active tab is remembered across sessions
 * - Tasks use the same context system as chats for communication with the backend
 * - Future support for renaming and deletion will be implemented later
 */

// Open the scheduler detail view for a specific task
function openTaskDetail(taskId) {
  // Wait for Alpine.js to be fully loaded
  if (globalThis.Alpine) {
    // Get the settings modal button and click it to ensure all init logic happens
    const settingsButton = document.getElementById("settings");
    if (settingsButton) {
      // Programmatically click the settings button
      settingsButton.click();

      // Now get a reference to the modal element
      const modalEl = document.getElementById("settingsModal");
      if (!modalEl) {
        console.error("Settings modal element not found after clicking button");
        return;
      }

      // Get the Alpine.js data for the modal
      const modalData = globalThis.Alpine ? Alpine.$data(modalEl) : null;

      // Use a timeout to ensure the modal is fully rendered
      setTimeout(() => {
        // Switch to the scheduler tab first
        modalData.switchTab("scheduler");

        // Use another timeout to ensure the scheduler component is initialized
        setTimeout(() => {
          // Get the scheduler component
          const schedulerComponent = document.querySelector(
            '[x-data="schedulerSettings"]'
          );
          if (!schedulerComponent) {
            console.error("Scheduler component not found");
            return;
          }

          // Get the Alpine.js data for the scheduler component
          const schedulerData = globalThis.Alpine
            ? Alpine.$data(schedulerComponent)
            : null;

          // Show the task detail view for the specific task
          schedulerData.showTaskDetail(taskId);

          console.log("Task detail view opened for task:", taskId);
        }, 50); // Give time for the scheduler tab to initialize
      }, 25); // Give time for the modal to render
    } else {
      console.error("Settings button not found");
    }
  } else {
    console.error("Alpine.js not loaded");
  }
}

// Make the function available globally
globalThis.openTaskDetail = openTaskDetail;
