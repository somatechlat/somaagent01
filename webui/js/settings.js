// Expose settings modal controller in a way Alpine inline handlers can access reliably.
// Note: top-level const/let do not create window properties in browsers; ensure we also assign to globalThis.
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
        const _delay = (ms)=> new Promise(res=>setTimeout(res, ms));
        console.log('Settings modal opening');
        const modalEl = document.getElementById('settingsModal');
        const modalAD = Alpine.$data(modalEl);

        // First, ensure the store is updated properly
        const store = Alpine.store('root');
        if (store) {
            // Set isOpen first to ensure proper state
            store.isOpen = true;
        }

        // Open the modal shell immediately; we’ll populate sections below
        try { if (modalAD) modalAD.isOpen = true; } catch(_) {}
        this.isOpen = true;
        try { await _delay(0); } catch(_) {}

        //get settings from backend
        try {
            // Gateway UI-shaped settings only (no legacy fallback)
            let set;
            const resp = await fetchApi('/v1/ui/settings/sections', { method: 'GET' });
            if (resp.ok) {
                set = await resp.json();
            } else {
                throw new Error(`HTTP ${resp.status}`);
            }

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
                "sections": set.settings.sections,
                // to be filled with presence map (has_secret)
                "credentials": { "has_secret": {} }
            }

            // Fetch provider credentials presence for UI badges (non-fatal)
            try {
                const c = await fetchApi('/v1/ui/settings/credentials', { method: 'GET' });
                if (c && c.ok) {
                    const body = await c.json().catch(()=>({}));
                    if (body && body.has_secret && typeof body.has_secret === 'object') {
                        settings.credentials = { has_secret: body.has_secret };
                    }
                }
            } catch (_) { /* ignore */ }

            // Update modal data and wait a frame to ensure teleported DOM renders
            modalAD.isOpen = true;
            modalAD.settings = settings;
            this.settings = settings;
            this.updateSpeechFieldVisibility();
            try { await _delay(0); } catch(_) {}

            // Wait until the teleported modal container is visible before resolving
            const deadline = Date.now() + 3000;
            while (Date.now() < deadline) {
                try {
                    const modal = document.querySelector('.modal-container');
                    const visible = modal && modal.offsetParent !== null;
                    if (visible) break;
                } catch(_) {}
                await _delay(50);
            }
            // Apply initial readonly state for Uploads & AV based on current values
            try{
                const getField=(id)=>{
                    for(const s of (this.settings.sections||[])){
                        for(const f of (s.fields||[])) if(f.id===id) return f;
                    }
                    return null;
                };
                const ue=(getField('uploads_enabled')||{}).value !== false;
                this._updateUploadsReadonly(ue);
                const ae=(getField('av_enabled')||{}).value === true;
                this._updateAvReadonly(ae);
            }catch(_){}

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
            try {
                // Validate Uploads + AV fields prior to save
                const errs = [];
                const getField = (id)=>{
                    for(const s of (modalAD.settings.sections||[])){
                        for(const f of (s.fields||[])) if(f.id===id) return f;
                    }
                    return null;
                };
                const numInRange = (val,min,max)=>{ const n=Number(val); return Number.isFinite(n)&&n>=min&&n<=max; };
                const uploadsEnabled = (getField('uploads_enabled')||{}).value !== false;
                if(uploadsEnabled){
                    if(!numInRange((getField('uploads_max_mb')||{}).value,1,512)) errs.push('Max File Size (MB) must be 1-512');
                    if(!numInRange((getField('uploads_max_files')||{}).value,1,25)) errs.push('Max Files must be 1-25');
                    if(!numInRange((getField('uploads_ttl_days')||{}).value,1,180)) errs.push('TTL (days) must be 1-180');
                    if(!numInRange((getField('uploads_janitor_interval_seconds')||{}).value,60,86400)) errs.push('Janitor interval must be 60-86400');
                }
                const avEnabled = (getField('av_enabled')||{}).value === true;
                const avStrict = (getField('av_strict')||{}).value === true;
                if(avStrict && !avEnabled) errs.push('Strict Mode requires Antivirus enabled');
                if(avEnabled && !numInRange((getField('av_port')||{}).value,1,65535)) errs.push('ClamAV Port must be 1-65535');
                if(errs.length){ showToast(errs.join('\n'),'error'); return; }

                // Prefer Gateway; fall back to legacy if needed
                const gwResp = await fetchApi('/v1/ui/settings/sections', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sections: modalAD.settings.sections })
                });
                if (gwResp.ok) {
                    const body = await gwResp.json();
                    document.dispatchEvent(new CustomEvent('settings-updated', { detail: body.settings }));
                    this.resolvePromise({ status: 'saved', data: body.settings });
                    this.stopSchedulerPolling();
                    this.isOpen = false;
                    const store = Alpine.store('root'); if (store) setTimeout(()=>{ store.isOpen=false; },10);
                    return;
                } else {
                    throw new Error(`HTTP ${gwResp.status}`);
                }
            } catch (e) {
                window.toastFetchError("Error saving settings", e)
                return
            }
            // Successful path returned earlier; this is not reached.
        } else if (buttonId === 'cancel') {
            this.handleCancel();
        }

        // Stop scheduler polling if it's running
        this.stopSchedulerPolling();

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
        this.resolvePromise({
            status: 'cancelled',
            data: null
        });

        // Stop scheduler polling if it's running
        this.stopSchedulerPolling();

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
                const resp = await fetchApi('/v1/av/test', { method: 'GET' });
                const body = await resp.json().catch(() => ({}));
                if (resp.ok && body.status === 'ok') {
                    showToast(`ClamAV reachable at ${body.host}:${body.port}`, 'success');
                } else {
                    const detail = body.detail || 'Unknown error';
                    showToast(`ClamAV not reachable: ${detail}`, 'warning');
                }
            } catch (e) {
                showToast('AV test failed: ' + (e?.message || String(e)), 'error');
            }
        }
    },

    handleFieldChange(field, value) {
        field.value = value;
        this.onFieldValueChange(field);
    },

    onFieldValueChange(field) {
        if (!field || !field.id) return;

        if (field.id === "speech_provider") {
            this.updateSpeechFieldVisibility();
        }
        if (field.id === 'uploads_enabled') {
            this._updateUploadsReadonly(field.value !== false);
        }
        if (field.id === 'av_enabled') {
            this._updateAvReadonly(field.value === true);
        }
    },

    updateSpeechFieldVisibility() {
        if (!this.settings || !this.settings.sections) return;

        const section = this.getSpeechSection();
        if (!section) return;

        const providerField = section.fields.find((f) => f.id === "speech_provider");
    const provider = providerField?.value || "openai_realtime";

        section.fields.forEach((field) => {
            if (field.id === "tts_kokoro") {
                field.hidden = provider !== "kokoro";
            } else if (field.id && field.id.startsWith("speech_realtime_")) {
                field.hidden = provider !== "openai_realtime";
            }
        });
    },

    getSpeechSection() {
        if (!this.settings || !Array.isArray(this.settings.sections)) return null;
        return this.settings.sections.find((section) => section.id === "speech") || null;
    },

    _getSection(id){
        if(!this.settings || !Array.isArray(this.settings.sections)) return null;
        return this.settings.sections.find(s => s.id===id) || null;
    },
    _setReadonly(sectionId, ids, ro){
        const sec = this._getSection(sectionId);
        if(!sec || !Array.isArray(sec.fields)) return;
        for(const f of sec.fields){
            if(ids.includes(f.id)) {
                f.readonly = !!ro;
                f._ui_disabled = !!ro;
            }
        }
    },
    _updateUploadsReadonly(enabled){
        // Always keep uploads_dir read-only; others depend on enabled
        const ro = !enabled;
        const ids = ['uploads_max_mb','uploads_max_files','uploads_allowed_mime','uploads_denied_mime','uploads_ttl_days','uploads_janitor_interval_seconds'];
        this._setReadonly('uploads', ids, ro);
        // Add UI class for disabled fields
        const sec = this._getSection('uploads');
        if(sec && Array.isArray(sec.fields)){
            for(const f of sec.fields){
                if(ids.includes(f.id)){
                    f._ui_disabled = ro;
                }
            }
        }
        this.updateFilteredSections();
    },
    _updateAvReadonly(enabled){
        const ro = !enabled;
        const ids = ['av_strict','av_host','av_port'];
        this._setReadonly('antivirus', ids, ro);
        // Add UI class for disabled fields
        const sec = this._getSection('antivirus');
        if(sec && Array.isArray(sec.fields)){
            for(const f of sec.fields){
                if(ids.includes(f.id)){
                    f._ui_disabled = ro;
                }
            }
        }
        this.updateFilteredSections();
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
                    const response = await fetchApi('/v1/ui/settings/sections', { method: 'GET' });
                    if (!response.ok) throw new Error(response.statusText || 'settings fetch failed');
                    const data = await response.json();
                    if (data && data.settings) {
                        this.settingsData = data.settings;
                    } else {
                        console.error('Invalid settings data format');
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
                    const base = this.settingsData.sections?.filter(section => section.tab === 'external') || [];
                    // Synthesize a Flare Tunnel section at the end to avoid hard-coded duplicates in HTML
                    // This keeps navigation and content generation uniform.
                    const tunnelSection = {
                        id: 'tunnel',
                        title: 'Flare Tunnel',
                        description: 'Create a secure public URL to access your Agent Zero instance anytime, anywhere.',
                        fields: []
                    };
                    // Avoid duplication if the backend ever ships a tunnel section in the future
                    const hasTunnel = base.some(s => (s.id || '').toLowerCase() === 'tunnel');
                    this.filteredSections = hasTunnel ? base : [...base, tunnelSection];
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

                    // Prepare data
                    const formData = {};
                    for (const section of this.settingsData.sections) {
                        for (const field of section.fields) {
                            formData[field.id] = field.value;
                        }
                    }

                    // Send request to Gateway UI-shaped settings endpoint
                    let response = await fetchApi('/v1/ui/settings/sections', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sections: this.settingsData.sections || [] })
                    });

                    if (response.ok) {
                        showToast('Settings saved successfully', 'success');
                        // Gateway UI-shaped endpoint already applies model profile and credentials

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

            _extractLlmConfigFromSections(sections){
                try{
                    const sec = sections.find(s => s.id === 'chat_model' || s.title === 'Chat Model');
                    if(!sec || !Array.isArray(sec.fields)) return null;
                    let model='', base_url='', temperature=0.2, kwargs={};
                    for(const f of sec.fields){
                        if(f.id==='chat_model_name') model = (f.value||'').trim();
                        if(f.id==='chat_model_api_base') base_url = (f.value||'').trim();
                        if(f.id==='chat_model_kwargs'){
                            if(typeof f.value==='string'){
                                const lines = f.value.split(/\n+/).map(s=>s.trim()).filter(Boolean);
                                for(const ln of lines){
                                    const idx = ln.indexOf('=');
                                    if(idx>0){
                                        const k=ln.slice(0,idx).trim();
                                        const v=ln.slice(idx+1).trim();
                                        kwargs[k]=v;
                                        if(k.toLowerCase()==='temperature'){
                                            const t=parseFloat(v); if(!Number.isNaN(t)) temperature=t;
                                        }
                                    }
                                }
                            } else if(f.value && typeof f.value==='object'){
                                kwargs={...f.value};
                                if(kwargs.temperature!==undefined){
                                    const t=parseFloat(kwargs.temperature); if(!Number.isNaN(t)) temperature=t;
                                }
                            }
                        }
                    }
                    return {model, base_url, temperature, kwargs};
                }catch(e){
                    console.error('extractLlmConfig error:', e);
                    return null;
                }
            },

            _extractProviderCredentials(sections){
                const creds=[];
                for(const sec of sections){
                    if(!sec || !Array.isArray(sec.fields)) continue;
                    for(const f of sec.fields){
                        if(typeof f.id==='string' && f.id.startsWith('api_key_')){
                            const provider = f.id.substring('api_key_'.length).trim().toLowerCase();
                            const val = (f.value||'').trim();
                            if(!val || val==='************') continue; // skip placeholder
                            creds.push({provider, secret: val});
                        }
                    }
                }
                return creds;
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

// Make the proxy available to Alpine inline expressions (e.g., @click="settingsModalProxy.openModal()")
// Some browsers won't resolve global lexical bindings from Alpine's evaluator; attach to global object explicitly.
try {
    if (!globalThis.settingsModalProxy) {
        globalThis.settingsModalProxy = settingsModalProxy;
    }
    // If Alpine already started before this script loaded, ensure the settings modal node is initialized now
    if (globalThis.Alpine) {
        const modalEl = document.getElementById('settingsModal');
        if (modalEl) {
            const hasData = (()=>{ try { return !!Alpine.$data(modalEl); } catch(_) { return false; } })();
            if (!hasData && typeof Alpine.initTree === 'function') {
                Alpine.initTree(modalEl);
            }
        }
    } else {
        // If Alpine isn't ready yet, register a hook to init when it is
        document.addEventListener('alpine:init', () => {
            const modalEl = document.getElementById('settingsModal');
            if (modalEl && typeof Alpine.initTree === 'function') {
                Alpine.initTree(modalEl);
            }
        });
    }
} catch (_) { /* no-op */ }
