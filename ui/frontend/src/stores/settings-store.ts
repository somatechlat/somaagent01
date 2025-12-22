/**
 * Eye of God Settings Store
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit Context implementation
 * - API persistence
 * - Optimistic updates with rollback
 */

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { provide } from '@lit/context';

export type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system';

export interface SettingsData {
    agent: AgentSettings;
    external: ExternalSettings;
    connectivity: ConnectivitySettings;
    system: SystemSettings;
}

export interface AgentSettings {
    chat_provider: string;
    chat_model: string;
    recall_interval: number;
    max_memories: number;
    temperature: number;
    max_tokens: number;
}

export interface ExternalSettings {
    openai_key?: string;
    anthropic_key?: string;
    groq_key?: string;
    serper_key?: string;
}

export interface ConnectivitySettings {
    api_base_url: string;
    ws_url: string;
    timeout_ms: number;
    retry_attempts: number;
}

export interface SystemSettings {
    log_level: string;
    debug_mode: boolean;
    telemetry_enabled: boolean;
}

export interface SettingsStateData {
    data: SettingsData;
    versions: Record<SettingsTab, number>;
    isLoading: boolean;
    isSaving: boolean;
    error: string | null;
    lastSaved: Date | null;
}

export const settingsContext = createContext<SettingsStateData>('settings-context');

const DEFAULT_SETTINGS: SettingsData = {
    agent: {
        chat_provider: 'openai',
        chat_model: 'gpt-4',
        recall_interval: 30,
        max_memories: 100,
        temperature: 0.7,
        max_tokens: 4096,
    },
    external: {},
    connectivity: {
        api_base_url: '/api/v2',
        ws_url: '/ws/v2/events',
        timeout_ms: 30000,
        retry_attempts: 3,
    },
    system: {
        log_level: 'INFO',
        debug_mode: false,
        telemetry_enabled: true,
    },
};

@customElement('eog-settings-provider')
export class EogSettingsProvider extends LitElement {
    @provide({ context: settingsContext })
    @state()
    settingsState: SettingsStateData = {
        data: { ...DEFAULT_SETTINGS },
        versions: { agent: 1, external: 1, connectivity: 1, system: 1 },
        isLoading: true,
        isSaving: false,
        error: null,
        lastSaved: null,
    };

    private _pendingChanges: Partial<SettingsData> = {};

    connectedCallback() {
        super.connectedCallback();
        this._loadAllSettings();
    }

    render() {
        return html`<slot></slot>`;
    }

    /**
     * Load all settings tabs from API
     */
    async _loadAllSettings() {
        this.settingsState = { ...this.settingsState, isLoading: true, error: null };

        try {
            const token = localStorage.getItem('eog_auth_token');
            const response = await fetch('/api/v2/settings/', {
                headers: { 'Authorization': `Bearer ${token}` },
            });

            if (!response.ok) {
                throw new Error('Failed to load settings');
            }

            const settings = await response.json();
            const data = { ...DEFAULT_SETTINGS };
            const versions: Record<string, number> = {};

            for (const setting of settings) {
                data[setting.tab as SettingsTab] = { ...data[setting.tab as SettingsTab], ...setting.data };
                versions[setting.tab] = setting.version;
            }

            this.settingsState = {
                ...this.settingsState,
                data: data as SettingsData,
                versions: versions as Record<SettingsTab, number>,
                isLoading: false,
            };
        } catch (error) {
            console.error('Settings load failed:', error);
            this.settingsState = {
                ...this.settingsState,
                isLoading: false,
                error: error instanceof Error ? error.message : 'Load failed',
            };
        }
    }

    /**
     * Update a single setting value (optimistic)
     */
    updateSetting<T extends SettingsTab>(tab: T, key: keyof SettingsData[T], value: unknown) {
        const previousData = { ...this.settingsState.data };

        // Optimistic update
        this.settingsState = {
            ...this.settingsState,
            data: {
                ...this.settingsState.data,
                [tab]: {
                    ...this.settingsState.data[tab],
                    [key]: value,
                },
            },
        };

        // Track pending changes
        if (!this._pendingChanges[tab]) {
            this._pendingChanges[tab] = {} as SettingsData[T];
        }
        (this._pendingChanges[tab] as Record<string, unknown>)[key as string] = value;

        // Debounce save
        this._debouncedSave(tab, previousData);
    }

    private _saveTimeout?: ReturnType<typeof setTimeout>;

    private _debouncedSave(tab: SettingsTab, previousData: SettingsData) {
        if (this._saveTimeout) {
            clearTimeout(this._saveTimeout);
        }

        this._saveTimeout = setTimeout(async () => {
            await this._saveSettings(tab, previousData);
        }, 1000);
    }

    /**
     * Save settings to API with rollback on failure
     */
    private async _saveSettings(tab: SettingsTab, previousData: SettingsData) {
        this.settingsState = { ...this.settingsState, isSaving: true, error: null };

        try {
            const token = localStorage.getItem('eog_auth_token');
            const response = await fetch(`/api/v2/settings/${tab}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    data: this.settingsState.data[tab],
                    version: this.settingsState.versions[tab],
                }),
            });

            if (!response.ok) {
                if (response.status === 409) {
                    throw new Error('Settings were modified elsewhere. Please refresh.');
                }
                throw new Error('Failed to save settings');
            }

            const result = await response.json();

            this.settingsState = {
                ...this.settingsState,
                versions: {
                    ...this.settingsState.versions,
                    [tab]: result.version,
                },
                isSaving: false,
                lastSaved: new Date(),
            };

            // Clear pending changes for this tab
            delete this._pendingChanges[tab];

        } catch (error) {
            console.error('Settings save failed:', error);

            // Rollback optimistic update
            this.settingsState = {
                ...this.settingsState,
                data: previousData,
                isSaving: false,
                error: error instanceof Error ? error.message : 'Save failed',
            };
        }
    }

    /**
     * Reset tab to defaults
     */
    async resetTab(tab: SettingsTab) {
        this.settingsState = {
            ...this.settingsState,
            data: {
                ...this.settingsState.data,
                [tab]: DEFAULT_SETTINGS[tab],
            },
        };

        try {
            const token = localStorage.getItem('eog_auth_token');
            const response = await fetch(`/api/v2/settings/${tab}/reset`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });

            if (response.ok) {
                const result = await response.json();
                this.settingsState = {
                    ...this.settingsState,
                    versions: {
                        ...this.settingsState.versions,
                        [tab]: result.version,
                    },
                };
            }
        } catch (error) {
            console.error('Reset failed:', error);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-settings-provider': EogSettingsProvider;
    }
}
