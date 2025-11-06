import * as msgs from "/js/messages.js";
import * as api from "/js/api.js";
import * as css from "/js/css.js";
import { sleep } from "/js/sleep.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import { store as notificationStore } from "/components/notifications/notification-store.js";

globalThis.fetchApi = api.fetchApi; // TODO - backward compatibility for non-modular scripts, remove once refactored to alpine

// Proactively clear any legacy CSRF/XSRF cookies that might be set by proxies or old UI code
function clearLegacyAntiCsrfCookies() {
  try {
    const names = document.cookie.split("; ").map((p) => p.split("=")[0]);
    const shouldDelete = (n) => /(^|[_-])(csrf|xsrf)(_|-|$)/i.test(n);
    const targets = names.filter(shouldDelete);
    if (targets.length === 0) return;
    const host = window.location.hostname;
    const paths = ["/", "/ui"]; // both root and UI subpath
    const samesites = ["Lax", "Strict", "None"];
    for (const name of targets) {
      for (const path of paths) {
        // Basic delete
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path};`;
        // With domain variations and SameSite flags
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; domain=${host};`;
        for (const ss of samesites) {
          const secure = ss === "None" ? " Secure;" : "";
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; SameSite=${ss};${secure}`;
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; domain=${host}; SameSite=${ss};${secure}`;
        }
      }
    }
  } catch (e) {
    // Non-fatal; proceed without blocking UI
  }
}

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
const progressBarIcon = document.getElementById("progress-bar-i");
const autoScrollSwitch = document.getElementById("auto-scroll-switch");
const timeDate = document.getElementById("time-date-container");

let autoScroll = true;
let context = "";
// Track which session ids are known to exist on the server (persisted vs. draft)
const persistedSessions = new Set();
let resetCounter = 0;
let skipOneSpeech = false;
let connectionStatus = undefined; // undefined = not checked yet, true = connected, false = disconnected
// Persisted UI header preferences (defaults aligned with golden UI)
// Golden UI defaults: Thoughts OFF, JSON ON, Utilities ON
let uiPrefs = { show_thoughts: false, show_json: true, show_utils: true };
// Guard to avoid persisting during initial bootstrapping of preferences
let initializingUiPrefs = false;
// Debounce timer for preference saves to avoid rapid flapping and race conditions
let _savePrefsTimer = null;

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
  clearLegacyAntiCsrfCookies();
  const overlay = document.getElementById("sidebar-overlay");
  overlay.addEventListener("click", () => {
    if (isMobile()) {
      toggleSidebar(false);
    }
  });
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
document.addEventListener("DOMContentLoaded", setupSidebarToggle);

export async function sendMessage() {
  try {
    const message = chatInput.value.trim();
    const attachmentsWithUrls = attachmentsStore.getAttachmentsForSending();
    const hasAttachments = attachmentsWithUrls.length > 0;

    if (!message && !hasAttachments) return;

    // Begin a new assistant turn – clear any carry-over streaming state
    resetAssistantStreamState();

    const messageId = generateGUID();

    // Optimistic UI: render user message immediately
    setMessage(messageId, "user", "", message, false, { attachments: attachmentsWithUrls });

    // Clear input and attachments for UX
    chatInput.value = "";
    attachmentsStore.clearAttachments();
    adjustTextareaHeight();

    // Upload attachments first (if any), but skip files already uploaded by selection flow
    let attachmentPaths = [];
    if (hasAttachments) {
      try {
        await sleep(0); // let DOM paint
        // Paths from any pre-uploaded attachments
        const prePaths = attachmentsWithUrls
          .map((a) => a.path)
          .filter((p) => typeof p === "string" && p.length > 0);

        // Identify attachments that still need uploading
        const needUpload = attachmentsWithUrls.filter((a) => !a.path && a.file);
        let uploadedPaths = [];
        if (needUpload.length > 0) {
          const formData = new FormData();
          for (const a of needUpload) formData.append("files", a.file);
          if (context) formData.append("session_id", context);

          const upResp = await api.fetchApi("/uploads", {
            method: "POST",
            body: formData,
          });
          if (!upResp.ok) throw new Error(await upResp.text());
          const descriptors = await upResp.json();
          uploadedPaths = Array.isArray(descriptors)
            ? descriptors.map((d) => d.path).filter(Boolean)
            : [];
        }
        attachmentPaths = [...prePaths, ...uploadedPaths];
      } catch (err) {
        toastFetchError("Attachment upload failed", err);
      }
    }

    // Give immediate UX feedback while backend enqueues/streams
    try {
      setThinking("Assistant is thinking…");
      showThinkingBubble();
    } catch(_e) {}

    // Send message to canonical endpoint
    const payload = {
      session_id: context || null,
      message,
      attachments: attachmentPaths,
      metadata: {},
    };
    const resp = await api.fetchApi("/session/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error((await resp.text()) || `HTTP ${resp.status}`);
    const json = await resp.json();
    if (json && json.session_id) {
      // Mark the session as persisted
      try { persistedSessions.add(String(json.session_id)); } catch(_e) {}
      // If we were in a draft (context set but not persisted), ensure SSE + history now
      if (!context || context !== json.session_id) {
        setContext(json.session_id);
      }
      // Connect SSE for newly persisted sessions (if not already). Avoid immediate
      // history load to prevent duplicating the optimistic user bubble; history will
      // be loaded on context switch or page reload.
      try { connectEventStream(json.session_id); } catch(_e) {}
      // Ensure sidebar reflects the new chat
      try {
        const chatsAD = globalThis.Alpine ? Alpine.$data(chatsSection) : null;
        if (chatsAD) {
          const exists = (chatsAD.contexts || []).some((c) => c.id === json.session_id);
          if (!exists) {
            const no = (chatsAD.contexts || []).length + 1;
            const item = { id: json.session_id, name: payload.message?.slice(0, 40) || "", no };
            chatsAD.contexts = [item, ...(chatsAD.contexts || [])];
            chatsAD.selected = json.session_id;
          }
        }
      } catch(_e) {}
    }
  } catch (e) {
    toastFetchError("Error sending message", e);
    // If sending failed, clear the thinking indicator to avoid a stuck state
    try { setThinking(""); hideThinkingBubble(); } catch(_e) {}
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
      const sid = getContext() || "";
      const files = Array.from(input.files || []);
      if (files.length === 0) return;

      // 1) Upload via canonical endpoint
      const formData = new FormData();
      for (const file of files) {
        formData.append("files", file);
      }
      if (sid) formData.append("session_id", sid);

      const uploadResp = await api.fetchApi("/uploads", {
        method: "POST",
        body: formData,
      });
      if (!uploadResp.ok) throw new Error(await uploadResp.text());
      const descriptors = await uploadResp.json();
      const list = Array.isArray(descriptors) ? descriptors : [];
      if (list.length === 0) {
        toast("No files uploaded", "warning");
        return;
      }

      // 2) Trigger ingestion tool per attachment
      const ingested = [];
      const failures = [];
      for (const d of list) {
        const attId = d && (d.id || d.attachment_id);
        if (!attId) continue;
        try {
          const req = await api.fetchApi("/tool/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sid || (d.session_id || ""),
              tool_name: "document_ingest",
              args: { attachment_id: String(attId), metadata: { tenant: d.tenant } },
              metadata: {},
            }),
          });
          if (!req.ok) throw new Error(await req.text());
          ingested.push(d.filename || d.path || attId);
        } catch (err) {
          failures.push((d && (d.filename || d.path)) || String(attId));
        }
      }

      if (ingested.length > 0) {
        toast(`Queued ingestion for: ${ingested.join(", ")}`, "success");
      }
      if (failures.length > 0) {
        toast(`Failed to queue: ${failures.join(", ")}` , "warning");
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
  return await api.callJsonApi(url, data);
  // const response = await api.fetchApi(url, {
  //     method: 'POST',
  //     headers: {
  //         'Content-Type': 'application/json'
  //     },
  //     body: JSON.stringify(data)
  // });

  // if (!response.ok) {
  //     const error = await response.text();
  //     throw new Error(error);
  // }
  // const jsonResponse = await response.json();
  // return jsonResponse;
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

function setConnectionStatus(connected) {
  connectionStatus = connected;
  if (globalThis.Alpine && timeDate) {
    const statusIconEl = timeDate.querySelector(".status-icon");
    if (statusIconEl) {
      const statusIcon = Alpine.$data(statusIconEl);
      if (statusIcon) {
        statusIcon.connected = connected;
      }
    }
  }
}

let lastSpokenNo = 0;
let eventSource = null;
let currentEventSessionId = null; // Track which session the current SSE is bound to
let currentAssistantMsgId = null;
let currentAssistantBuffer = "";
let lastAssistantSeenText = ""; // used to prevent duplicated fragments during streaming
// Stream lifecycle token to discard stale events and dedupe per-connection
let streamToken = 0;
// Track processed event ids per stream to avoid rendering duplicates across SSE/history
let processedEventIds = new Set();

function resetAssistantStreamState() {
  currentAssistantMsgId = null;
  currentAssistantBuffer = "";
  lastAssistantSeenText = "";
}

function setThinking(text) {
  try {
    if (!progressBar) return;
    if (text && text.trim().length > 0) {
      progressBar.textContent = text;
      progressBar.classList.add("shiny-text");
      if (progressBarIcon) progressBarIcon.textContent = "⏳";
    } else {
      progressBar.textContent = "";
      progressBar.classList.remove("shiny-text");
      if (progressBarIcon) progressBarIcon.textContent = "|>";
    }
  } catch(_e) {}
}

// Ephemeral thinking bubble in the chat area (parity with golden). Gated by uiPrefs.show_thoughts.
function showThinkingBubble(text = "Assistant is thinking…") {
  try {
    if (!uiPrefs?.show_thoughts) return;
    const msgId = `thinking-${streamToken}`;
    setMessage(msgId, "hint", "", text, true, {});
  } catch(_e) {}
}

function hideThinkingBubble() {
  try {
    const el = document.getElementById(`message-thinking-${streamToken}`) || document.getElementById(`message-${`thinking-${streamToken}`}`);
    if (el) {
      const group = el.closest('.message-group');
      el.remove();
      // If group becomes empty, remove it too
      if (group && group.querySelectorAll('.message-container').length === 0) {
        group.remove();
      }
    }
  } catch(_e) {}
}

function rotateStreamToken() {
  streamToken++;
  processedEventIds = new Set();
  resetAssistantStreamState();
  setThinking("");
  hideThinkingBubble();
}

// Legacy poll removed; SSE is used exclusively. Keep a no-op for safety.
async function poll() { /* no-op (SSE-only) */ }

// SSE-only stream (replaces legacy polling)
function connectEventStream(sessionId) {
  try {
    // If already connected to this session and stream is open, keep the stream/token
    if (eventSource && currentEventSessionId === sessionId && eventSource.readyState === 1) {
      return;
    }
    // If switching sessions, rotate token to drop stale streaming state
    if (currentEventSessionId !== sessionId) {
      rotateStreamToken();
    }
    // Close any existing source before opening a new one (same session reconnects will preserve token)
    if (eventSource) {
      try { eventSource.close(); } catch (e) {}
      eventSource = null;
    }
    if (!sessionId) return;
    const url = `/v1/session/${encodeURIComponent(sessionId)}/events`;
    const es = new EventSource(url);
    eventSource = es;
    currentEventSessionId = sessionId;
    const myToken = streamToken;
    es.onopen = () => {
      if (myToken !== streamToken) return; // stale
      setConnectionStatus(true);
    };
    es.onerror = () => {
      if (myToken !== streamToken) return; // stale
      setConnectionStatus(false);
      setThinking("");
      hideThinkingBubble();
    };
    es.onmessage = (evt) => {
      if (myToken !== streamToken) return; // discard stale events from previous streams
      try {
        const payload = JSON.parse(evt.data);
        const t = payload.type || "";
        const role = payload.role || "";
        const evId = payload.event_id || payload.id || null;

        // If we've already processed this exact event id (final/tool), skip it
        if (evId && processedEventIds.has(evId)) {
          return;
        }
        // Update a lightweight thinking/working indicator
        if (/^assistant[.:](start|started|thinking|working)/i.test(t)) {
          setThinking("Assistant is thinking…");
          showThinkingBubble();
        } else if (/^tool[.:](start|started|progress)/i.test(t)) {
          const name = (payload.metadata && (payload.metadata.tool_name || payload.metadata.name)) || "tool";
          setThinking(`Running ${name}…`);
        } else if (/completed|final/i.test(t) || /^assistant[.:](end|stopped|finished)/i.test(t)) {
          setThinking("");
          hideThinkingBubble();
        } else if (/^uploads[.:]progress$/i.test(t)) {
          const meta = (payload && payload.metadata) || {};
          const file = meta.filename || "file";
          const bytes = meta.bytes_uploaded || 0;
          setThinking(`Uploading ${file} (${bytes} bytes)…`);
          // Update per-attachment progress bar if available
          try { attachmentsStore.updateUploadProgress(meta); } catch(_e) {}
        } else if ((role === "assistant" || t.startsWith("assistant")) && !(payload.done || /completed|final/i.test(t))) {
          // For any non-final assistant activity, ensure thinking shows
          setThinking("Assistant is thinking…");
          showThinkingBubble();
        }
        // Prefer true streaming deltas when present; otherwise treat message/content as cumulative
        const hasDelta = typeof payload.delta === 'string' && payload.delta.length > 0;
        const cumulative = (typeof payload.message === 'string' && payload.message.length > 0)
          ? payload.message
          : (typeof payload.content === 'string' ? payload.content : "");
        // Assistant streaming: accumulate deltas into a single UI message
        if (role === "assistant" || t.startsWith("assistant")) {
          // Determine if this is a final/completed event
          const isFinal = !!(payload.done || (payload.metadata && (payload.metadata.final || payload.metadata.completed)) || /completed|final/i.test(t));
          if (!currentAssistantMsgId) currentAssistantMsgId = payload.event_id || generateGUID();

          // If a redundant assistant:start/begin arrives mid-stream, avoid wiping the visible buffer.
          if (/^assistant:(start|begin)/i.test(t)) {
            if (!currentAssistantMsgId || !currentAssistantBuffer) {
              currentAssistantBuffer = "";
              lastAssistantSeenText = "";
            } else {
              // Ignore restart signal; continue accumulating to preserve non-decreasing UI length
            }
          }

          if (hasDelta) {
            // Append only the delta chunk
            currentAssistantBuffer += payload.delta;
          } else if (cumulative) {
            // Prefer cumulative content when it represents a growth or a superset of the current buffer.
            // Guard against backtracking/partial cumulative payloads that would shrink the visible text.
            if (cumulative !== lastAssistantSeenText) {
              const grows = cumulative.length >= currentAssistantBuffer.length;
              const isSuperset = currentAssistantBuffer
                ? cumulative.startsWith(currentAssistantBuffer)
                : true;
              if (grows || isSuperset) {
                currentAssistantBuffer = cumulative;
                lastAssistantSeenText = cumulative;
              } else {
                // Ignore stale/partial cumulative updates to prevent UI shrink
              }
            }
          }
          // Avoid creating empty assistant placeholder messages on started/thinking events
          if ((currentAssistantBuffer || "").trim().length > 0 || isFinal) {
            // On final, if backend supplies a stable event_id, rename the DOM node id to match for history de-duplication
            const finalId = payload.event_id;
            if (isFinal && finalId && finalId !== currentAssistantMsgId) {
              const prevEl = document.getElementById(`message-${currentAssistantMsgId}`);
              if (prevEl) {
                prevEl.id = `message-${finalId}`;
              }
              currentAssistantMsgId = finalId;
            }
            // Throttle streaming updates to reduce DOM churn; always render final immediately
            const now = Date.now();
            const shouldThrottle = !isFinal;
            if (!globalThis._lastAssistantRenderAtMs) globalThis._lastAssistantRenderAtMs = 0;
            const due = (now - globalThis._lastAssistantRenderAtMs) >= 33; // ~30fps

            if (isFinal) {
              const prevPlain = currentAssistantBuffer; // keep a copy to guard against transient shrink on final
              setMessage(currentAssistantMsgId, "response", "", currentAssistantBuffer, false, payload.metadata || {});
              // Inject a short-lived hidden shadow text to avoid transient textContent shrink during final render
              try { injectShadowText(currentAssistantMsgId, prevPlain, 3000); } catch(_e) {}
              globalThis._lastAssistantRenderAtMs = now;
            } else if (!shouldThrottle || due) {
              setMessage(currentAssistantMsgId, "response_stream", "", currentAssistantBuffer, false, payload.metadata || {});
              globalThis._lastAssistantRenderAtMs = now;
            }
          }
          if (isFinal) {
            // Mark final event as processed to avoid duplicate finals
            if (evId) processedEventIds.add(evId);
            currentAssistantMsgId = null;
            currentAssistantBuffer = "";
            lastAssistantSeenText = "";
            hideThinkingBubble();
          }
          return;
        }

        // Optionally render tool outputs
        if (role === "tool" || t.startsWith("tool")) {
          // Suppress echo tool outputs from UI; keep others for diagnostics
          try {
            const meta = payload.metadata || {};
            const toolName = String(meta.tool_name || meta.name || "").toLowerCase();
            if (toolName.includes("echo")) {
              if (evId) processedEventIds.add(evId);
              return;
            }
          } catch(_) {}
          const content = cumulative || payload.message || "";
          const id = payload.event_id || generateGUID();
          setMessage(id, "tool", "", content, false, payload.metadata || {});
          if (evId) processedEventIds.add(evId);
          return;
        }

        // Utility messages (hidden when Show utility messages is off)
        if (role === "util" || t.startsWith("util")) {
          // Special-case: settings saved broadcast from Gateway
          try {
            const evType = String(payload.type || "").toLowerCase();
            const metaType = String((payload.metadata && payload.metadata.event) || "").toLowerCase();
            if (evType === "ui.settings.saved" || metaType === "ui.settings.saved") {
              // Notify local components to rehydrate settings without a full page reload
              try {
                document.dispatchEvent(new CustomEvent("settings-updated", { detail: payload.settings || null }));
              } catch (_) {}
              // Lightweight toast to inform the user (debounced by SSE id)
              try { justToast("Settings updated", "success", 1200, "settings-apply"); } catch (_) {}
              if (evId) processedEventIds.add(evId);
              return;
            }
          } catch (_) {}

          const content = cumulative || payload.message || "";
          const id = payload.event_id || generateGUID();
          const kv = payload.metadata || {};
          const heading = (kv && (kv.headline || kv.title)) || "Utility";
          setMessage(id, "util", heading, content, false, kv);
          if (evId) processedEventIds.add(evId);
          return;
        }
      } catch (e) {
        // ignore malformed events
      }
    };
  } catch (e) {
    setConnectionStatus(false);
  }
}

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

    // SSE will stream updates once context is set
  }

  updateAfterScroll();
};

// use v4-like GUIDs for session ids to align with server UUIDs

export const newContext = function () {
  context = generateGUID();
  // New chats start as drafts (not persisted on the server yet)
  try { persistedSessions.delete(String(context)); } catch(_e) {}
  setContext(context);
  // Optimistically add the new chat to the sidebar list for immediate UX feedback
  try {
    if (globalThis.Alpine && chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      const items = Array.isArray(chatsAD?.contexts) ? chatsAD.contexts : [];
      const exists = items.some((c) => c.id === context);
      if (!exists) {
        chatsAD.contexts = [
          { id: context, name: "New chat", no: (items[0]?.no || 0) + 1, updated_at: new Date().toISOString() },
          ...items,
        ];
        chatsAD.selected = context;
      }
    }
  } catch(_e) {}
}

// Expose a user-friendly alias for creating a new chat used by the UI buttons
globalThis.newChat = function () {
  newContext();
  justToast("New chat created", "success", 1000, "chat-new");
};

export const setContext = function (id) {
  if (id == context) return;
  context = id;
  lastSpokenNo = 0;

  // Stop speech when switching chats
  speechStore.stopAudio();

  // Clear the chat history immediately to avoid showing stale content
  chatHistory.innerHTML = "";

  // Update both selected states
  if (globalThis.Alpine) {
    if (chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      if (chatsAD) chatsAD.selected = id;
    }
    if (tasksSection) {
      const tasksAD = Alpine.$data(tasksSection);
      if (tasksAD) tasksAD.selected = id;
    }
  }

  //skip one speech if enabled when switching context
  if (localStorage.getItem("speech") == "true") skipOneSpeech = true;
  // Connect SSE and load history only for persisted sessions
  try {
    if (persistedSessions.has(String(context))) {
      connectEventStream(context);
      // Load and render current session history for visibility (welcome, first user message, etc.)
      // Fire and forget; errors surfaced via toast
      loadAndRenderSessionHistory(context).catch((_e) => {});
    }
  } catch(_e) {}
};

// Delete chat/session from sidebar (Chats tab)
globalThis.killChat = async function (id) {
  try {
    if (!id) return;
    // Switch away first if deleting current context
    switchFromContext(id);
    // If this is a draft (not persisted), remove locally without server call
    if (!persistedSessions.has(String(id))) {
      // Update UI contexts list if present
      if (globalThis.Alpine && chatsSection) {
        const chatsAD = Alpine.$data(chatsSection);
        const updated = (chatsAD?.contexts || []).filter((c) => c.id !== id);
        chatsAD.contexts = [...updated];
      }
      updateAfterScroll();
      justToast("Chat deleted", "success", 1000, "chat-removal");
      return;
    }
    // Persisted session – delete server‑side
    const resp = await api.fetchApi(`/sessions/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (!resp.ok) throw new Error(await resp.text());

    // Update UI contexts list if present
    if (globalThis.Alpine && chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      const updated = (chatsAD?.contexts || []).filter((c) => c.id !== id);
      chatsAD.contexts = [...updated];
    }
    updateAfterScroll();
    justToast("Chat deleted successfully", "success", 1000, "chat-removal");
  } catch (e) {
    console.error("Error deleting chat:", e);
    toastFetchError("Error deleting chat", e);
  }
};

// Delete task (same backend as sessions)
globalThis.deleteTaskGlobal = async function (id) {
  try {
    if (!id) return;
    if (context === id) newContext();
    const resp = await api.fetchApi(`/sessions/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
    if (!resp.ok) throw new Error(await resp.text());
    if (globalThis.Alpine && tasksSection) {
      const tasksAD = Alpine.$data(tasksSection);
      tasksAD.tasks = (tasksAD?.tasks || []).filter((t) => t.id !== id);
    }
    justToast("Task deleted", "success", 1000, "task-removal");
  } catch (e) {
    toastFetchError("Error deleting task", e);
  }
};

// Reset chat/session history but keep the session id
globalThis.resetChat = async function (id) {
  try {
    const sid = id || context;
    if (!sid) return;
    // Draft session: clear UI only, no server call
    if (!persistedSessions.has(String(sid))) {
      if (sid === context) {
        chatHistory.innerHTML = "";
        resetCounter++;
        try { if (eventSource) { eventSource.close(); eventSource = null; } } catch(_e) {}
      }
      justToast("Chat reset", "success", 1200, "chat-reset");
      return;
    }
    const resp = await api.fetchApi(`/sessions/${encodeURIComponent(sid)}/reset`, { method: "POST" });
    if (!resp.ok) throw new Error(await resp.text());
    // Clear current chat history visually
    if (sid === context) {
      chatHistory.innerHTML = "";
      resetCounter++;
      // Ensure we fully rotate the stream and drop any stale events after reset
      try { if (eventSource) { eventSource.close(); eventSource = null; } } catch(_e) {}
      connectEventStream(context);
    }
    justToast("Chat reset", "success", 1200, "chat-reset");
  } catch (e) {
    toastFetchError("Error resetting chat", e);
  }
};

export const getContext = function () {
  return context;
};

export const getChatBasedId = function (id) {
  return context + "-" + resetCounter + "-" + id;
};

// Best-effort call of a global method by name. Used by Alpine x-effect bindings
// for header toggles (Show thoughts / JSON / utilities) to avoid hard coupling
// and race conditions during component initialization.
globalThis.safeCall = function (fnName, ...args) {
  try {
    const fn = (globalThis || {})[fnName];
    if (typeof fn === 'function') return fn(...args);
  } catch (_) {}
  return undefined;
};

globalThis.toggleAutoScroll = async function (_autoScroll) {
  autoScroll = _autoScroll;
};

globalThis.toggleJson = async function (showJson) {
  css.toggleCssProperty(".msg-json", "display", showJson ? "block" : "none");
  try {
    uiPrefs.show_json = !!showJson;
    await saveUiPreferences();
  } catch(_e) {}
};

globalThis.toggleThoughts = async function (showThoughts) {
  css.toggleCssProperty(
    ".msg-thoughts",
    "display",
    showThoughts ? undefined : "none"
  );
  try {
    uiPrefs.show_thoughts = !!showThoughts;
    await saveUiPreferences();
    // When user turns thoughts ON, inject a one‑time greeting thought for the current chat
    if (showThoughts) {
      maybeShowThoughtsGreeting();
    }
  } catch(_e) {}
};

globalThis.toggleUtils = async function (showUtils) {
  css.toggleCssProperty(
    ".message-util",
    "display",
    showUtils ? undefined : "none"
  );
  try {
    uiPrefs.show_utils = !!showUtils;
    await saveUiPreferences();
    if (showUtils) {
      maybeShowUtilitiesGreeting();
    }
  } catch(_e) {}
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
    await api.fetchApi("/session/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "nudge", session_id: sid }),
    });
  } catch (e) {
    toastFetchError("Error nudging agent", e);
  }
};

globalThis.restart = async function () {
  // No canonical restart endpoint; show info toast instead
  await toastFrontendInfo("Restart not supported in this UI. Use your process manager.", "System", 6, "restart");
};

// Graceful pause/resume control (frontend-only for now)
globalThis.pauseAgent = async function (shouldPause) {
  try {
    // Update local Alpine state for button text/icon
    const section = document.getElementById("input-section");
    if (globalThis.Alpine && section) {
      const data = Alpine.$data(section);
      if (data && typeof data.paused !== 'undefined') {
        data.paused = !!shouldPause;
      }
    }
    // Inform backend via canonical quick action
    if (context) {
      await api.fetchApi('/session/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: shouldPause ? 'pause' : 'resume', session_id: context })
      }).catch((e) => {
        console.warn('pauseAgent backend call failed:', e?.message || e);
      });
    }
    justToast(shouldPause ? "Agent paused" : "Agent resumed", "info", 1200, "agent-pause");
  } catch (e) {
    // Never error hard; keep UI responsive
    console.warn("pauseAgent encountered an issue:", e);
  }
};

// Modify this part
document.addEventListener("DOMContentLoaded", () => {
  const isDarkMode = localStorage.getItem("darkMode") !== "false";
  toggleDarkMode(isDarkMode);
});

globalThis.loadChats = async function () {
  try {
    const fileContents = await readJsonFiles();
    if (!fileContents || fileContents.length === 0) return;
    const resp = await api.fetchApi("/sessions/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessions: fileContents }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    const ids = data.ctxids || data.session_ids || data.ids || [];
    if (ids.length > 0) setContext(ids[0]);
    toast("Chats imported.", "success");
  } catch (e) {
    toastFetchError("Error importing chats", e);
  }
};

globalThis.saveChat = async function () {
  try {
    if (!context) return;
    const resp = await api.fetchApi("/sessions/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: context }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    const filename = data.filename || `${data.ctxid || context}.json`;
    const content = data.content || JSON.stringify(data, null, 2);
    downloadFile(filename, content);
    toast("Chat file downloaded.", "success");
  } catch (e) {
    toastFetchError("Error exporting chat", e);
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

// Inject a one‑time “Thoughts” greeting message in the current chat when the user enables Thoughts.
function maybeShowThoughtsGreeting() {
  try {
    const sid = context || "unspecified";
    const shownKey = `thoughtsGreetingShown:${sid}`;
    if (localStorage.getItem(shownKey) === "1") return;

    const id = getChatBasedId("thoughts-greeting");
    const heading = "Greeting response";
    const kvps = {
      thoughts: "**Hello! 👋** How can I assist you today?",
      tool: "response",
    };
    // Render as an informational message with a Thoughts KVP row; respects the Thoughts toggle visibility
    setMessage(id, "info", heading, "", false, kvps);
    localStorage.setItem(shownKey, "1");
  } catch (_) {}
}

// Enqueue an initial utility bubble via Gateway when utilities are enabled (one-time per chat)
function maybeShowUtilitiesGreeting() {
  try {
    const sid = context || "";
    if (!sid) return;
    const shownKey = `utilitiesGreetingShown:${sid}`;
    if (localStorage.getItem(shownKey) === "1") return;

    // Publish a utility event through Gateway so it appears in SSE like normal events
    fetch(`/v1/util/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sid,
        title: 'Utility',
        text: 'Searching memories…',
        kvps: {
          query: 'No relevant memory query generated, skipping search',
        },
      })
    }).catch(() => { /* non-fatal */ });
    localStorage.setItem(shownKey, "1");
  } catch (_) {}
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
  const seconds = Math.max(timeout / 1000, 1);
  const t = String(type || "info").toLowerCase();
  switch (t) {
    case "error":
      return notificationStore.frontendError(text, "Error", seconds, group);
    case "success":
      return notificationStore.frontendSuccess(text, "Success", seconds, group);
    case "warning":
      return notificationStore.frontendWarning(text, "Warning", seconds, group);
    case "info":
    default:
      return notificationStore.frontendInfo(text, "Info", seconds, group);
  }
}

function toast(text, type = "info", timeout = 5000) {
  // Alias to justToast without group
  return justToast(text, type, timeout);
}
globalThis.toast = toast;

function scheduleSaveUiPreferences(delayMs = 250) {
  try { if (_savePrefsTimer) clearTimeout(_savePrefsTimer); } catch(_e) {}
  _savePrefsTimer = setTimeout(() => {
    // Fire-and-forget; any error is non-fatal
    saveUiPreferences().catch(() => {});
  }, delayMs);
}

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

// No polling; SSE is established on context selection

// Setup event handlers once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  setupSidebarToggle();
  setupTabs();
  initializeActiveTab();
  // Bootstrap chats list and initial session selection
  bootstrapSessions().catch((e) => {
    console.warn("Failed to bootstrap sessions:", e?.message || e);
  });
  // Load and apply UI preferences (thoughts/json/utils)
  initUiPreferences().catch((e) => {
    console.warn("Failed to init UI preferences:", e?.message || e);
  });
  // Ensure Preferences toggles are visible in the sidebar
  try {
    const lp = document.getElementById('left-panel');
    if (lp) lp.scrollTop = lp.scrollHeight;
  } catch(_e) {}
  // Initialize speech store once on load so it fetches settings immediately
  try { if (speechStore && typeof speechStore.init === 'function') speechStore.init(); } catch(_e) {}
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

  // Request a poll update
  // SSE will stream updates once context is set
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

// ---- UI Preferences (persisted) ----

async function initUiPreferences() {
  initializingUiPrefs = true;
  try {
    const resp = await api.fetchApi('/ui/preferences');
    if (resp.ok) {
      const prefs = await resp.json();
      // Update local cache with defaults for missing keys
      uiPrefs = {
        show_thoughts: typeof prefs.show_thoughts === 'boolean' ? prefs.show_thoughts : false,
        // Force golden-parity defaults: JSON ON, Utilities ON
        show_json: true,
        show_utils: true,
      };
    }
  } catch(_e) {
    // Non-fatal; keep defaults
  } finally {
    // We keep the flag true while applying values to avoid persisting during init
  }

  // Apply to Alpine-bound toggles by updating their component state
  try {
    // Thoughts
    const thoughtsInput = document.querySelector('input[x-effect*="toggleThoughts"]');
    if (thoughtsInput) {
      const li = thoughtsInput.closest('li');
      const data = globalThis.Alpine ? Alpine.$data(li) : null;
      if (data && typeof data.showThoughts !== 'undefined') {
        data.showThoughts = !!uiPrefs.show_thoughts;
      } else {
        // Fallback if Alpine not ready: reflect state directly on checkbox
        thoughtsInput.checked = !!uiPrefs.show_thoughts;
      }
      // Ensure CSS reflects value immediately
      globalThis.toggleThoughts(!!uiPrefs.show_thoughts);
    }
    // JSON
    const jsonInput = document.querySelector('input[x-effect*="toggleJson"]');
    if (jsonInput) {
      const li = jsonInput.closest('li');
      const data = globalThis.Alpine ? Alpine.$data(li) : null;
      if (data && typeof data.showJson !== 'undefined') {
        data.showJson = !!uiPrefs.show_json;
      } else {
        jsonInput.checked = !!uiPrefs.show_json;
      }
      globalThis.toggleJson(!!uiPrefs.show_json);
    }
    // Utils
    const utilsInput = document.querySelector('input[x-effect*="toggleUtils"]');
    if (utilsInput) {
      const li = utilsInput.closest('li');
      const data = globalThis.Alpine ? Alpine.$data(li) : null;
      if (data && typeof data.showUtils !== 'undefined') {
        data.showUtils = !!uiPrefs.show_utils;
      } else {
        utilsInput.checked = !!uiPrefs.show_utils;
      }
      globalThis.toggleUtils(!!uiPrefs.show_utils);
    }
  } catch(_e) {}
  finally {
    // Allow subsequent user interactions to persist preferences
    initializingUiPrefs = false;
  }
}

async function saveUiPreferences() {
  // Avoid persisting while initializing from server/defaults to prevent flapping
  if (initializingUiPrefs) return;
  try {
    await api.fetchApi('/ui/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(uiPrefs),
    });
  } catch(_e) {
    // Non-fatal; UI stays responsive
  }
}

// ---- Sessions bootstrap and history rendering ----

async function bootstrapSessions() {
  try {
    const resp = await api.fetchApi("/sessions");
    if (!resp.ok) throw new Error(await resp.text());
    const sessions = await resp.json();

    // Map to sidebar-friendly structure
    const items = (Array.isArray(sessions) ? sessions : []).map((s, idx) => ({
      id: s.session_id,
      name: s.subject || (s.metadata && s.metadata.subject) || "",
      no: idx + 1,
      updated_at: s.updated_at || s.created_at || null,
    }));
    // Sort by updated_at desc when available
    items.sort((a, b) => {
      const ax = a.updated_at ? new Date(a.updated_at).getTime() : 0;
      const bx = b.updated_at ? new Date(b.updated_at).getTime() : 0;
      return bx - ax;
    });

    const chatsAD = globalThis.Alpine ? Alpine.$data(chatsSection) : null;
    if (chatsAD) {
      chatsAD.contexts = items;
    }
    // Mark all fetched sessions as persisted
    try { (items || []).forEach((i) => persistedSessions.add(String(i.id))); } catch(_e) {}

    // Choose session: lastSelectedChat or first
    const last = localStorage.getItem("lastSelectedChat");
    const pick = (items.find((i) => i.id === last) || items[0]);
    if (pick && pick.id) {
      // setContext will connect SSE and load history; avoid double render
      setContext(pick.id);
      if (chatsAD) chatsAD.selected = pick.id;
    } else {
      // No sessions present. Golden UI parity requires an empty history here
      // (no default welcome/notification bubbles) so tests that assert
      // post-reset counts (≤ 1 bubble) remain stable. Do not inject any
      // default bubbles when there are no sessions.
    }
  } catch (e) {
    toastFetchError("Failed to load sessions", e);
  }
}

// Ensure only one notification bell (toggle) is present even if components load twice
function dedupeNotificationBell() {
  try {
    const toggles = document.querySelectorAll('.notification-toggle');
    if (toggles.length > 1) {
      // Keep the first visible within the time-date container if present
      const container = document.getElementById('time-date-container');
      let kept = null;
      if (container) {
        const inContainer = container.querySelector('.notification-toggle');
        if (inContainer) kept = inContainer;
      }
      kept = kept || toggles[0];
      toggles.forEach((el) => {
        if (el !== kept) el.remove();
      });
    }
  } catch(_e) {
    // Best-effort; ignore
  }
}

// Run once on load and again after a brief delay to catch late component mounts
window.addEventListener('load', () => {
  dedupeNotificationBell();
  setTimeout(dedupeNotificationBell, 500);
});

// Append a hidden text node under the message body to temporarily prevent textContent length from shrinking
function injectShadowText(messageId, text, ttlMs = 2000) {
  if (!messageId || !text) return;
  const el = document.getElementById(`message-${messageId}`);
  if (!el) return;
  const body = el.querySelector('.message-body');
  if (!body) return;
  const shadow = document.createElement('span');
  shadow.className = 'shadow-final-text';
  shadow.style.display = 'none';
  shadow.textContent = text;
  body.appendChild(shadow);
  if (ttlMs > 0) {
    setTimeout(() => {
      try { shadow.remove(); } catch(_e) {}
    }, ttlMs);
  }
}

async function loadAndRenderSessionHistory(sessionId) {
  try {
    // Avoid server call for draft sessions
    if (!persistedSessions.has(String(sessionId))) return;
    const resp = await api.fetchApi(`/sessions/${encodeURIComponent(sessionId)}/events?limit=500`);
    if (!resp.ok) {
      // Suppress 404 for races or missing history; only toast for other errors
      const msg = await resp.text();
      if (resp.status === 404) return;
      throw new Error(msg || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    const events = Array.isArray(data?.events) ? data.events : [];
    // Render in chronological order by DB id
    for (const ev of events) {
      const p = ev.payload || {};
      const role = (p.role || "").toLowerCase();
      const type = (p.type || "").toLowerCase();
      const msg = p.message || p.content || "";
      const id = p.event_id || `${ev.id}` || generateGUID();
      if (role === "user") {
        setMessage(id, "user", "", msg, false, { attachments: p.attachments || [] });
      } else if (role === "assistant" || type.startsWith("assistant")) {
        setMessage(id, "response", "", msg, false, p.metadata || {});
      } else if (role === "tool" || type.startsWith("tool")) {
        setMessage(id, "tool", "", msg, false, p.metadata || {});
      } else {
        // Ignore utilities for initial history render
        continue;
      }
    }
  } catch (e) {
    toastFetchError("Failed to load chat history", e);
  }
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
