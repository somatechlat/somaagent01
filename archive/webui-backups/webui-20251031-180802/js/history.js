import { getContext } from "../index.js";

export async function openHistoryModal() {
    try {
        const ctx = getContext();
        if (!ctx) throw new Error("No active session");
        const response = await fetchApi(`/v1/sessions/${encodeURIComponent(ctx)}/history`, { method: "GET" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const hist = await response.json();
        const data = hist.history || "";
        const size = hist.tokens ?? Math.round((data.length || 0) / 4);
        await showEditorModal(data, "markdown", `History ~${size} tokens`, "Conversation history visible to the LLM. History is compressed to fit into the context window over time.");
    } catch (e) {
        window.toastFrontendError("Error fetching history: " + e.message, "Chat History Error");
        return;
    }
}

export async function openCtxWindowModal() {
    try {
        const ctx = getContext();
        if (!ctx) throw new Error("No active session");
        const response = await fetchApi(`/v1/sessions/${encodeURIComponent(ctx)}/context-window`, { method: "GET" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const win = await response.json();
        const data = win.content || "";
        const size = win.tokens ?? Math.round((data.length || 0) / 4);
        await showEditorModal(data, "markdown", `Context window ~${size} tokens`, "Data passed to the LLM during last interaction. Contains system message, conversation history and RAG.");
    } catch (e) {
        window.toastFrontendError("Error fetching context: " + e.message, "Context Error");
        return;
    }
}

async function showEditorModal(data, type = "json", title, description = "") {
    // Generate the HTML with JSON Viewer container
    const html = `<div id="json-viewer-container"></div>`;

    // Open the modal with the generated HTML
    await window.genericModalProxy.openModal(title, description, html, ["history-viewer"]);

    // Initialize the JSON Viewer after the modal is rendered
    const container = document.getElementById("json-viewer-container");
    if (container) {
        const editor = ace.edit("json-viewer-container");

        const dark = localStorage.getItem('darkMode')
        if (dark != "false") {
            editor.setTheme("ace/theme/github_dark");
        } else {
            editor.setTheme("ace/theme/tomorrow");
        }

        editor.session.setMode("ace/mode/" + type);
        editor.setValue(data);
        editor.clearSelection();
        // editor.session.$toggleFoldWidget(5, {})
    }
}

window.openHistoryModal = openHistoryModal;
window.openCtxWindowModal = openCtxWindowModal;
