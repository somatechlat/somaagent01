const settingsModalProxy = {
    isOpen: false,
    settings: {},
    resolvePromise: null,
    activeTab: 'agent', // Default tab
    provider: 'cloudflared',

    // Computed property for filtered sections
    get filteredSections() {
        if (!this.settings || !this.settings.sections) return [];
        const filteredSections = this.settings.sections.filter(section => section.tab === this.activeTab);

        // If no sections match the current tab (or all tabs are missing), show all sections
        if (filteredSections.length === 0) {
            return this.settings.sections;
        }

        return filteredSections;
    },

    // Switch tab method
    switchTab(tabName) {
        // Update our component state
        this.activeTab = tabName;

        // Update the store safely
        const store = Alpine.store('root');
        if (store) {
            store.activeTab = tabName;
        }

        localStorage.setItem('settingsActiveTab', tabName);

        // Auto-scroll active tab into view after a short delay to ensure DOM updates
        setTimeout(() => {
            const activeTab = document.querySelector('.settings-tab.active');
            if (activeTab) {
                activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }

            // When switching to the scheduler tab, initialize Flatpickr components
            if (tabName === 'scheduler') {
                console.log('Switching to scheduler tab, initializing Flatpickr');
                const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                if (schedulerElement) {
                    const schedulerData = Alpine.$data(schedulerElement);
                    if (schedulerData) {
                        // Start polling
                        if (typeof schedulerData.startPolling === 'function') {
                            schedulerData.startPolling();
                        }

                        // Initialize Flatpickr if editing or creating
                        if (typeof schedulerData.initFlatpickr === 'function') {
                            // Check if we're creating or editing and initialize accordingly
                            if (schedulerData.isCreating) {
                                schedulerData.initFlatpickr('create');
                            } else if (schedulerData.isEditing) {
                                schedulerData.initFlatpickr('edit');
                            }
                        }

                        // Force an immediate fetch
                        if (typeof schedulerData.fetchTasks === 'function') {
                            schedulerData.fetchTasks();
                        }
                    }
                }
            }
        }, 10);
    },

    async openModal() {
        console.log('Settings modal opening');
        const modalEl = document.getElementById('settingsModal');
        const modalAD = Alpine.$data(modalEl);

        // First, ensure the store is updated properly
        const store = Alpine.store('root');
        if (store) {
            // Set isOpen first to ensure proper state
            store.isOpen = true;
        }
        // Also set the component state so x-show binds render immediately
        try { this.isOpen = true; } catch(_) {}
        try { if (modalAD) modalAD.isOpen = true; } catch(_) {}
        // Hard-show overlay immediately in case Alpine reactivity is late
        try {
            const overlay = modalEl.querySelector('.modal-overlay');
            if (overlay) overlay.style.setProperty('display','flex','important');
        } catch(_) {}

        //get settings from backend (canonical /v1)
        try {
            const resp = await fetchApi('/ui/settings/sections', { method: 'GET' });
            if (!resp.ok) throw new Error(await resp.text());
            const set = await resp.json();

            // First load the settings data without setting the active tab
            const settings = {
                "title": "Settings",
                "buttons": [
                    {
                        "id": "save",
                        "title": "Save",
                        "classes": "btn btn-ok"
                    },
                    {
                        "id": "cancel",
                        "title": "Cancel",
                        "type": "secondary",
                        "classes": "btn btn-cancel"
                    }
                ],
                "sections": set.settings.sections
            }

            // Update modal data
            modalAD.isOpen = true;
            modalAD.settings = settings;

            // Now set the active tab after the modal is open
            // This ensures Alpine reactivity works as expected
            setTimeout(() => {
                // Get stored tab or default to 'agent'
                const savedTab = localStorage.getItem('settingsActiveTab') || 'agent';
                console.log(`Setting initial tab to: ${savedTab}`);

                // Directly set the active tab
                modalAD.activeTab = savedTab;

                // Also update the store
                if (store) {
                    store.activeTab = savedTab;
                }

                localStorage.setItem('settingsActiveTab', savedTab);

                // Add a small delay *after* setting the tab to ensure scrolling works
                setTimeout(() => {
                    const activeTabElement = document.querySelector('.settings-tab.active');
                    if (activeTabElement) {
                        activeTabElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                    }
                    // Debug log
                    const schedulerTab = document.querySelector('.settings-tab[title="Task Scheduler"]');
                    console.log(`Current active tab after direct set: ${modalAD.activeTab}`);
                    console.log('Scheduler tab active after direct initialization?',
                        schedulerTab && schedulerTab.classList.contains('active'));

                    // Explicitly start polling if we're on the scheduler tab
                    if (modalAD.activeTab === 'scheduler') {
                        console.log('Settings opened directly to scheduler tab, initializing polling');
                        const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                        if (schedulerElement) {
                            const schedulerData = Alpine.$data(schedulerElement);
                            if (schedulerData && typeof schedulerData.startPolling === 'function') {
                                schedulerData.startPolling();
                                // Also force an immediate fetch
                                if (typeof schedulerData.fetchTasks === 'function') {
                                    schedulerData.fetchTasks();
                                }
                            }
                        }
                    }
                }, 10); // Small delay just for scrolling

            }, 5); // Keep a minimal delay for modal opening reactivity

            // Add a watcher to disable the Save button when a task is being created or edited
            const schedulerComponent = document.querySelector('[x-data="schedulerSettings"]');
            if (schedulerComponent) {
                // Watch for changes to the scheduler's editing state
                const checkSchedulerEditingState = () => {
                    const schedulerData = Alpine.$data(schedulerComponent);
                    if (schedulerData) {
                        // If we're on the scheduler tab and creating/editing a task, disable the Save button
                        const saveButton = document.querySelector('.modal-footer button.btn-ok');
                        if (saveButton && modalAD.activeTab === 'scheduler' &&
                            (schedulerData.isCreating || schedulerData.isEditing)) {
                            saveButton.disabled = true;
                            saveButton.classList.add('btn-disabled');
                        } else if (saveButton) {
                            saveButton.disabled = false;
                            saveButton.classList.remove('btn-disabled');
                        }
                    }
                };

                // Add a mutation observer to detect changes in the scheduler component's state
                const observer = new MutationObserver(checkSchedulerEditingState);
                observer.observe(schedulerComponent, { attributes: true, subtree: true, childList: true });

                // Also watch for tab changes to update button state
                modalAD.$watch('activeTab', checkSchedulerEditingState);

                // Initial check
                setTimeout(checkSchedulerEditingState, 100);
            }

            return new Promise(resolve => {
                this.resolvePromise = resolve;
            });

        } catch (e) {
            window.toastFetchError("Error getting settings", e)
        }
    },

    async handleButton(buttonId) {
        if (buttonId === 'save') {

            const modalEl = document.getElementById('settingsModal');
            const modalAD = Alpine.$data(modalEl);
            let savedJson = null;
            try {
                // Progress toast (replaced by success/error via group)
                if (window.toastFrontendInfo) {
                    window.toastFrontendInfo('Saving settings…', 'Settings', 2, 'settings-save');
                }
                // Save sections back to canonical endpoint
                const resp = await fetchApi('/ui/settings/sections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sections: modalAD.settings.sections })
                });
                if (!resp.ok) throw new Error(await resp.text());
                try { savedJson = await resp.json(); } catch (_) { savedJson = null; }
            } catch (e) {
                if (window.toastFrontendError) {
                    const msg = (e && e.message) ? e.message : String(e);
                    window.toastFrontendError(`Failed to save settings: ${msg}`, 'Settings', 6, 'settings-save');
                } else {
                    window.toastFetchError("Error saving settings", e)
                }
                return
            }

            // Opportunistic LLM credentials save if fields present
            try {
                const sections = modalAD.settings.sections || [];
                let provider = '';
                let secret = '';
                for (const sec of sections) {
                    for (const f of sec.fields || []) {
                        const id = String(f.id || '').toLowerCase();
                        if (id.includes('provider') && !provider) provider = String(f.value || '').trim();
                        if ((id.includes('api_key') || id.includes('secret') || id.includes('token')) && !secret) {
                            secret = String(f.value || '').trim();
                        }
                    }
                }
                if (provider && secret) {
                    await fetchApi('/llm/credentials', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ provider, secret })
                    });
                }
            } catch (e) {
                // Non-fatal; credential saving is best-effort
                console.warn('LLM credentials save skipped:', e?.message || e);
            }
            // Success toast replaces progress toast
            if (window.toastFrontendSuccess) {
                window.toastFrontendSuccess('Settings saved successfully', 'Settings', 3, 'settings-save');
            }
            // Immediately re-fetch sections to pick up masked credentials and normalized URLs
            try {
                const ref = await fetchApi('/ui/settings/sections', { method: 'GET' });
                if (ref.ok) {
                    const fresh = await ref.json().catch(() => null);
                    if (fresh && fresh.settings) {
                        modalAD.settings = fresh.settings;
                    }
                }
            } catch(_e) {}
            // Update modal data with server-returned shape when available
            if (savedJson && savedJson.settings) {
                modalAD.settings = savedJson.settings;
            }
            document.dispatchEvent(new CustomEvent('settings-updated', { detail: (savedJson && savedJson.settings) ? savedJson.settings : modalAD.settings }));
            this.resolvePromise({
                status: 'saved',
                data: modalAD.settings
            });
        } else if (buttonId === 'cancel') {
            this.handleCancel();
        }

        // Stop scheduler polling if it's running
        this.stopSchedulerPolling();

        // First update our component state
        this.isOpen = false;
        try {
            const modalEl = document.getElementById('settingsModal');
            const overlay = modalEl ? modalEl.querySelector('.modal-overlay') : null;
            if (overlay) overlay.style.removeProperty('display');
        } catch(_) {}

        // Then safely update the store
        const store = Alpine.store('root');
        if (store) {
            // Use a slight delay to avoid reactivity issues
            setTimeout(() => {
                store.isOpen = false;
            }, 10);
        }
    },

    async handleCancel() {
        this.resolvePromise({
            status: 'cancelled',
            data: null
        });

        // Stop scheduler polling if it's running
        this.stopSchedulerPolling();

        // First update our component state
        this.isOpen = false;
        try {
            const modalEl = document.getElementById('settingsModal');
            const overlay = modalEl ? modalEl.querySelector('.modal-overlay') : null;
            if (overlay) overlay.style.removeProperty('display');
        } catch(_) {}

        // Then safely update the store
        const store = Alpine.store('root');
        if (store) {
            // Use a slight delay to avoid reactivity issues
            setTimeout(() => {
                store.isOpen = false;
            }, 10);
        }
    },

    // Add a helper method to stop scheduler polling
    stopSchedulerPolling() {
        // Find the scheduler component and stop polling if it exists
        const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
        if (schedulerElement) {
            const schedulerData = Alpine.$data(schedulerElement);
            if (schedulerData && typeof schedulerData.stopPolling === 'function') {
                console.log('Stopping scheduler polling on modal close');
                schedulerData.stopPolling();
            }
        }
    },

    async handleFieldButton(field) {
        console.log(`Button clicked: ${field.id}`);

        if (field.id === "mcp_servers_config") {
            openModal("settings/mcp/client/mcp-servers.html");
        } else if (field.id === "backup_create") {
            openModal("settings/backup/backup.html");
        } else if (field.id === "backup_restore") {
            openModal("settings/backup/restore.html");
        } else if (field.id === "show_a2a_connection") {
            openModal("settings/external/a2a-connection.html");
        } else if (field.id === "external_api_examples") {
            openModal("settings/external/api-examples.html");
        } else if (field.id === "memory_dashboard") {
            openModal("settings/memory/memory-dashboard.html");
        } else if (field.id === "av_test") {
            try {
                const oldVal = field.value;
                field.value = 'Testing…';
                const resp = await fetchApi('/v1/av/test', { method: 'GET' });
                const data = await resp.json().catch(() => ({}));
                field.value = oldVal;
                const status = (data && data.status) || 'unknown';
                if (status === 'ok') {
                    showToast(`Antivirus reachable at ${data.host}:${data.port}`, 'success');
                } else if (status === 'disabled') {
                    showToast(`Antivirus is disabled (configured ${data.host}:${data.port})`, 'info');
                } else {
                    const detail = (data && data.detail) ? `: ${data.detail}` : '';
                    showToast(`Antivirus error${detail}`, 'error');
                }
            } catch (e) {
                showToast(`Antivirus test failed: ${e?.message || e}`, 'error');
            }
        }
    }
};


// function initSettingsModal() {

//     window.openSettings = function () {
//         proxy.openModal().then(result => {
//             console.log(result);  // This will log the result when the modal is closed
//         });
//     }

//     return proxy
// }


// document.addEventListener('alpine:init', () => {
//     Alpine.store('settingsModal', initSettingsModal());
// });

// Expose for Alpine expressions in markup (e.g., @click="settingsModalProxy.openModal()")
try { globalThis.settingsModalProxy = settingsModalProxy; } catch (_) {}

// Fallback: bind Settings button click after DOM is ready in case Alpine event parsing fails
try {
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('settings');
    if (btn) {
      btn.addEventListener('click', (e) => {
        try { e.preventDefault(); } catch(_) {}
        try { settingsModalProxy.openModal(); } catch(_) {}
      });
    }
  });
} catch(_) {}

// Live-refresh settings in any open modal when another tab/process saves settings.
// Listens for 'settings-updated' (also dispatched from SSE handler in index.js).
document.addEventListener('settings-updated', async function () {
  try {
    const modalEl = document.getElementById('settingsModal');
    if (!modalEl) return;
    const ad = window.Alpine ? Alpine.$data(modalEl) : null;
    const needsRefresh = ad && (ad.settings !== undefined || ad.settingsData !== undefined);
    if (!needsRefresh) return;
    const resp = await fetchApi('/ui/settings/sections', { method: 'GET' });
    if (!resp.ok) return;
    const json = await resp.json().catch(() => null);
    if (!json || !json.settings) return;
    if (ad.settings !== undefined) ad.settings = json.settings;
    if (ad.settingsData !== undefined) ad.settingsData = json.settings;
    if (typeof ad.updateFilteredSections === 'function') {
      try { ad.updateFilteredSections(); } catch (_) {}
    }
  } catch (_) {}
});

document.addEventListener('alpine:init', function () {
    // Initialize the root store first to ensure it exists before components try to access it
    Alpine.store('root', {
        activeTab: localStorage.getItem('settingsActiveTab') || 'agent',
        isOpen: false,

        toggleSettings() {
            this.isOpen = !this.isOpen;
        }
    });

    // Then initialize other Alpine components
    Alpine.data('settingsModal', function () {
        return {
            settingsData: {},
            filteredSections: [],
            activeTab: 'agent',
            isLoading: true,

            async init() {
                // Initialize with the store value
                this.activeTab = Alpine.store('root').activeTab || 'agent';

                // Watch store tab changes
                this.$watch('$store.root.activeTab', (newTab) => {
                    if (typeof newTab !== 'undefined') {
                        this.activeTab = newTab;
                        localStorage.setItem('settingsActiveTab', newTab);
                        this.updateFilteredSections();
                    }
                });

                // Load settings
                await this.fetchSettings();
                this.updateFilteredSections();
            },

            switchTab(tab) {
                // Update our component state
                this.activeTab = tab;

                // Update the store safely
                const store = Alpine.store('root');
                if (store) {
                    store.activeTab = tab;
                }
            },

            async fetchSettings() {
                try {
                    this.isLoading = true;
                    const response = await fetchApi('/ui/settings/sections', { method: 'GET' });
                    if (response.ok) {
                        const data = await response.json();
                        if (data && data.settings) {
                            this.settingsData = data.settings;
                        } else {
                            console.error('Invalid settings data format');
                        }
                    } else {
                        console.error('Failed to fetch settings:', response.statusText);
                    }
                } catch (error) {
                    console.error('Error fetching settings:', error);
                } finally {
                    this.isLoading = false;
                }
            },

            updateFilteredSections() {
                // Filter sections based on active tab
                if (this.activeTab === 'agent') {
                    this.filteredSections = this.settingsData.sections?.filter(section =>
                        section.tab === 'agent'
                    ) || [];
                } else if (this.activeTab === 'external') {
                    this.filteredSections = this.settingsData.sections?.filter(section =>
                        section.tab === 'external'
                    ) || [];
                } else if (this.activeTab === 'developer') {
                    this.filteredSections = this.settingsData.sections?.filter(section =>
                        section.tab === 'developer'
                    ) || [];
                } else if (this.activeTab === 'mcp') {
                    this.filteredSections = this.settingsData.sections?.filter(section =>
                        section.tab === 'mcp'
                    ) || [];
                } else if (this.activeTab === 'backup') {
                    this.filteredSections = this.settingsData.sections?.filter(section =>
                        section.tab === 'backup'
                    ) || [];
                } else {
                    // For any other tab, show nothing since those tabs have custom UI
                    this.filteredSections = [];
                }
            },

            async saveSettings() {
                try {
                    // First validate
                    for (const section of this.settingsData.sections) {
                        for (const field of section.fields) {
                            if (field.required && (!field.value || (typeof field.value === 'string' && field.value.trim() === ''))) {
                                showToast(`${field.title} in ${section.title} is required`, 'error');
                                return;
                            }
                        }
                    }

                    // If provider changed but base_url points to another provider, blank it so Gateway applies provider default.
                    try {
                        let provider = '';
                        let apiBaseField = null;
                        for (const sec of this.settingsData.sections) {
                            for (const f of sec.fields || []) {
                                const id = String(f.id || '').toLowerCase();
                                if (id === 'chat_model_provider') provider = String(f.value || '').trim().toLowerCase();
                                if (id === 'chat_model_api_base') apiBaseField = f;
                            }
                        }
                        if (provider && apiBaseField && typeof apiBaseField.value === 'string' && apiBaseField.value.trim()) {
                            const v = apiBaseField.value.trim().toLowerCase();
                            const mismatched = (provider === 'groq' && v.includes('openrouter')) ||
                                               (provider === 'openrouter' && v.includes('groq')) ||
                                               (provider === 'openai' && (v.includes('openrouter') || v.includes('groq')));
                            if (mismatched) {
                                apiBaseField.value = '';
                            }
                        }
                    } catch (_) {}

                    // Send sections as-is to canonical endpoint
                    const response = await fetchApi('/ui/settings/sections', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sections: this.settingsData.sections })
                    });

                    if (response.ok) {
                        showToast('Settings saved successfully', 'success');
                        // Opportunistic credentials write when an unmasked key is provided
                        try {
                            let provider = '';
                            let secret = '';
                            for (const sec of this.settingsData.sections) {
                                for (const f of sec.fields || []) {
                                    const id = String(f.id || '').toLowerCase();
                                    const val = (typeof f.value === 'string') ? f.value.trim() : '';
                                    if (!provider && (id.includes('provider') || id === 'provider')) provider = val;
                                    const isSecret = id.includes('api_key') || id.includes('secret') || id.includes('token');
                                    if (!secret && isSecret && val && val !== '************') secret = val;
                                }
                            }
                            if (provider && secret) {
                                await fetchApi('/llm/credentials', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ provider, secret })
                                });
                            }
                        } catch (e) {
                            console.warn('Credentials save skipped:', e?.message || e);
                        }
                        // Refresh settings sections to pick up normalized base_url and masked secrets
                        await this.fetchSettings();
                        // Broadcast for other components/tabs
                        try { document.dispatchEvent(new CustomEvent('settings-updated', { detail: this.settingsData })); } catch(_) {}
                    } else {
                        const errorText = await response.text();
                        throw new Error(errorText || 'Failed to save settings');
                    }
                } catch (error) {
                    console.error('Error saving settings:', error);
                    showToast('Failed to save settings: ' + error.message, 'error');
                }
            },

            // Handle special button field actions
            handleFieldButton(field) {
                if (field.action === 'test_connection') {
                    this.testConnection(field);
                } else if (field.action === 'reveal_token') {
                    this.revealToken(field);
                } else if (field.action === 'generate_token') {
                    this.generateToken(field);
                } else {
                    console.warn('Unknown button action:', field.action);
                }
            },

            // Test LLM connection (admin): uses /v1/llm/test
            async testConnection(field) {
                try {
                    field.testResult = 'Testing...';
                    field.testStatus = 'loading';

                    // Determine role under test (dialogue|escalation); default to dialogue
                    const role = (field?.service === 'escalation' || field?.role === 'escalation') ? 'escalation' : 'dialogue';

                    const response = await fetchApi('/llm/test', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ role })
                    });

                    const data = await response.json();

                    if (response.ok && data.ok) {
                        const parts = [];
                        if (data.provider) parts.push(`provider: ${data.provider}`);
                        if (data.base_url) parts.push(`base: ${data.base_url}`);
                        parts.push(`credentials: ${data.credentials_present ? 'present' : 'missing'}`);
                        parts.push(`reachable: ${data.reachable ? 'yes' : 'no'}`);
                        field.testResult = `OK (${parts.join(', ')})`;
                        field.testStatus = data.reachable && data.credentials_present ? 'success' : 'warning';
                    } else {
                        throw new Error(data.detail || data.error || 'Connection failed');
                    }
                } catch (error) {
                    console.error('Connection test failed:', error);
                    field.testResult = `Failed: ${error.message}`;
                    field.testStatus = 'error';
                }
            },

            // Reveal token temporarily
            revealToken(field) {
                // Find target field
                for (const section of this.settingsData.sections) {
                    for (const f of section.fields) {
                        if (f.id === field.target) {
                            // Toggle field type
                            f.type = f.type === 'password' ? 'text' : 'password';

                            // Update button text
                            field.value = f.type === 'password' ? 'Show' : 'Hide';

                            break;
                        }
                    }
                }
            },

            // Generate random token
            generateToken(field) {
                // Find target field
                for (const section of this.settingsData.sections) {
                    for (const f of section.fields) {
                        if (f.id === field.target) {
                            // Generate random token
                            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
                            let token = '';
                            for (let i = 0; i < 32; i++) {
                                token += chars.charAt(Math.floor(Math.random() * chars.length));
                            }

                            // Set field value
                            f.value = token;
                            break;
                        }
                    }
                }
            },

            closeModal() {
                // Stop scheduler polling before closing the modal
                const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                if (schedulerElement) {
                    const schedulerData = Alpine.$data(schedulerElement);
                    if (schedulerData && typeof schedulerData.stopPolling === 'function') {
                        console.log('Stopping scheduler polling on modal close');
                        schedulerData.stopPolling();
                    }
                }

                this.$store.root.isOpen = false;
            }
        };
    });
});

// Global helper to run provider connectivity test and surface provider/host/reachability
// Show toast notification - now uses new notification system
function showToast(message, type = 'info') {
    // Use new frontend notification system based on type
    if (window.Alpine && window.Alpine.store && window.Alpine.store('notificationStore')) {
        const store = window.Alpine.store('notificationStore');
        switch (type.toLowerCase()) {
            case 'error':
                return store.frontendError(message, "Settings", 5);
            case 'success':
                return store.frontendInfo(message, "Settings", 3);
            case 'warning':
                return store.frontendWarning(message, "Settings", 4);
            case 'info':
            default:
                return store.frontendInfo(message, "Settings", 3);
        }
    } else {
        // Fallback if Alpine/store not ready
        console.log(`SETTINGS ${type.toUpperCase()}: ${message}`);
        return null;
    }
}
