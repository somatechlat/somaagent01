/**
 * IQ Store — AgentIQ knob state.
 *
 * The lookup tables live on the server (`admin/core/agentiq/tables.py` and
 * `derivation.py`). This store NEVER re-implements them. Derived settings are
 * whatever the server last reported; until an endpoint returns them they are
 * absent, not guessed.
 *
 * Knob field names follow the model keys (`intelligence_level`,
 * `autonomy_level`, `resource_budget`, `response_style`) — see
 * SOMA-01-UIUX-001 H-07.
 */

import { createContext } from '@lit/context';

export interface IQKnobs {
    intelligence_level: number;   // 1-10
    autonomy_level: number;       // 1-10
    resource_budget: number;      // $/turn
    response_style: string;       // precise | balanced | creative
}

/**
 * Server-side DerivedSettings (admin/core/agentiq/settings.py).
 * Every field is computed by the server from the knobs. The UI must not
 * invent values for any of them.
 */
export interface DerivedSettings {
    response_style: string;
    temperature: number;
    max_tokens: number;
    recall_limit: number;
    model_tier: 'budget' | 'standard' | 'premium' | 'flagship';
    brain_query_enabled: boolean;
    require_hitl: boolean;
    tool_approval: 'none' | 'dangerous' | 'all';
    egress_allowed: 'none' | 'whitelist' | 'expanded' | 'unrestricted';
    token_limit: number;
}

export const iqContext = createContext<IQStore>('iq-store');

export class IQStore {
    /** Knobs as last seen from the server. Null = not loaded. */
    private _knobs: IQKnobs | null = null;
    /** Derived settings as last computed by the server. Null = not loaded. */
    private _derived: DerivedSettings | null = null;
    private _saved: IQKnobs | null = null;
    private _listeners: Set<() => void> = new Set();

    get knobs(): Readonly<IQKnobs> | null {
        return this._knobs ? { ...this._knobs } : null;
    }

    get derived(): Readonly<DerivedSettings> | null {
        return this._derived ? { ...this._derived } : null;
    }

    get saved(): Readonly<IQKnobs> | null {
        return this._saved ? { ...this._saved } : null;
    }

    get dirty(): boolean {
        if (!this._knobs || !this._saved) return false;
        return (
            this._knobs.intelligence_level !== this._saved.intelligence_level ||
            this._knobs.autonomy_level !== this._saved.autonomy_level ||
            this._knobs.resource_budget !== this._saved.resource_budget ||
            this._knobs.response_style !== this._saved.response_style
        );
    }

    subscribe(listener: () => void): () => void {
        this._listeners.add(listener);
        return () => this._listeners.delete(listener);
    }

    private _notify() {
        this._listeners.forEach(l => l());
    }

    /** Load knobs + derived settings the server computed. Missing fields stay missing. */
    setFromServer(knobs: Partial<IQKnobs> | null, derived: Partial<DerivedSettings> | null) {
        if (knobs) {
            this._knobs = {
                intelligence_level: knobs.intelligence_level ?? this._knobs?.intelligence_level ?? 5,
                autonomy_level: knobs.autonomy_level ?? this._knobs?.autonomy_level ?? 5,
                resource_budget: knobs.resource_budget ?? this._knobs?.resource_budget ?? 0.10,
                response_style: knobs.response_style ?? this._knobs?.response_style ?? 'balanced',
            };
            if (!this._saved) this._saved = { ...this._knobs };
        }
        if (derived) {
            this._derived = { ...(this._derived ?? {}), ...derived } as DerivedSettings;
        }
        this._notify();
    }

    markSaved() {
        if (this._knobs) this._saved = { ...this._knobs };
        this._notify();
    }

    setKnob<K extends keyof IQKnobs>(key: K, value: IQKnobs[K]) {
        if (!this._knobs) {
            this._knobs = {
                intelligence_level: 5,
                autonomy_level: 5,
                resource_budget: 0.10,
                response_style: 'balanced',
            };
            if (!this._saved) this._saved = { ...this._knobs };
        }
        this._knobs = { ...this._knobs, [key]: value };
        this._notify();
    }

    resetToSaved() {
        if (this._saved) {
            this._knobs = { ...this._saved };
            this._notify();
        }
    }
}

export const iqStore = new IQStore();
