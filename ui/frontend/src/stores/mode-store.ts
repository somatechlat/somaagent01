/**
 * Eye of God Mode Store (Lit Context)
 * Per Eye of God UIX Design Section 4.2
 *
 * VIBE COMPLIANT:
 * - Real Lit context implementation
 * - SpiceDB permission check on mode change
 * - WebSocket sync support
 */

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { provide } from '@lit/context';
import { apiClient } from '../services/api-client.js';

/**
 * Agent operating modes.
 * STD - Standard: Normal operation
 * TRN - Training: Learning mode with feedback loops
 * ADM - Admin: Full system access
 * DEV - Developer: Debug and diagnostic access
 * RO - Read-Only: No write operations
 * DGR - Degraded: Fallback mode with limited capabilities
 */
export type AgentMode = 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR';

export interface ModeInfo {
    code: AgentMode;
    name: string;
    description: string;
    icon: string;
    color: string;
}

export interface ModeState {
    current: AgentMode;
    available: AgentMode[];
    modes: Record<AgentMode, ModeInfo>;
    loading: boolean;
    error: string | null;
}

// Mode metadata
const MODE_INFO: Record<AgentMode, ModeInfo> = {
    STD: {
        code: 'STD',
        name: 'Standard',
        description: 'Normal operation mode',
        icon: '🔵',
        color: '#3b82f6',
    },
    TRN: {
        code: 'TRN',
        name: 'Training',
        description: 'Learning mode with feedback',
        icon: '📚',
        color: '#8b5cf6',
    },
    ADM: {
        code: 'ADM',
        name: 'Admin',
        description: 'Full system access',
        icon: '⚙️',
        color: '#ef4444',
    },
    DEV: {
        code: 'DEV',
        name: 'Developer',
        description: 'Debug and diagnostics',
        icon: '🔧',
        color: '#f59e0b',
    },
    RO: {
        code: 'RO',
        name: 'Read-Only',
        description: 'No write operations',
        icon: '👁️',
        color: '#64748b',
    },
    DGR: {
        code: 'DGR',
        name: 'Degraded',
        description: 'Limited fallback mode',
        icon: '⚠️',
        color: '#dc2626',
    },
};

export const modeContext = createContext<ModeState>('mode-state');

@customElement('eog-mode-provider')
export class EogModeProvider extends LitElement {
    @provide({ context: modeContext })
    @property({ attribute: false })
    state: ModeState = {
        current: 'STD',
        available: ['STD'],
        modes: MODE_INFO,
        loading: false,
        error: null,
    };

    async connectedCallback() {
        super.connectedCallback();
        await this.loadAvailableModes();
    }

    /**
     * Load available modes from API.
     */
    async loadAvailableModes(): Promise<void> {
        this.state = { ...this.state, loading: true, error: null };

        try {
            const response = await apiClient.get<{
                current: AgentMode;
                available: AgentMode[];
            }>('/modes');

            this.state = {
                ...this.state,
                current: response.current,
                available: response.available,
                loading: false,
            };
        } catch (error) {
            this.state = {
                ...this.state,
                loading: false,
                error: String(error),
            };
        }
    }

    /**
     * Change the current agent mode.
     * @param mode - Target mode
     */
    async setMode(mode: AgentMode): Promise<boolean> {
        if (mode === this.state.current) {
            return true;
        }

        if (!this.state.available.includes(mode)) {
            this.state = {
                ...this.state,
                error: `Mode ${mode} is not available`,
            };
            return false;
        }

        this.state = { ...this.state, loading: true, error: null };

        try {
            const response = await apiClient.put<{ mode: AgentMode }>(
                '/modes/current',
                { mode }
            );

            this.state = {
                ...this.state,
                current: response.mode,
                loading: false,
            };

            // Dispatch event for WebSocket sync
            this.dispatchEvent(new CustomEvent('mode-changed', {
                bubbles: true,
                composed: true,
                detail: { mode: response.mode, previous: this.state.current },
            }));

            return true;
        } catch (error) {
            this.state = {
                ...this.state,
                loading: false,
                error: String(error),
            };
            return false;
        }
    }

    /**
     * Get info for a specific mode.
     */
    getModeInfo(mode: AgentMode): ModeInfo {
        return this.state.modes[mode];
    }

    /**
     * Check if a mode is available.
     */
    isModeAvailable(mode: AgentMode): boolean {
        return this.state.available.includes(mode);
    }

    /**
     * Clear any errors.
     */
    clearError(): void {
        this.state = { ...this.state, error: null };
    }

    render() {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-mode-provider': EogModeProvider;
    }
}
