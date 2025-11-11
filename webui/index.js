import * as msgs from "/js/messages.js";
import * as api from "/js/api.js";
import * as css from "/js/css.js";
import * as bus from "/js/event-bus.js";
import * as stream from "/js/stream.js";
import { sleep } from "/js/sleep.js";
import { store as attachmentsStore } from "/components/chat/attachments/attachmentsStore.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
// Legacy notification store (toast + polling-era compatibility)
// Consolidated SSE + REST notifications store (legacy polling/ toast removed)
import { store as notificationsSseStore } from "/components/notifications/notificationsStore.js";
import { createStore as createAlpineStore } from "/js/AlpineStore.js";

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
    const hasLocalAttachments = (attachmentsStore.attachments || []).length > 0;

    if (message || hasLocalAttachments) {
      let response;
      const messageId = generateGUID();

      // Clear input immediately (keep attachments until uploaded)
      chatInput.value = "";
      adjustTextareaHeight();

      // Render the user message immediately (attachments will appear as uploaded)
      setMessage(messageId, "user", null, message, false, null);

      // If we have local attachments, upload them first to /v1/uploads
      let attachmentIds = [];
      if (hasLocalAttachments) {
        try {
          await sleep(0); // one frame for UX
          const descriptors = await attachmentsStore.uploadAll(context);
          attachmentIds = (descriptors || []).map(d => d.id);
        } catch (e) {
          toastFetchError("Attachment upload failed", e);
          // proceed with message without attachments
        }
      }

      // Enqueue the message via canonical endpoint
      const payload = {
        session_id: context || null,
        persona_id: null,
        message,
        attachments: attachmentIds,
        metadata: {},
      };
      response = await api.fetchApi("/v1/session/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const txt = await response.text();
        throw new Error(txt || "Failed to enqueue message");
      }
      const json = await response.json();
      if (json?.session_id) setContext(json.session_id);
      // Clear attachments only after we attempted to send
      attachmentsStore.clearAttachments();
    }
  } catch (e) {
    toastFetchError("Error sending message", e); // Will use new notification system
  }
}

function toastFetchError(text, error) {
  console.error(text, error);
  const errorMessage = error?.message || error?.toString() || "Unknown error";
  // Emit an SSE-style notification creation; fallback to console only
  try {
    notificationsSseStore.create({ type: "error", title: text, body: errorMessage, severity: "error", ttl_seconds: 8 });
  } catch {}
}
globalThis.toastFetchError = toastFetchError;

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) {
    e.preventDefault();
    if (!getConnectionStatus()) {
      stream.requestReconnect();
    }
    sendMessage();
  }
});

sendButton.addEventListener("click", () => {
  if (!getConnectionStatus()) {
    stream.requestReconnect();
  }
  sendMessage();
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
  try {
    if (globalThis.Alpine?.store && globalThis.Alpine.store('conn')) {
      const s = globalThis.Alpine.store('conn');
      s.status = connected ? 'online' : 'offline';
      s.tooltip = connected ? 'Online' : 'Offline';
    }
  } catch {}
}

let lastLogVersion = 0;
let lastLogGuid = "";
let lastSpokenNo = 0;

// --- SSE integration (replaces legacy polling) ---
let currentAssistantId = null;
let assistantBuffer = "";

// Subscribe to stream lifecycle & events
bus.on("stream.online", () => {
  setConnectionStatus(true);
  try { const s = globalThis.Alpine?.store && globalThis.Alpine.store('conn'); if (s) { s.status = 'online'; s.tooltip = 'Online'; } } catch {}
  try { notificationsSseStore.create({ type: "system", title: "Connected", body: "Streaming online", severity: "success", ttl_seconds: 3 }); } catch {}
});
bus.on("stream.offline", (info) => {
  setConnectionStatus(false);
  try { const s = globalThis.Alpine?.store && globalThis.Alpine.store('conn'); if (s) { s.status = 'offline'; s.tooltip = info?.reason ? `Offline — ${info.reason}` : 'Offline'; } } catch {}
  try { notificationsSseStore.create({ type: "system", title: "Disconnected", body: "Backend stream offline", severity: "warning", ttl_seconds: 15 }); } catch {}
});
bus.on("stream.stale", (info) => {
  try { const s = globalThis.Alpine?.store && globalThis.Alpine.store('conn'); if (s) { s.status = 'stale'; const secs = Math.max(1, Math.round((info?.ms_since_heartbeat || 0)/1000)); s.tooltip = `Stale — ${secs}s since last heartbeat`; } } catch {}
});
bus.on("stream.reconnecting", (info) => {
  try { const s = globalThis.Alpine?.store && globalThis.Alpine.store('conn'); if (s) { s.status = 'reconnecting'; const attempt = info?.attempt || 1; const delayMs = info?.delay || 0; s.tooltip = `Reconnecting (attempt ${attempt}, ${Math.round(delayMs)}ms)`; } } catch {}
  try { notificationsSseStore.create({ type: "system", title: "Reconnecting", body: `Attempt ${info.attempt || 1}`, severity: "info", ttl_seconds: 4 }); } catch {}
});
bus.on("stream.retry.success", (info) => {
  try { const s = globalThis.Alpine?.store && globalThis.Alpine.store('conn'); if (s) { s.status = 'online'; s.tooltip = `Reconnected after ${info?.attempt || 1} attempts`; } } catch {}
});
bus.on("stream.retry.giveup", (info) => {
  try { const s = globalThis.Alpine?.store && globalThis.Alpine.store('conn'); if (s) { s.status = 'offline'; s.tooltip = `Reconnection paused after ${info?.attempt || 1} attempts`; } } catch {}
});
bus.on("sse:event", (ev) => {
  if (ev && (!ev.session_id || ev.session_id === context)) {
    renderEvent(ev);
  }
});

function mapEventToUi(ev) {
  const t = (ev.type || "").toLowerCase();
  const role = (ev.role || "").toLowerCase();
  if (t === "assistant.delta" || t === "assistant.final" || role === "assistant") return "response";
  if (role === "user") return "user";
  if (role === "tool" || t.startsWith("tool")) return "tool";
  if (t.endsWith(".error")) return "error";
  return "agent";
}

function renderEvent(ev) {
  try {
    const uiType = mapEventToUi(ev);
    if (ev.type === "system.keepalive") return;

    if (uiType === "response") {
      if ((ev.type || "").toLowerCase() === "assistant.delta") {
        if (!currentAssistantId) currentAssistantId = generateGUID();
        assistantBuffer = (assistantBuffer || "") + (ev.message || "");
        setMessage(currentAssistantId, "response", null, assistantBuffer, true, ev.metadata || null);
      } else {
        // final or other assistant events
        if (!currentAssistantId) currentAssistantId = generateGUID();
        const content = (assistantBuffer || "") + (ev.message || "");
        const md = Object.assign({}, ev.metadata || {}, { finished: true });
        setMessage(currentAssistantId, "response", null, content, false, md);
        afterMessagesUpdate([{ no: Date.now(), type: "response", kvps: md }]);
        currentAssistantId = null;
        assistantBuffer = "";
      }
      return;
    }

    // For user/tool/agent/error
    const id = ev.event_id || generateGUID();
    const heading = (ev.metadata && (ev.metadata.subject || ev.metadata.tool_name)) || null;
    const content = ev.message || (ev.metadata ? JSON.stringify(ev.metadata, null, 2) : "");
    setMessage(id, uiType, heading, content, false, ev.metadata || null);
  } catch (e) {
    console.error("Failed to render SSE event", e, ev);
  }
}

async function fetchSessionsAndPopulate() {
  try {
    const resp = await fetch("/v1/sessions", { credentials: "same-origin" });
    if (!resp.ok) return;
    const sessions = await resp.json();
    if (globalThis.Alpine && chatsSection) {
      const chatsAD = Alpine.$data(chatsSection);
      if (chatsAD) {
        chatsAD.contexts = (sessions || []).map((s) => ({ id: s.session_id, name: s.subject || s.session_id, created_at: new Date(s.created_at || Date.now()).getTime() }));
      }
    }
    // Select first session if none selected
    if (!context && sessions && sessions.length) {
      setContext(sessions[0].session_id);
    }
  } catch (e) {
    console.warn("Failed to load sessions list", e);
  }
}

async function loadHistory(sessionId) {
  try {
    if (!sessionId) return;
    const resp = await fetch(`/v1/sessions/${encodeURIComponent(sessionId)}/history`, { credentials: "same-origin" });
    if (!resp.ok) return;
    const data = await resp.json();
    // data may be { events: [ { payload: {...} } ] }
    const rows = Array.isArray(data?.events) ? data.events : [];
    chatHistory.innerHTML = "";
    rows.forEach((row) => {
      const ev = row?.payload || row || {};
      renderEvent(ev);
    });
  } catch (e) {
    console.warn("Failed to load session history", e);
  }
}

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
    const resp = await sendJsonData("/pause", { paused: paused, context });
  } catch (e) {
    globalThis.toastFetchError("Error pausing agent", e);
  }
};

globalThis.resetChat = async function (ctxid = null) {
  try {
    const resp = await sendJsonData("/chat_reset", {
      context: ctxid === null ? context : ctxid,
    });
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
    await sendJsonData("/chat_remove", { context: id });

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

    // Hydrate and connect SSE for this selection
    stream.stop();
    loadHistory(id).then(() => stream.start(id));
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
}

export const setContext = function (id) {
  if (id == context) return;
  context = id;
  // Always reset the log tracking variables when switching contexts
  // This ensures we get fresh data from the backend
  lastLogGuid = "";
  lastLogVersion = 0;
  lastSpokenNo = 0;

  // Stop speech when switching chats
  speechStore.stopAudio();

  // Clear the chat history immediately to avoid showing stale content
  chatHistory.innerHTML = "";

  // Bind SSE to the new context and hydrate from history
  stream.stop();
  loadHistory(context).then(() => stream.start(context));

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
    const resp = await sendJsonData("/nudge", { ctxid: getContext() });
  } catch (e) {
    toastFetchError("Error nudging agent", e);
  }
};

globalThis.restart = async function () {
  try {
    if (!getConnectionStatus()) {
      await toastFrontendError(
        "Backend disconnected, cannot restart.",
        "Restart Error"
      );
      return;
    }
    // First try to initiate restart
    const resp = await sendJsonData("/restart", {});
  } catch (e) {
    // Show restarting message with no timeout and restart group
    await toastFrontendInfo("Restarting...", "System Restart", 9999, "restart");

    let retries = 0;
    const maxRetries = 240; // Maximum number of retries (60 seconds with 250ms interval)

    while (retries < maxRetries) {
      try {
        const resp = await sendJsonData("/health", {});
        // Server is back up, show success message that replaces the restarting message
        await new Promise((resolve) => setTimeout(resolve, 250));
        await toastFrontendSuccess("Restarted", "System Restart", 5, "restart");
        return;
      } catch (e) {
        // Server still down, keep waiting
        retries++;
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
    }

    // If we get here, restart failed or took too long
    await toastFrontendError(
      "Restart timed out or failed",
      "Restart Error",
      8,
      "restart"
    );
  }
};

// Modify this part
document.addEventListener("DOMContentLoaded", () => {
  const isDarkMode = localStorage.getItem("darkMode") !== "false";
  toggleDarkMode(isDarkMode);
  // Initialize and subscribe SSE notifications store once DOM ready
  try {
    if (!globalThis.Alpine) {
      document.addEventListener("alpine:init", () => {
        notificationsSseStore.subscribe();
        notificationsSseStore.fetchList({ limit: 25 }).catch(()=>{});
      }, { once: true });
    } else {
      notificationsSseStore.subscribe();
      notificationsSseStore.fetchList({ limit: 25 }).catch(()=>{});
    }
    // Expose for debugging
    globalThis.notificationsSse = notificationsSseStore;
    // Back-compat toast helpers routed through unified notifications store
    globalThis.toastFrontendInfo = function(message, title = "Info", display_time = 3, group = "", priority) {
      try { notificationsSseStore.create({ type: "info", title, body: message, severity: "info", ttl_seconds: display_time }); } catch {}
    };
    globalThis.toastFrontendSuccess = function(message, title = "Success", display_time = 3, group = "", priority) {
      try { notificationsSseStore.create({ type: "success", title, body: message, severity: "success", ttl_seconds: display_time }); } catch {}
    };
    globalThis.toastFrontendWarning = function(message, title = "Warning", display_time = 5, group = "", priority) {
      try { notificationsSseStore.create({ type: "warning", title, body: message, severity: "warning", ttl_seconds: display_time }); } catch {}
    };
    globalThis.toastFrontendError = function(message, title = "Error", display_time = 8, group = "", priority) {
      try { notificationsSseStore.create({ type: "error", title, body: message, severity: "error", ttl_seconds: display_time }); } catch {}
    };
  } catch (e) { console.warn("Failed to init SSE notifications store", e); }

  // Bridge SSE notifications to an Alpine store for UI bindings
  try {
    const notifBridge = createAlpineStore("notificationSse", { unreadCount: 0, count: 0, list: [], toastStack: [] });
    // Seed initial values if already loaded
    if (notificationsSseStore?.state) {
      notifBridge.unreadCount = notificationsSseStore.state.unreadCount || 0;
      notifBridge.count = (notificationsSseStore.state.list || []).length;
      notifBridge.list = notificationsSseStore.state.list || [];
      notifBridge.toastStack = notificationsSseStore.state.toastStack || [];
    }
    bus.on("notifications.updated", ({ unread, count }) => {
      notifBridge.unreadCount = unread || 0;
      notifBridge.count = count || 0;
      notifBridge.list = notificationsSseStore.state.list || [];
      notifBridge.toastStack = notificationsSseStore.state.toastStack || [];
    });
    // Connection status Alpine store (used by bell-adjacent indicator)
    const connBridge = createAlpineStore('conn', { status: 'offline', tooltip: 'Offline' });
    // If connection already established before DOM ready, reflect it
    if (typeof connectionStatus === 'boolean') {
      connBridge.status = connectionStatus ? 'online' : 'offline';
      connBridge.tooltip = connectionStatus ? 'Online' : 'Offline';
    }
  } catch (e) { console.warn("Failed to create Alpine notifications bridge", e); }

  // Ensure an active context exists so SSE connects (needed for notifications stream)
  try {
    if (!getContext()) {
      newContext();
    }
  } catch (e) { console.warn("Failed to ensure SSE context", e); }
});

globalThis.loadChats = async function () {
  try {
    const fileContents = await readJsonFiles();
    const response = await sendJsonData("/chat_load", { chats: fileContents });

    if (!response) {
      toast("No response returned.", "error");
    }
    // else if (!response.ok) {
    //     if (response.message) {
    //         toast(response.message, "error")
    //     } else {
    //         toast("Undefined error.", "error")
    //     }
    // }
    else {
      setContext(response.ctxids[0]);
      toast("Chats loaded.", "success");
    }
  } catch (e) {
    toastFetchError("Error loading chats", e);
  }
};

globalThis.saveChat = async function () {
  try {
    const response = await sendJsonData("/chat_export", { ctxid: context });

    if (!response) {
      toast("No response returned.", "error");
    }
    //  else if (!response.ok) {
    //     if (response.message) {
    //         toast(response.message, "error")
    //     } else {
    //         toast("Undefined error.", "error")
    //     }
    // }
    else {
      downloadFile(response.ctxid + ".json", response.content);
      toast("Chat file downloaded.", "success");
    }
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

function justToast(text, type = "info", timeout = 5000) {
  try { notificationsSseStore.create({ type, title: text, body: "", severity: type, ttl_seconds: Math.max(1, timeout/1000) }); } catch {}
}
  

function toast(text, type = "info", timeout = 5000) {
  try { notificationsSseStore.create({ type, title: text, body: "", severity: type.toLowerCase(), ttl_seconds: Math.max(1, timeout/1000) }); } catch {}
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

// Legacy polling fully removed; SSE handles live updates

// Setup event handlers once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  setupSidebarToggle();
  setupTabs();
  initializeActiveTab();
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

  // Refresh sessions list and rebind SSE/history for current context
  fetchSessionsAndPopulate().then(() => {
    if (context) {
      loadHistory(context).then(() => stream.start(context));
    }
  });
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
