// Marketplace UI script – fetches capsules from the registry and renders them.

import { list_capsules } from "../python/somaagent/capsule.js"; // Assuming the SDK is bundled or accessible via a module loader.

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

// Fallback: if the SDK import fails, use a direct HTTP call.
async function fetchCapsules() {
  try {
    // Try the SDK first (may not be available in the browser environment).
    if (typeof list_capsules === "function") {
      return await list_capsules();
    }
  } catch (e) {
    console.warn("SDK not available, falling back to direct fetch", e);
  }
  // Direct fetch using the public API.
  const resp = await fetch("/capsules");
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
        const statusNode = e.target.closest(".capsule-card").querySelector(".install-status");
        toggleBusy(e.target, true);
        try {
          setStatus(statusNode, "Installing capsule…", "info");
          const resp = await fetch(`/capsules/${id}/install`, { method: "POST" });
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
        } catch (err) {
          console.error(err);
          setStatus(statusNode, `Install error: ${escapeHtml(err.message)}`, "error");
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
window.addEventListener("DOMContentLoaded", renderMarketplace);
