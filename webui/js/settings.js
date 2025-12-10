// Settings modal logic for the web UI.
// The settingsModal Alpine component is pre-initialized in index.html.
// This module provides the proxy object and Alpine store initialization.

/** Proxy object exposed as `settingsModalProxy` for Alpine components. */
const settingsModalProxy = {
    isOpen: false,
    resolvePromise: null,
    activeTab: "agent",
    settings: { sections: [] },
    
    openModal() {
        this.isOpen = true;
        if (typeof Alpine !== 'undefined' && Alpine.store) {
            const store = Alpine.store('root');
            if (store) {
                store.isOpen = true;
            }
        }
    },
    
    closeModal() {
        this.isOpen = false;
        if (typeof Alpine !== 'undefined' && Alpine.store) {
            const store = Alpine.store('root');
            if (store) {
                store.isOpen = false;
            }
        }
        if (this.resolvePromise) {
            this.resolvePromise({ status: "cancelled" });
            this.resolvePromise = null;
        }
    }
};

globalThis.settingsModalProxy = settingsModalProxy;

// Initialize Alpine root store (settings modal component is in index.html)
function initializeAlpineStore() {
    if (!Alpine.store('root')) {
        Alpine.store('root', {
            activeTab: localStorage.getItem('settingsActiveTab') || 'agent',
            isOpen: false,
            toggleSettings() {
                this.isOpen = !this.isOpen;
            }
        });
    }
}

if (typeof Alpine !== 'undefined' && Alpine.store) {
    initializeAlpineStore();
} else {
    document.addEventListener('alpine:init', initializeAlpineStore);
}
