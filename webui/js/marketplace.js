// Marketplace UI script – fetches capsules from the registry and renders them.

import { list_capsules } from "../python/somaagent/capsule.js"; // Assuming the SDK is bundled or accessible via a module loader.

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

function createCapsuleCard(capsule) {
  const card = document.createElement("div");
  card.className = "capsule-card";
  card.innerHTML = `
    <h3>${capsule.name} <small>v${capsule.version}</small></h3>
    <p>${capsule.description || "(no description)"}</p>
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
    // Attach install handlers
    container.querySelectorAll(".install-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.dataset.id;
        try {
          // Simple install – download and extract to a temp location.
          const resp = await fetch(`/capsules/${id}`);
          if (!resp.ok) throw new Error(`Download failed: ${resp.status}`);
          const blob = await resp.blob();
          // In a real UI we would invoke the SDK install method.
          alert(`Capsule ${id} downloaded (${blob.size} bytes). Implement SDK install as needed.`);
        } catch (err) {
          console.error(err);
          alert(`Error installing capsule: ${err.message}`);
        }
      });
    });
  } catch (err) {
    console.error(err);
    container.textContent = "Failed to load capsules.";
  }
}

// Run when the page loads.
window.addEventListener("DOMContentLoaded", renderMarketplace);
