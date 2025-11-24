// Simple toast helper that logs errors to the console.
// The original implementation called `window.toastFetchError`, which was later
// assigned to this same function, causing infinite recursion and a stack overflow.
// We replace it with a straightforward console error logger.
const safeToast = (text, error) => {
    console.error(text, error);
};

// Preserve backward compatibility: expose `toastFetchError` if not already defined.
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
            // Use cached settings if available to avoid duplicate GETs
            if (window._settingsCache) {
                const cached = window._settingsCache;
                const payload = cached?.sections || cached?.settings?.sections || [];
                const configTitle = cached?.title || "Settings";
                const settings = {
                    "title": configTitle,
                    "buttons": [
                        { "id": "save", "title": "Save", "classes": "btn btn-ok" },
                        { "id": "cancel", "title": "Cancel", "type": "secondary", "classes": "btn btn-cancel" }
                    ],
                    "sections": payload
                };
                if (modalAD) {
                    modalAD.isOpen = true;
                    modalAD.settings = settings;
                }
                // Continue to set active tab after opening modal
                setTimeout(() => {
                    const savedTab = localStorage.getItem('settingsActiveTab') || 'agent';
                    if (modalAD) modalAD.activeTab = savedTab;
                    if (store) store.activeTab = savedTab;
                    localStorage.setItem('settingsActiveTab', savedTab);
                }, 5);
                // Return a resolved promise for consistency
                return new Promise(resolve => { this.resolvePromise = resolve; });
            }
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

// The original implementation duplicated the Settings modal logic using Alpine.data('settingsModal')
// while the UI actually relies on the global `settingsModalProxy` object (x-data="settingsModalProxy").
// This caused conflicting state, duplicate fetching, and race conditions that broke the modal UI.
// The redundant Alpine component has been removed. The modal now uses only `settingsModalProxy`
// which handles opening, tab switching, fetching, and saving settings.
// The root store initialization remains unchanged and is sufficient for tab persistence.
document.addEventListener('alpine:init', function () {
    // Initialize the root store first to ensure it exists before components try to access it
    Alpine.store('root', {
        activeTab: localStorage.getItem('settingsActiveTab') || 'agent',
        isOpen: false,

        toggleSettings() {
            this.isOpen = !this.isOpen;
        }
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
