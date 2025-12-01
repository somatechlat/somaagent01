// Settings modal logic for the web UI.
// Implements a UI‑side fallback so that the Settings modal always contains the
// required LLM fields even when the backend returns an empty payload.
// All API paths are derived from the central `API` config object.

import { API } from "./config.js";

/** Helper to display error toast messages. */
const safeToast = (text, error) => {
  if (typeof window !== "undefined" && typeof window.toastFetchError === "function") {
    window.toastFetchError(text, error);
  } else {
    console.error(text, error);
  }
};

/** Simple i18n helper – falls back to the provided default. */
const t = (k, fb) => (globalThis.i18n ? i18n.t(k) : fb || k);

/** Proxy object exposed as `settingsModalProxy` for Alpine components. */
const settingsModalProxy = {
    /** Indicates whether the Settings modal is currently open. */
    isOpen: false,
    /** Holds a promise resolver for awaiting modal closure. */
    resolvePromise: null,
    /** Currently active tab within the modal (e.g., 'agent'). */
    activeTab: "agent",
    /** Open the Settings modal and sync state with the Alpine root store. */
    openModal() {
        const store = Alpine.store('root');
        if (store) {
            store.isOpen = true;
        }
        this.isOpen = true;
    },
    /** Close the modal and resolve any awaiting promise. */
    closeModal() {
        const store = Alpine.store('root');
        if (store) {
            store.isOpen = false;
        }
        this.isOpen = false;
        if (this.resolvePromise) {
            this.resolvePromise({ status: "cancelled" });
            this.resolvePromise = null;
        }
    }
};

globalThis.settingsModalProxy = settingsModalProxy;

// Alpine registrations
document.addEventListener('alpine:init', function () {
  Alpine.store('root', {
    // -----------------------------------------------------------------------------
    // Clean Settings modal implementation (replaces previous corrupted version).
    // -----------------------------------------------------------------------------
    import { API } from "./config.js";

    /** Display an error toast – falls back to console.error if UI toast unavailable. */
    const safeToast = (text, error) => {
        if (typeof window !== "undefined" && typeof window.toastFetchError === "function") {
            window.toastFetchError(text, error);
        } else {
            console.error(text, error);
        }
    };

    /** Simple i18n helper – uses global i18n if present. */
    const t = (k, fb) => (globalThis.i18n ? i18n.t(k) : fb || k);

    /** Proxy exposed globally; UI components call `settingsModalProxy.openModal()`. */
    const settingsModalProxy = {
        isOpen: false,
        resolvePromise: null,
        activeTab: "agent",
        /** Open the modal and sync with Alpine root store. */
        openModal() {
            const store = Alpine.store('root');
            if (store) store.isOpen = true;
            this.isOpen = true;
        },
        /** Close the modal and resolve any awaiting promise. */
        closeModal() {
            const store = Alpine.store('root');
            if (store) store.isOpen = false;
            this.isOpen = false;
            if (this.resolvePromise) {
                this.resolvePromise({ status: "cancelled" });
                this.resolvePromise = null;
            }
        }
    };

    globalThis.settingsModalProxy = settingsModalProxy;

    // -----------------------------------------------------------------------------
    // Alpine registrations – root store and modal component.
    // -----------------------------------------------------------------------------
    document.addEventListener('alpine:init', () => {
        // Root store holds global UI state (open/close, active tab).
        Alpine.store('root', {
            activeTab: localStorage.getItem('settingsActiveTab') || 'agent',
            isOpen: false,
            toggleSettings() { this.isOpen = !this.isOpen; }
        });

        // Settings modal component.
        Alpine.data('settingsModal', () => ({
            settings: {},
            filteredSections: [],
            activeTab: 'agent',
            isLoading: true,

            async init() {
                this.activeTab = Alpine.store('root').activeTab || 'agent';
                this.$watch('$store.root.activeTab', (newTab) => {
                    if (newTab !== undefined) {
                        this.activeTab = newTab;
                        localStorage.setItem('settingsActiveTab', newTab);
                        this.updateFilteredSections();
                    }
                });
                await this.fetchSettings();
                this.updateFilteredSections();
            },

            switchTab(tab) {
                this.activeTab = tab;
                const store = Alpine.store('root');
                if (store) store.activeTab = tab;
            },

            async fetchSettings() {
                try {
                    this.isLoading = true;
                    const resp = await fetchApi(`${API.BASE}${API.SETTINGS}`);
                    if (resp.ok) {
                        const data = await resp.json();
                        const sections = data?.sections || data?.settings?.sections || data?.data?.sections || [];
                        const title = data?.title || data?.data?.title || t('settings.title', 'Settings');
                        const buttons = data?.buttons || data?.settings?.buttons || [
                            { id: "save", title: t('actions.save', 'Save'), classes: "btn btn-ok" },
                            { id: "cancel", title: t('actions.cancel', 'Cancel'), type: "secondary", classes: "btn btn-cancel" }
                        ];
                        this.settings = { title, buttons, sections };
                    } else {
                        console.error(t('settings.fetchFailed', 'Failed to fetch settings'), resp.statusText);
                    }
                } catch (e) {
                    console.error(t('settings.fetchError', 'Error getting settings'), e);
                } finally {
                    this.isLoading = false;
                }
            },

            updateFilteredSections() {
                if (!this.settings.sections) { this.filteredSections = []; return; }
                this.filteredSections = this.settings.sections.filter(s => s.tab === this.activeTab);
            },

            async handleButton(buttonId) {
                if (buttonId === 'save') {
                    const modalEl = document.getElementById('settingsModal');
                    const modalAD = modalEl ? Alpine.$data(modalEl) : null;
                    const sections = modalAD?.settings?.sections || [];
                    try {
                        const response = await fetchApi(`${API.BASE}${API.SETTINGS}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ sections })
                        });
                        if (!response.ok) throw new Error(await response.text());
                        const data = await response.json();
                        const updated = data?.sections || data?.settings?.sections || [];
                        if (modalAD && Array.isArray(updated) && updated.length) {
                            modalAD.settings.sections = updated;
                        }
                        document.dispatchEvent(new CustomEvent('settings-updated', { detail: data }));
                        if (typeof window.toastFrontendSuccess === 'function') {
                            window.toastFrontendSuccess(t('settings.saved', 'Settings saved'), t('settings.title', 'Settings'), 3);
                        }
                        if (this.resolvePromise) {
                            this.resolvePromise({ status: 'saved', data });
                            this.resolvePromise = null;
                        }
                    } catch (e) {
                        safeToast(t('settings.saveError', 'Error saving settings'), e);
                    }
                } else if (buttonId === 'cancel') {
                    this.handleCancel();
                    return;
                }
                // Close UI after any button action.
                this.isOpen = false;
                const store = Alpine.store('root');
                if (store) setTimeout(() => { store.isOpen = false; }, 10);
            },

            async handleCancel() {
                if (this.resolvePromise) {
                    this.resolvePromise({ status: 'cancelled', data: null });
                    this.resolvePromise = null;
                }
                this.isOpen = false;
                const store = Alpine.store('root');
                if (store) setTimeout(() => { store.isOpen = false; }, 10);
            }
        }));
    });
//             console.log(result);  // This will log the result when the modal is closed
//         });
//     }

//     return proxy
// }


// document.addEventListener('alpine:init', () => {
//     Alpine.store('settingsModal', initSettingsModal());
// });

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
                    const response = await fetchApi(`${API.BASE}${API.SETTINGS}`);
                    if (response.ok) {
                        const data = await response.json();
                        const sections = data?.sections || data?.settings?.sections || data?.data?.sections;
                        if (sections) {
                            this.settingsData = { sections };
                        } else {
                            console.error(t('settings.invalidFormat', 'Invalid settings data format'));
                        }
                    } else {
                        console.error(t('settings.fetchFailed', 'Failed to fetch settings:'), response.statusText);
                    }
                } catch (error) {
                    console.error(t('settings.fetchError', 'Error getting settings'), error);
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
                            if (field.required && (!field.value || field.value.trim() === '')) {
                                showToast(t('settings.fieldRequired', '{field} in {section} is required').replace('{field}', field.title).replace('{section}', section.title), 'error');
                                return;
                            }
                        }
                    }

                    // Prepare data
                    const formData = {};
                    for (const section of this.settingsData.sections) {
                        for (const field of section.fields) {
                            formData[field.id] = field.value;
                        }
                    }

                    // Send request
                    const response = await fetchApi('/api/settings_save', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    });

                    if (response.ok) {
                        showToast(t('settings.savedSuccess', 'Settings saved successfully'), 'success');
                        // Refresh settings
                        await this.fetchSettings();
                    } else {
                        const errorData = await response.json();
                        throw new Error(errorData.error || t('settings.saveFailed', 'Failed to save settings'));
                    }
                } catch (error) {
                    console.error(t('settings.saveErrorLog', 'Error saving settings:'), error);
                    showToast(t('settings.saveFailedWithReason', 'Failed to save settings: {reason}').replace('{reason}', error.message), 'error');
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

            // Test API connection
            async testConnection(field) {
                try {
                    field.testResult = t('settings.testing', 'Testing...');
                    field.testStatus = 'loading';

                    // Find the API key field
                    let apiKey = '';
                    for (const section of this.settingsData.sections) {
                        for (const f of section.fields) {
                            if (f.id === field.target) {
                                apiKey = f.value;
                                break;
                            }
                        }
                    }

                    if (!apiKey) {
                        throw new Error(t('settings.apiKeyRequired', 'API key is required'));
                    }

                    // Send test request
                    const response = await fetchApi('/api/test_connection', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            service: field.service,
                            api_key: apiKey
                        })
                    });

                    const data = await response.json();

                    if (response.ok && data.success) {
                        field.testResult = t('settings.connectionSuccess', 'Connection successful!');
                        field.testStatus = 'success';
                    } else {
                        throw new Error(data.error || t('settings.connectionFailed', 'Connection failed'));
                    }
                } catch (error) {
                    console.error('Connection test failed:', error);
                    field.testResult = t('settings.connectionFailedReason', 'Failed: {reason}').replace('{reason}', error.message);
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
                            field.value = f.type === 'password' ? t('actions.show', 'Show') : t('actions.hide', 'Hide');

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

// Show toast notification - now uses new notification system
function showToast(message, type = 'info') {
    // Use new frontend notification system based on type
    if (window.Alpine && window.Alpine.store && window.Alpine.store('notificationStore')) {
        const store = window.Alpine.store('notificationStore');
        const title = t('settings.title', 'Settings');
        switch (type.toLowerCase()) {
            case 'error':
                return store.frontendError(message, title, 5);
            case 'success':
                return store.frontendInfo(message, title, 3);
            case 'warning':
                return store.frontendWarning(message, title, 4);
            case 'info':
            default:
                return store.frontendInfo(message, title, 3);
        }
    } else {
        // Fallback if Alpine/store not ready
        console.log(`SETTINGS ${type.toUpperCase()}: ${message}`);
        return null;
    }
}
