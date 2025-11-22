const safeToast = (text, error) => {
  if (typeof window !== 'undefined' && typeof window.toastFetchError === 'function') {
    window.toastFetchError(text, error);
  } else {
    console.error(text, error);
  }
};

if (typeof window !== 'undefined' && typeof window.toastFetchError !== 'function') {
  window.toastFetchError = safeToast;
}

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
                // Debug: Switching to scheduler tab, initializing Flatpickr
                const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                if (schedulerElement) {
                    const schedulerData = Alpine.$data(schedulerElement);
                    if (schedulerData) {
                        // Polling removed

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
        // Debug: Settings modal opening
        const modalEl = document.getElementById('settingsModal');
        const modalAD = modalEl ? Alpine.$data(modalEl) : null;

        // First, ensure the store is updated properly
        const store = Alpine.store('root');
        if (store) {
            // Set isOpen first to ensure proper state
            store.isOpen = true;
        }

        //get settings from backend
        try {
            const resp = await fetchApi('/v1/ui/settings/sections');
            if (!resp.ok) {
                throw new Error(await resp.text());
            }
            const payload = await resp.json();
            const sectionsPayload = payload?.sections || payload?.settings?.sections || [];
            const configTitle = payload?.title || "Settings";

            // First load the settings data without setting the active tab
            const settings = {
                "title": configTitle,
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
                "sections": sectionsPayload
            }

            // Update modal data
            if (modalAD) {
                modalAD.isOpen = true;
                modalAD.settings = settings;
            }

            // Now set the active tab after the modal is open
            // This ensures Alpine reactivity works as expected
            setTimeout(() => {
                // Get stored tab or default to 'agent'
                const savedTab = localStorage.getItem('settingsActiveTab') || 'agent';
                // Debug: Setting initial tab to:, savedTab

                // Directly set the active tab
                if (modalAD) {
                    modalAD.activeTab = savedTab;
                }

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
                    const schedulerTab = document.querySelector('.settings-tab[title="Task Scheduler"]');
                    const schedulerTabActive = !!(schedulerTab && schedulerTab.classList.contains('active'));

                    // Polling removed; just fetch if scheduler is active
                    if (modalAD.activeTab === 'scheduler' && schedulerTabActive) {
                        const schedulerElement = document.querySelector('[x-data="schedulerSettings"]');
                        const schedulerData = schedulerElement && Alpine.$data(schedulerElement);
                        if (schedulerData && typeof schedulerData.fetchTasks === 'function') {
                            schedulerData.fetchTasks();
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
            safeToast("Error getting settings", e);
        }
    },

    async handleButton(buttonId) {
        if (buttonId === 'save') {
            const modalEl = document.getElementById('settingsModal');
            const modalAD = modalEl ? Alpine.$data(modalEl) : null;
            const sections = modalAD?.settings?.sections || [];
            try {
                const response = await fetchApi('/v1/ui/settings/sections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sections }),
                });
                if (!response.ok) {
                    throw new Error(await response.text());
                }
                const data = await response.json();
                const updatedSections = data?.sections || data?.settings?.sections || [];
                if (modalAD && Array.isArray(updatedSections) && updatedSections.length > 0) {
                    modalAD.settings.sections = updatedSections;
                }
                document.dispatchEvent(new CustomEvent('settings-updated', { detail: data }));
                if (typeof window.toastFrontendSuccess === 'function') {
                    window.toastFrontendSuccess('Settings saved', 'Settings', 3);
                }
                this.resolvePromise?.({
                    status: 'saved',
                    data,
                });
                this.resolvePromise = null;
            } catch (e) {
                window.toastFetchError?.('Error saving settings', e);
                return;
            }
        } else if (buttonId === 'cancel') {
            this.handleCancel();
            return;
        }

        // Polling removed

        // First update our component state
        this.isOpen = false;

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
        this.resolvePromise?.({
            status: 'cancelled',
            data: null
        });
        this.resolvePromise = null;

        // Polling removed

        // First update our component state
        this.isOpen = false;

        // Then safely update the store
        const store = Alpine.store('root');
        if (store) {
            // Use a slight delay to avoid reactivity issues
            setTimeout(() => {
                store.isOpen = false;
            }, 10);
        }
    },

    // Prior polling helper removed

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
        }
    }
};

globalThis.settingsModalProxy = settingsModalProxy;


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
                    const response = await fetchApi('/v1/ui/settings/sections');
                    if (response.ok) {
                        const data = await response.json();
                        if (data && data.sections) {
                            this.settingsData = { sections: data.sections };
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
                            if (field.required && (!field.value || field.value.trim() === '')) {
                                showToast(`${field.title} in ${section.title} is required`, 'error');
                                return;
                            }
                        }
                    }

                    // Prepare payload matching the backend schema (sections array)
                    const payload = { sections: this.settingsData.sections };

                    // Send request to the correct endpoint. The backend will split
                    // secret vs non‑secret fields and persist them.
                    const response = await fetchApi('/v1/ui/settings/sections', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });

                    if (response.ok) {
                        showToast('Settings saved successfully', 'success');
                        // Refresh settings
                        await this.fetchSettings();
                    } else {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Failed to save settings');
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

            // Test API connection
            async testConnection(field) {
                try {
                    field.testResult = 'Testing...';
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
                        throw new Error('API key is required');
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
                        field.testResult = 'Connection successful!';
                        field.testStatus = 'success';
                    } else {
                        throw new Error(data.error || 'Connection failed');
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

// Show toast notification - now uses new notification system
/**
 * Unified toast helper for Settings UI.
 * The original implementation attempted to use an Alpine store named
 * `notificationStore`, but the application actually registers the store as
 * `notificationSse` (see `webui/index.js`). As a result the lookup always
 * failed and the function fell back to a console.log, producing no visible
 * toast messages. This also meant the UI appeared as if the save operation
 * never succeeded.
 *
 * The new implementation first tries the modern `notificationSse` store. If
 * that is unavailable (e.g., during early page load), it falls back to the
 * global helper functions (`toastFrontendInfo`, `toastFrontendSuccess`,
 * `toastFrontendError`, `toastFrontendWarning`) that are always defined by
 * `webui/index.js`. This guarantees a visible toast regardless of the store
 * initialization timing.
 */
function showToast(message, type = 'info') {
    try {
        // Preferred: use the SSE notification Alpine store if present
        if (window.Alpine && window.Alpine.store && window.Alpine.store('notificationSse')) {
            const store = window.Alpine.store('notificationSse');
            // The store expects a payload; we map the toast type accordingly.
            const payload = {
                type: type.toLowerCase(),
                title: 'Settings',
                body: message,
                severity: type.toLowerCase(),
                ttl_seconds: type === 'error' ? 5 : 3,
            };
            // Directly push to the store's toast stack if method exists
            if (typeof store.create === 'function') {
                store.create(payload);
                return;
            }
        }
    } catch (e) {
        // Silently ignore and fall back
    }

    // Fallback to the global toast helpers defined in index.js
    if (typeof globalThis.toastFrontendInfo === 'function' &&
        typeof globalThis.toastFrontendSuccess === 'function' &&
        typeof globalThis.toastFrontendError === 'function' &&
        typeof globalThis.toastFrontendWarning === 'function') {
        switch (type.toLowerCase()) {
            case 'error':
                return globalThis.toastFrontendError(message, 'Settings');
            case 'success':
                return globalThis.toastFrontendSuccess(message, 'Settings');
            case 'warning':
                return globalThis.toastFrontendWarning(message, 'Settings');
            case 'info':
            default:
                return globalThis.toastFrontendInfo(message, 'Settings');
        }
    }

    // Last resort: log to console so developers can see the message.
    console.log(`SETTINGS ${type.toUpperCase()}: ${message}`);
    return null;
}
