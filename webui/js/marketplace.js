// Marketplace UI script – fetches capsules from the registry and renders them.

const API_BASE = "/v1";
const LOG_LIMIT = 25;
const HISTORY_LIMIT = 20;
const HISTORY_KEY = "capsuleInstallHistory";

let logList;
let logEmpty;
let historyContainer;
let historyEmpty;

const state = {
  logEntries: [],
};

function initPanels() {
  logList = document.getElementById("install-log");
  logEmpty = document.getElementById("install-log-empty");
  historyContainer = document.getElementById("install-history");
  historyEmpty = document.getElementById("install-history-empty");

  const clearLogBtn = document.getElementById("clear-log");
  if (clearLogBtn) {
    clearLogBtn.addEventListener("click", () => {
      state.logEntries = [];
      renderLog();
    });
  }

  const clearHistoryBtn = document.getElementById("clear-history");
  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener("click", () => {
      persistHistory([]);
      renderHistory([]);
    });
  }

  renderHistory(loadHistory());
  renderLog();
}

function escapeHtml(value = "") {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setStatus(node, message, intent = "info") {
  if (!node) return;
  node.dataset.intent = intent;
  node.innerHTML = message;
}

function nowIso() {
  return new Date().toISOString();
}

function renderLog() {
  if (!logList || !logEmpty) return;
  logList.innerHTML = "";
  if (state.logEntries.length === 0) {
    logList.hidden = true;
    logEmpty.hidden = false;
    return;
  }
  logList.hidden = false;
  logEmpty.hidden = true;

  state.logEntries.forEach((entry, index) => {
    const li = document.createElement("li");
    li.dataset.index = String(state.logEntries.length - index);

    const time = document.createElement("time");
    time.dateTime = entry.timestamp;
    time.textContent = new Date(entry.timestamp).toLocaleTimeString();

    const message = document.createElement("div");
    message.className = "log-message";
    message.dataset.intent = entry.intent;
    const capsulePart = entry.capsuleName
      ? `<strong>${escapeHtml(entry.capsuleName)}</strong>`
      : "";
    message.innerHTML = `${capsulePart ? `${capsulePart} — ` : ""}${escapeHtml(entry.message)}`;

    li.appendChild(time);
    li.appendChild(message);
    logList.appendChild(li);
  });
}

function appendLog({ intent = "info", message, capsuleName }) {
  state.logEntries.unshift({
    intent,
    message,
    capsuleName,
    timestamp: nowIso(),
  });
  if (state.logEntries.length > LOG_LIMIT) {
    state.logEntries.length = LOG_LIMIT;
  }
  renderLog();
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch (err) {
    console.warn("Unable to load capsule install history", err);
    return [];
  }
}

function persistHistory(entries) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
  } catch (err) {
    console.warn("Unable to persist capsule install history", err);
  }
}

function renderHistory(entries) {
  if (!historyContainer || !historyEmpty) return;
  historyContainer.innerHTML = "";
  if (!entries || entries.length === 0) {
    historyContainer.hidden = true;
    historyEmpty.hidden = false;
    return;
  }
  historyContainer.hidden = false;
  historyEmpty.hidden = true;

  entries.forEach((entry) => {
    const item = document.createElement("article");
    item.className = "history-item";

    const header = document.createElement("header");
    header.innerHTML = `<span>${escapeHtml(entry.name)} <small>v${escapeHtml(
      entry.version || "?"
    )}</small></span><span>${new Date(entry.timestamp).toLocaleString()}</span>`;

    const meta = document.createElement("div");
    meta.className = "history-meta";
    const pathLine = entry.installPath
      ? `<span>Path: <code>${escapeHtml(entry.installPath)}</code></span>`
      : "";
    const signatureLine = entry.signature
      ? `<span>Signature: <code>${escapeHtml(entry.signature)}</code></span>`
      : `<span>Signature: <em>not provided</em></span>`;
    meta.innerHTML = `${pathLine}${signatureLine}`;

    item.appendChild(header);
    item.appendChild(meta);
    historyContainer.appendChild(item);
  });
}

function recordHistory(entry) {
  const current = loadHistory();
  current.unshift(entry);
  if (current.length > HISTORY_LIMIT) {
    current.length = HISTORY_LIMIT;
  }
  persistHistory(current);
  renderHistory(current);
}

function toggleBusy(button, isBusy) {
  if (!button) return;
  if (isBusy) {
    button.dataset.originalText = button.textContent;
    button.textContent = "Installing…";
    button.disabled = true;
    button.classList.add("is-busy");
  } else {
    const original = button.dataset.originalText || "Install";
    button.textContent = original;
    button.disabled = false;
    button.classList.remove("is-busy");
  }
}

// Capsules are exposed through the gateway proxy (`/v1/capsules`).
async function fetchCapsules() {
  // Direct fetch using the public API exposed via the gateway proxy.
  const resp = await fetch(`${API_BASE}/capsules`);
  if (!resp.ok) throw new Error(`Failed to fetch capsules: ${resp.status}`);
  return await resp.json();
}

function formatDate(isoString) {
  if (!isoString) return "Unknown";
  try {
    return new Date(isoString).toLocaleString();
  } catch (err) {
    console.warn("Failed to format capsule timestamp", err);
    return isoString;
  }
}

function createCapsuleCard(capsule) {
  const card = document.createElement("div");
  card.className = "capsule-card";
  const signatureBlock = capsule.signature
    ? `<details class="capsule-signature"><summary>Signature</summary><code class="capsule-signature__value">${escapeHtml(capsule.signature)}</code><button type="button" class="copy-signature" data-signature="${encodeURIComponent(
        capsule.signature
      )}">Copy</button></details>`
    : `<p class="capsule-signature capsule-signature--missing">Unsigned capsule</p>`;
  card.innerHTML = `
    <h3>${capsule.name} <small>v${capsule.version}</small></h3>
    <p>${capsule.description || "(no description)"}</p>
    <p class="capsule-meta">Published: ${formatDate(capsule.created_at)}</p>
    ${signatureBlock}
    <div class="install-status" aria-live="polite"></div>
    <button class="install-btn" data-id="${capsule.id}">Install</button>
  `;
  const installBtn = card.querySelector(".install-btn");
  if (installBtn) {
    installBtn.dataset.name = capsule.name || "Unknown capsule";
    installBtn.dataset.version = capsule.version || "";
  }
  return card;
}

async function renderMarketplace() {
  const container = document.getElementById("capsule-list");
  if (!container) return;
  container.innerHTML = "Loading...";
  try {
    const capsules = await fetchCapsules();
    container.innerHTML = "";
    if (capsules.length === 0) {
      container.textContent = "No capsules available.";
      return;
    }
    capsules.forEach((c) => {
      const card = createCapsuleCard(c);
      container.appendChild(card);
    });
    // Attach event handlers
    container.querySelectorAll(".copy-signature").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const signature = e.currentTarget.dataset.signature;
        if (!signature || !navigator.clipboard) {
          return;
        }
        try {
          await navigator.clipboard.writeText(decodeURIComponent(signature));
          const statusNode = e.currentTarget.closest(".capsule-card").querySelector(".install-status");
          setStatus(statusNode, "Signature copied to clipboard", "success");
          setTimeout(() => setStatus(statusNode, "", "info"), 1500);
        } catch (err) {
          console.error("Failed to copy signature", err);
        }
      });
    });
    container.querySelectorAll(".install-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.dataset.id;
        const capsuleName = e.target.dataset.name || "Unknown capsule";
        const capsuleVersion = e.target.dataset.version || "";
        const statusNode = e.target.closest(".capsule-card").querySelector(".install-status");
        toggleBusy(e.target, true);
        try {
          setStatus(statusNode, "Installing capsule…", "info");
          appendLog({ intent: "info", message: "Install started", capsuleName: `${capsuleName} ${capsuleVersion ? `v${capsuleVersion}` : ""}`.trim() });
          const resp = await fetch(`${API_BASE}/capsules/${id}/install`, { method: "POST" });
          if (!resp.ok) {
            const detail = await resp.text();
            throw new Error(detail || `Install failed: ${resp.status}`);
          }
          const result = await resp.json();
          const installPath = result.install_path || "(unknown path)";
          const signature = result.signature
            ? `<span class="install-status__meta">Signature: <code>${escapeHtml(result.signature)}</code></span>`
            : `<span class="install-status__meta">Unsigned capsule</span>`;
          setStatus(
            statusNode,
            `Installed to <code>${escapeHtml(installPath)}</code>. ${signature}`,
            "success"
          );
          appendLog({
            intent: "success",
            message: `Installed to ${installPath}`,
            capsuleName: `${capsuleName}${capsuleVersion ? ` v${capsuleVersion}` : ""}`,
          });
          recordHistory({
            id,
            name: capsuleName,
            version: capsuleVersion,
            installPath,
            signature: result.signature || "",
            timestamp: nowIso(),
          });
        } catch (err) {
          console.error(err);
          setStatus(statusNode, `Install error: ${escapeHtml(err.message)}`, "error");
          appendLog({
            intent: "error",
            message: err.message || "Install failed",
            capsuleName: `${capsuleName}${capsuleVersion ? ` v${capsuleVersion}` : ""}`,
          });
        }
        toggleBusy(e.target, false);
      });
    });
  } catch (err) {
    console.error(err);
    container.textContent = "Failed to load capsules.";
  }
}

// Run when the page loads.
window.addEventListener("DOMContentLoaded", () => {
  initPanels();
  renderMarketplace();
});
